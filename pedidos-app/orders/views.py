import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import Http404
from .forms import OrderForm, RegisterUserForm, VerifyForm
from .services import (
    ensure_indexes, create_user_with_keys, get_user, insert_order, list_orders,
    find_order, update_order, delete_order, get_last_hash, insert_audit_entry
)
from .crypto import make_operation_hash, sign_hash, verify_hash_signature, hybrid_encrypt, hybrid_decrypt

ensure_indexes()

def home(request):
    return render(request, "orders/home.html")

def order_list(request):
    return render(request, "orders/order_list.html", {"orders": list_orders(100)})

def order_detail(request, order_id):
    doc = find_order(order_id)
    if not doc: raise Http404("Pedido no existe")
    return render(request, "orders/order_detail.html", {"order": doc})

def order_create(request):
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            try:
                items = json.loads(form.cleaned_data["items"]); assert isinstance(items, dict)
            except Exception:
                messages.error(request, "Items debe ser JSON tipo {item:cantidad}")
                return render(request, "orders/order_form.html", {"form": form})

            order_doc = {
                "cliente": form.cleaned_data["cliente"],
                "documento": form.cleaned_data["documento"],
                "fecha": str(form.cleaned_data["fecha"]),
                "items": items,
            }

            signer = request.GET.get("user", "auditor")
            user = get_user(signer)
            if not user:
                messages.error(request, "No existe el usuario firmante.")
                return render(request, "orders/order_form.html", {"form": form})

            prev_hash = get_last_hash()
            audit_payload = make_operation_hash(order_doc, signer, prev_hash)  # -> incluye "hash"

            private_pem = user.get("private_key_pem_enc", "").encode()
            signature_b64 = sign_hash(audit_payload["hash"], private_pem, passphrase=None)

            public_pem = user["public_key_pem"].encode()
            envelope = hybrid_encrypt(audit_payload, public_pem)

            oid = insert_order({
                **order_doc,
                "audit": {
                    "hash": audit_payload["hash"],
                    "prev_hash": audit_payload["prev_hash"],
                    "timestamp": audit_payload["timestamp"],
                    "signer": signer,
                    "signature": signature_b64,
                    "pub_fingerprint": user["fingerprint"],
                    "envelope": envelope,
                }
            })
            insert_audit_entry(audit_payload, signature_b64, signer, user["fingerprint"], envelope)
            messages.success(request, f"Pedido creado, firmado y cifrado. ID: {oid}")
            return redirect("order_detail", order_id=oid)
    else:
        form = OrderForm()
    return render(request, "orders/order_form.html", {"form": form})

def order_update(request, order_id):
    doc = find_order(order_id)
    if not doc: raise Http404("Pedido no existe")
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            try:
                items = json.loads(form.cleaned_data["items"]); assert isinstance(items, dict)
            except Exception:
                messages.error(request, "Items debe ser JSON válido")
                return render(request, "orders/order_form.html", {"form": form, "update": True})
            ok = update_order(order_id, {
                "cliente": form.cleaned_data["cliente"],
                "documento": form.cleaned_data["documento"],
                "fecha": str(form.cleaned_data["fecha"]),
                "items": items,
            })
            if ok: messages.success(request, "Pedido actualizado.")
            return redirect("order_detail", order_id=order_id)
    else:
        form = OrderForm(initial={
            "cliente": doc.get("cliente",""),
            "documento": doc.get("documento",""),
            "fecha": doc.get("fecha",""),
            "items": json.dumps(doc.get("items",{}), ensure_ascii=False),
        })
    return render(request, "orders/order_form.html", {"form": form, "update": True})

def order_delete(request, order_id):
    if delete_order(order_id): messages.success(request, "Pedido eliminado.")
    return redirect("order_list")

def register_user(request):
    ctx = {"form": RegisterUserForm()}
    if request.method == "POST":
        form = RegisterUserForm(request.POST); ctx["form"] = form
        if form.is_valid():
            data = create_user_with_keys(form.cleaned_data["username"], form.cleaned_data["email"], form.cleaned_data["passphrase"] or None)
            messages.success(request, f"Usuario creado. Fingerprint: {data['fingerprint']}")
            ctx["pub_pem"] = data["public_pem"].decode()
            ctx["priv_pem"] = data["private_pem"].decode()
    return render(request, "orders/register.html", ctx)

def verify(request):
    ctx = {"form": VerifyForm()}
    if request.method == "POST":
        form = VerifyForm(request.POST); ctx["form"] = form
        if form.is_valid():
            doc = find_order(form.cleaned_data["order_id"])
            if not doc or "audit" not in doc:
                messages.error(request, "Pedido o auditoría inexistente")
                return render(request, "orders/verify.html", ctx)

            a = doc["audit"]
            user = get_user(a["signer"])
            if not user:
                messages.error(request, "No existe el usuario firmante")
                return render(request, "orders/verify.html", ctx)

            payload = {
                "order": {"cliente": doc.get("cliente"), "documento": doc.get("documento"), "fecha": doc.get("fecha"), "items": doc.get("items", {})},
                "user": a["signer"], "timestamp": a["timestamp"], "prev_hash": a.get("prev_hash",""), "hash": a["hash"],
            }
            ok_sig = verify_hash_signature(a["hash"], a["signature"], user["public_key_pem"].encode())
            try:
                decrypted = hybrid_decrypt(a["envelope"], user.get("private_key_pem_enc","").encode(), passphrase=None)
                ok_dec = (decrypted.get("hash") == a["hash"])
            except Exception:
                ok_dec = False

            ctx.update({"order": doc, "sig_ok": ok_sig, "dec_ok": ok_dec})
            if ok_sig and ok_dec:
                messages.success(request, "✅ Firma válida y sobre descifrado: hash coincide.")
            elif ok_sig:
                messages.warning(request, "✅ Firma válida, pero el sobre no se pudo descifrar (o no coincide).")
            else:
                messages.error(request, "❌ Firma inválida.")
    return render(request, "orders/verify.html", ctx)
