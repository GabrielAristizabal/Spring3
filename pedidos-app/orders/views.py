# orders/views.py
from __future__ import annotations
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .services import (
    db,
    generar_llaves_rsa_pem,
    utcnow,
    get_user_by_document,
    crear_pedido_firmado,
)

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
# Lista de pedidos
# -----------------------------
def order_list(request):
    """Muestra todos los pedidos registrados"""
    pedidos = list(db.orders.find().sort("created_at", -1))
    return render(request, "orders/order_list.html", {"orders": pedidos})


# -----------------------------
# Registro de usuario + firmante en sesión
# -----------------------------
@require_http_methods(["GET", "POST"])
def register_user(request):
    """Registra el usuario y genera sus llaves"""
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        doc = (request.POST.get("document") or "").strip()
        if not name or not doc:
            messages.error(request, "Nombre y documento son obligatorios.")
            return redirect("register_user")

        existing = db.users.find_one({"document": doc})
        if not existing:
            priv_pem, pub_pem = generar_llaves_rsa_pem()
            db.users.insert_one({
                "name": name,
                "document": doc,
                "pub_key": pub_pem,
                "priv_key": priv_pem,
                "created_at": utcnow(),
            })

        request.session["signer_doc"] = doc
        messages.success(request, f"Usuario {name} registrado correctamente.")
        return redirect("create_order")

    return render(request, "orders/register.html")


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

    if request.method == "GET":
        if not signer:
            messages.error(request, "Debe registrar o seleccionar un usuario firmante.")
        return render(
            request,
            "orders/order_form.html",
            {
                "signer": signer,
                "signer_keys": signer_keys,
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
