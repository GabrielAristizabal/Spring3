# orders/views.py
from __future__ import annotations
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings
import requests
from .services import (
    db,
    generar_llaves_rsa_pem,
    utcnow,
    get_user_by_document,
    crear_pedido_firmado,
)
from .auth0_client import (
    verify_token,
    set_token_in_session,
    clear_auth0_session,
    get_auth0_user_from_session,
    get_token_from_session,
)
from .auth0_decorators import auth0_required, auth0_optional

# -----------------------------
# Página principal
# -----------------------------
def home(request):
    """Página de inicio"""
    return render(request, "orders/home.html")


def health(request):
    """Endpoint simple para monitorización."""
    return JsonResponse({"status": "ok", "timestamp": utcnow().isoformat() + "Z"})


# -----------------------------
# Autenticación Auth0
# -----------------------------
@require_http_methods(["GET", "POST"])
def auth0_login(request):
    """
    Vista de login con Auth0.
    Si viene con token en POST, lo valida y guarda en sesión.
    Si es GET, muestra formulario para ingresar token.
    """
    if request.method == "POST":
        token = (request.POST.get("token") or "").strip()
        if not token:
            messages.error(request, "Debes proporcionar un token de Auth0.")
            return render(request, "orders/auth0_login.html")
        
        try:
            # Validar el token
            payload = verify_token(token)
            
            # Guardar en sesión
            set_token_in_session(request, token, payload)
            
            # Obtener información del usuario de Auth0
            auth0_user = get_auth0_user_from_session(request)
            messages.success(request, f"Autenticado exitosamente como {auth0_user.get('email', 'usuario')}")
            
            # Redirigir al registro o crear pedido
            return redirect("register_user")
        except Exception as e:
            messages.error(request, f"Error validando token: {str(e)}")
            return render(request, "orders/auth0_login.html")
    
    # GET: mostrar formulario de login
    return render(request, "orders/auth0_login.html")


@require_http_methods(["GET"])
def auth0_callback(request):
    """
    Callback de Auth0 (puede recibir token como parámetro o en header).
    """
    # Intentar obtener token de query parameter
    token = request.GET.get("token") or request.GET.get("access_token")
    
    # Si no está en query, intentar del header Authorization
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split()[1]
    
    if not token:
        messages.error(request, "No se proporcionó token de Auth0.")
        return redirect("auth0_login")
    
    try:
        # Validar el token
        payload = verify_token(token)
        
        # Guardar en sesión
        set_token_in_session(request, token, payload)
        
        # Obtener información del usuario
        auth0_user = get_auth0_user_from_session(request)
        messages.success(request, f"Autenticado exitosamente como {auth0_user.get('email', 'usuario')}")
        
        # Redirigir al registro
        return redirect("register_user")
    except Exception as e:
        messages.error(request, f"Error validando token: {str(e)}")
        return redirect("auth0_login")


@require_http_methods(["GET"])
def auth0_logout(request):
    """Cierra la sesión de Auth0."""
    clear_auth0_session(request)
    messages.success(request, "Sesión cerrada exitosamente.")
    return redirect("auth0_login")


# -----------------------------
# Lista de pedidos
# -----------------------------
@auth0_optional
def order_list(request):
    """Muestra todos los pedidos registrados"""
    pedidos = list(db.orders.find().sort("created_at", -1))
    
    # Enriquecer pedidos con información del creador
    pedidos_enriquecidos = []
    for pedido in pedidos:
        pedido_dict = dict(pedido)
        # Obtener información del usuario que creó el pedido
        created_by_doc = pedido.get("created_by")
        creador_info = None
        if created_by_doc:
            creador = get_user_by_document(created_by_doc)
            if creador:
                creador_info = {
                    "name": creador.get("name", "N/A"),
                    "document": creador.get("document", "N/A"),
                }
        
        pedido_dict["creador"] = creador_info
        pedidos_enriquecidos.append(pedido_dict)
    
    return render(request, "orders/order_list.html", {"orders": pedidos_enriquecidos})


# -----------------------------
# Registro de usuario + firmante en sesión
# -----------------------------
@require_http_methods(["GET", "POST"])
@auth0_required
def register_user(request):
    """
    Registra el usuario y genera sus llaves.
    Requiere autenticación con Auth0 primero.
    """
    # Obtener información del usuario de Auth0
    auth0_user = get_auth0_user_from_session(request)
    token = get_token_from_session(request)
    
    if not auth0_user or not token:
        messages.error(request, "Debes iniciar sesión con Auth0 primero.")
        return redirect("auth0_login")
    
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        doc = (request.POST.get("document") or "").strip()
        
        # Si no se proporciona nombre, usar el de Auth0
        if not name:
            name = auth0_user.get("name") or auth0_user.get("nickname") or auth0_user.get("email", "").split("@")[0]
        
        if not doc:
            messages.error(request, "El documento es obligatorio.")
            return redirect("register_user")

        # Verificar que el token sigue siendo válido
        try:
            payload = verify_token(token)
        except Exception as e:
            messages.error(request, f"Token inválido o expirado: {str(e)}")
            clear_auth0_session(request)
            return redirect("auth0_login")

        # Buscar o crear usuario en la base de datos
        existing = db.users.find_one({"document": doc})
        if not existing:
            # Generar llaves RSA para el usuario
            priv_pem, pub_pem = generar_llaves_rsa_pem()
            db.users.insert_one({
                "name": name,
                "document": doc,
                "pub_key": pub_pem,
                "priv_key": priv_pem,
                "auth0_sub": auth0_user.get("sub"),  # Guardar sub de Auth0
                "auth0_email": auth0_user.get("email"),
                "created_at": utcnow(),
            })
            messages.success(request, f"Usuario {name} registrado correctamente con llaves RSA.")
        else:
            # Actualizar información de Auth0 si ya existe
            db.users.update_one(
                {"document": doc},
                {"$set": {
                    "auth0_sub": auth0_user.get("sub"),
                    "auth0_email": auth0_user.get("email"),
                }}
            )
            messages.info(request, f"Usuario {name} ya existe. Llaves RSA ya generadas.")

        # Establecer como firmante activo
        request.session["signer_doc"] = doc
        return redirect("create_order")

    # GET: mostrar formulario de registro
    # Pre-llenar con datos de Auth0 si están disponibles
    context = {
        "auth0_user": auth0_user,
        "default_name": auth0_user.get("name") or auth0_user.get("nickname") or "",
        "default_email": auth0_user.get("email") or "",
    }
    return render(request, "orders/register.html", context)


# -----------------------------
# Cambiar firmante manualmente
# -----------------------------
@require_http_methods(["GET"])
def set_signer(request):
    """
    Cambia el firmante activo colocando el documento en la sesión:
    /firmante/usar/?doc=XXXXXXXX
    """
    doc = (request.GET.get("doc") or "").strip()
    if not doc:
        messages.error(request, "Debes enviar el parámetro ?doc=DOCUMENTO")
        return redirect("create_order")

    user = db.users.find_one({"document": doc})
    if user:
        request.session["signer_doc"] = doc
        messages.success(request, f"Firmante activo cambiado a {doc} ({user.get('name','')}).")
    else:
        messages.error(request, f"No existe un usuario con documento {doc}.")
    return redirect("create_order")


# -----------------------------
# Crear pedido
# -----------------------------
@require_http_methods(["GET", "POST"])
@auth0_required
def create_order(request):
    """Crea un pedido firmado por el usuario en sesión"""
    signer_doc = request.session.get("signer_doc")
    signer = get_user_by_document(signer_doc) if signer_doc else None
    signer_keys = None

    if signer:
        def _pem_to_text(value):
            if not value:
                return ""
            if isinstance(value, str):
                return value
            try:
                return bytes(value).decode("utf-8")
            except Exception:
                try:
                    return value.decode("utf-8")
                except Exception:
                    return str(value)

        signer_keys = {
            "public": _pem_to_text(signer.get("pub_key")),
            "private": _pem_to_text(signer.get("priv_key")),
        }

    # Obtener información de Auth0 para mostrar en la vista
    auth0_user = get_auth0_user_from_session(request)
    
    if request.method == "GET":
        if not signer:
            messages.error(request, "Debe registrar o seleccionar un usuario firmante.")
        return render(
            request,
            "orders/order_form.html",
            {
                "signer": signer,
                "signer_keys": signer_keys,
                "auth0_user": auth0_user,
            },
        )

    cliente = (request.POST.get("cliente") or "").strip()
    documento = (request.POST.get("documento") or "").strip()
    fecha = (request.POST.get("fecha") or "").strip()
    items_json = (request.POST.get("items") or "").strip()

    if not all([cliente, documento, fecha, items_json]):
        messages.error(request, "Todos los campos del pedido son obligatorios.")
        return redirect("create_order")

    try:
        pedido_id = crear_pedido_firmado(
            cliente=cliente,
            documento=documento,
            fecha=fecha,
            items_json=items_json,
            signer=signer,
        )
        messages.success(request, f"Pedido creado exitosamente: {pedido_id}")
        return redirect("order_list")
    except Exception as e:
        messages.error(request, f"Error al crear el pedido: {e}")
        return redirect("create_order")
