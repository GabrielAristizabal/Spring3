# orders/views.py
from __future__ import annotations

import json
import datetime as dt
from base64 import b64encode

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

from .crypto import make_operation_hash, sha256_hex  # ya lo tenías en tu proyecto
from .services import (
    users,
    audits,
    create_user_with_keys,   # reemplaza a generar_llaves_rsa_pem
    get_user,                # usamos el doc como "username"
    get_last_hash,
    insert_audit_entry,
    insert_order,
)

# ---------------------------------------------------------------------
# helpers de firma RSA en esta vista (para no tocar tu crypto.py actual)
# ---------------------------------------------------------------------
def _sign_detached_b64(private_pem: str, data: bytes) -> str:
    """
    Firma 'data' con RSA (PKCS#1 v1.5 + SHA256) y retorna firma base64.
    private_pem puede venir sin passphrase (DEMO). Si tienes passphrase,
    descomenta el 'password=' y pásala.
    """
    key = serialization.load_pem_private_key(
        private_pem.encode(),
        password=None,  # TODO: si guardas cifrada, coloca aquí la passphrase (bytes)
        backend=default_backend(),
    )
    signature = key.sign(
        data,
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return b64encode(signature).decode()


# ==========================
# Registro de usuario
# ==========================
@require_http_methods(["GET", "POST"])
def register_user(request):
    """
    Registra el usuario (si no existe), genera llaves y deja firmante en sesión.
    Usamos el documento como 'username' en la colección users.
    """
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        doc  = (request.POST.get("document") or "").strip()
        passphrase = (request.POST.get("passphrase") or "").strip() or None

        if not name or not doc:
            messages.error(request, "Nombre y documento son obligatorios.")
            return redirect("register_user")

        existing = users.find_one({"username": doc})
        if not existing:
            bundle = create_user_with_keys(username=doc, email=f"{doc}@demo.local", passphrase=passphrase)
            # Opcional: guarda también el nombre
            users.update_one({"username": doc}, {"$set": {"name": name}}, upsert=True)

            messages.success(
                request,
                f"Usuario {name} creado. Fingerprint: {bundle['fingerprint'][:10]}…"
            )
        else:
            messages.info(request, f"El usuario con documento {doc} ya existe.")

        # Deja firmante activo
        request.session["signer_doc"] = doc
        return redirect("create_order")

    return render(request, "orders/register.html")


# ==========================
# Cambiar firmante manualmente
# ==========================
@require_http_methods(["GET"])
def set_signer(request):
    """
    Cambia el firmante activo: /firmante/usar/?doc=XXXXXXXX
    """
    doc = (request.GET.get("doc") or "").strip()
    if not doc:
        messages.error(request, "Debes enviar el parámetro ?doc=DOCUMENTO")
        return redirect("create_order")

    user = get_user(doc)  # usamos doc como username
    if user:
        request.session["signer_doc"] = doc
        messages.success(request, f"Firmante activo cambiado a {doc} ({user.get('name','')}).")
    else:
        messages.error(request, f"No existe un usuario con documento {doc}.")
    return redirect("create_order")


# ==========================
# Crear pedido firmado (no repudio + hash encadenado)
# ==========================
@require_http_methods(["GET", "POST"])
def create_order(request):
    """
    - GET: muestra formulario y, si hay firmante en sesión, lo indica.
    - POST: crea pedido, calcula hash de operación, firma con privada del firmante,
      guarda pedido y entrada de auditoría con hash encadenado.
    """
    signer_doc = request.session.get("signer_doc")
    firmante_form = (request.POST.get("firmante") or request.GET.get("firmante") or "").strip()
    if firmante_form:
        signer_doc = firmante_form
        request.session["signer_doc"] = signer_doc

    signer = get_user(signer_doc) if signer_doc else None

    if request.method == "GET":
        if not signer:
            messages.error(request, "No existe el usuario firmante.")
        return render(request, "orders/create.html", {"signer": signer})

    # POST
    if not signer:
        messages.error(request, "No existe el usuario firmante. Selecciónalo o regístralo.")
        return redirect("create_order")

    cliente    = (request.POST.get("cliente") or "").strip()
    documento  = (request.POST.get("documento") or "").strip()
    fecha      = (request.POST.get("fecha") or "").strip()
    items_json = (request.POST.get("items") or "").strip()

    if not cliente or not documento or not fecha or not items_json:
        messages.error(request, "Todos los campos del pedido son obligatorios.")
        return redirect("create_order")

    # Parse items
    try:
        items = json.loads(items_json)
        if not isinstance(items, dict):
            raise ValueError("Items debe ser un objeto JSON {item: cantidad}.")
    except Exception as e:
        messages.error(request, f"JSON inválido en items: {e}")
        return redirect("create_order")

    # ----- Construir orden base
    ts = dt.datetime.utcnow().isoformat()
    order_payload = {
        "cliente": cliente,
        "documento": documento,
        "fecha": fecha,
        "items": items,
        "created_at": ts,
        "created_by": signer_doc,
    }

    try:
        # 1) Hash de operación con hash anterior (encadenamiento)
        prev_hash = get_last_hash() or ""
        op_hash = make_operation_hash(order_payload, prev_hash)

        # 2) Firma del hash con privada del firmante
        priv_pem = signer.get("private_key_pem_enc") or signer.get("private_key_pem")
        if not priv_pem:
            raise RuntimeError("El usuario no posee una clave privada almacenada (DEMO).")

        signature_b64 = _sign_detached_b64(priv_pem, op_hash.encode())

        # 3) Insertar pedido
        order_id = insert_order(order_payload)

        # 4) Insertar auditoría con cadena de hash
        audit_payload = {
            "action": "CREATE_ORDER",
            "order_id": order_id,
            "actor": signer_doc,
            "timestamp": ts,
            "op_hash": op_hash,
            "prev_hash": prev_hash,
            # opcional: un hash de cadena - ej. sha256(prev_hash + op_hash + signature)
            "hash": sha256_hex((prev_hash + op_hash + signature_b64).encode()),
        }
        # Envolvente para verificación
        envelope = {
            "payload": order_payload,
            "prev_hash": prev_hash,
        }
        insert_audit_entry(
            audit_payload=audit_payload,
            signature_b64=signature_b64,
            signer=signer_doc,
            pub_fingerprint=sha256_hex((signer.get("public_key_pem") or "").encode())[:16],
            envelope=envelope,
        )

        messages.success(request, f"Pedido creado: {order_id}")
        return redirect("create_order")

    except Exception as e:
        messages.error(request, f"Error creando pedido: {e}")
        return redirect("create_order")
