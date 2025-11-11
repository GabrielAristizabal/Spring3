# orders/views.py
import json, time
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
from pymongo import MongoClient, ReturnDocument
from .authz import get_subject, get_role
from .audit import AuditEvent, write_event

def _db():
    c = MongoClient(settings.MONGODB_URI)
    return c[settings.MONGODB_DB]

@login_required
@csrf_exempt
def approve_order(request, order_id: str):
    if request.method != "POST":
        return JsonResponse({"detail":"Only POST"}, status=405)

    # Autorización simple por rol (ajústalo a tus perfiles)
    role = get_role(request)
    if role not in {"Gerencia","Supervisor","Auditor"}:  # ejemplo
        return HttpResponseForbidden("No autorizado")

    db = _db()
    before = db.orders.find_one({"_id": order_id})
    if not before:
        return JsonResponse({"detail":"Pedido no existe"}, status=404)
    if before.get("status") == "APPROVED":
        return JsonResponse({"detail":"Ya aprobado"}, status=409)

    after = {**before, "status": "APPROVED"}
    db.orders.update_one({"_id": order_id}, {"$set":{"status":"APPROVED"}})

    actor = get_subject(request)  # sub de Auth0
    prev_hash = before.get("last_event_hash")
    ev = AuditEvent(order_id=order_id, action="APPROVE",
                    actor_sub=actor, ts=time.time(),
                    before={"status": before.get("status")},
                    after={"status": "APPROVED"},
                    prev_hash=prev_hash)
    head = write_event(db, ev)  # guarda evento y ancla hash

    return JsonResponse({"ok": True, "order_id": order_id, "audit_head": head})
