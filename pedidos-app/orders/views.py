# orders/views.py
from __future__ import annotations

from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods

# Importa tus utilidades/servicios ya existentes
# (ajusta los nombres si en tu proyecto difieren)
from .services import (
    db,
    generar_llaves_rsa_pem,
    utcnow,
    get_user_by_document,
    crear_pedido_firmado,
)


# -----------------------------
# Registro de usuario + firmante en sesión
# -----------------------------
@require_http_methods(["GET", "POST"])
def register_user(request):
    """
    Registra el usuario (si no existe), genera sus llaves y deja el firmante activo en sesión.
    """
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        doc  = (request.POST.get("document") or "").strip()

        if not name or not doc:
            messages.error(request, "Nombre y documento son obligatorios.")
            return redirect("register_user")

        # Verifica si ya existe
        existing = db.users.find_one({"document": doc})
        if not existing:
            # Generar llaves públicas/privadas (ajusta si guardas solo la pública)
            priv_pem, pub_pem = generar_llaves_rsa_pem()
            db.users.insert_one({
                "name": name,
                "document": doc,
                "pub_key": pub_pem,
                "priv_key": priv_pem,   # Si no deseas guardarla, elimínala
                "created_at": utcnow(),
            })

        # Dejar firmante activo en sesión
        request.session["signer_doc"] = doc
        messages.success(request, f"Usuario {name} registrado. Firmante activo: {doc}")
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
# Crear pedido (usando firmante en sesión o en el form)
# -----------------------------
@require_http_methods(["GET", "POST"])
def create_order(request):
    """
    - GET: muestra formulario; si no hay firmante en sesión, muestra aviso.
    - POST: crea el pedido firmando con el firmante activo. Si viene "firmante"
      en el form, actualiza la sesión con ese doc.
    """
    # 1) intenta desde sesión
    signer_doc = request.session.get("signer_doc")

    # 2) si viene en el form (campo opcional), úsalo y actualiza sesión
    firmante_form = (request.POST.get("firmante") or request.GET.get("firmante") or "").strip()
    if firmante_form:
        signer_doc = firmante_form
        request.session["signer_doc"] = signer_doc

    signer = get_user_by_document(signer_doc) if signer_doc else None

    if request.method == "GET":
        if not signer:
            messages.error(request, "No existe el usuario firmante.")
        return render(request, "orders/create.html", {"signer": signer})

    # POST: aquí sí necesitamos firmante
    if not signer:
        messages.error(request, "No existe el usuario firmante. Selecciónalo o regístralo.")
        return redirect("create_order")

    # Campos del pedido
    cliente    = (request.POST.get("cliente") or "").strip()
    documento  = (request.POST.get("documento") or "").strip()
    fecha      = (request.POST.get("fecha") or "").strip()
    items_json = (request.POST.get("items") or "").strip()

    if not cliente or not documento or not fecha or not items_json:
        messages.error(request, "Todos los campos del pedido son obligatorios.")
        return redirect("create_order")

    try:
        # Crea el pedido firmando y encadenando hash (no repudio)
        pedido_id = crear_pedido_firmado(
            cliente=cliente,
            documento=documento,
            fecha=fecha,
            items_json=items_json,
            signer=signer,  # dict con pub_key/priv_key/document/name
        )
        messages.success(request, f"Pedido creado: {pedido_id}")
        # Si tienes lista de pedidos, redirígelo allá (por simplicidad, lo dejamos aquí)
        return redirect("create_order")
    except Exception as e:
        messages.error(request, f"Error creando pedido: {e}")
        return redirect("create_order")
