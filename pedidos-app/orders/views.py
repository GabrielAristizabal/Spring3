# orders/views.py
from __future__ import annotations
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

# Si tienes autenticación, puedes usar get_subject de tu helper; aquí lo dejamos simple
def _actor(request) -> str:
    # reemplaza por tu extractor real (Auth0): get_subject(request)
    return getattr(request.user, "username", "anonymous")

# --- VISTA HOME (requerida por tu urls.py) ---
def home(request):
    return HttpResponse("PedidosApp OK")

# --- Integración con servicios de dominio ---
from .services import (
    create_order_with_strict_stock,
    approve_order as approve_order_service,
)

@csrf_exempt
def create_order(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Only POST"}, status=405)
    try:
        data = json.loads(request.body or "{}")
        order_id  = data["order_id"]
        cliente   = data["cliente"]
        documento = data["documento"]
        fecha     = data["fecha"]
        items     = data["items"]          # {"Arroz":2,"Azúcar":1}
        req_id    = data.get("client_request_id")
    except Exception:
        return JsonResponse({"detail": "JSON inválido"}, status=400)

    actor = _actor(request)
    order, err = create_order_with_strict_stock(
        order_id=order_id, cliente=cliente, documento=documento, fecha=fecha,
        items=items, actor_sub=actor, client_request_id=req_id
    )
    if err:
        # 409 si es stock, 400 en otros casos
        code = 409 if "Sin disponibilidad" in err else 400
        return JsonResponse({"ok": False, "error": err}, status=code)

    return JsonResponse({"ok": True, "order": order}, status=201)

@csrf_exempt
def approve_order(request, order_id: str):
    if request.method != "POST":
        return JsonResponse({"detail": "Only POST"}, status=405)

    actor = _actor(request)
    order, err = approve_order_service(order_id=order_id, actor_sub=actor)
    if err:
        return JsonResponse({"ok": False, "error": err}, status=400)

    return JsonResponse({"ok": True, "order": order})
