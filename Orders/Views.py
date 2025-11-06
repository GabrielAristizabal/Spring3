from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from pymongo import MongoClient

# Conexión al Mongo de tu EC2
client = MongoClient("mongodb://wms_app:WmsApp!2025@13.222.177.119:27017/wms_dev")
db = client["wms_dev"]
inventory = db.inventory
orders = db.orders

@csrf_exempt
def create_order(request):
    if request.method == "GET":
        return HttpResponse("Endpoint /order/create/ listo (usa POST)")

    if request.method != "POST":
        return JsonResponse({"error": "Solo POST"}, status=405)

    data = json.loads(request.body)
    cliente = data.get("cliente")
    documento = data.get("documento")
    fecha = data.get("fecha")
    items = data.get("items", {})

    # Validación simple
    if not cliente or not items:
        return JsonResponse({"error": "cliente e items son obligatorios"}, status=400)

    session = client.start_session()
    session.start_transaction()

    try:
        total = 0
        precios = {}

        for nombre, qty in items.items():
            prod = inventory.find_one({"item": nombre}, session=session)
            if not prod:
                raise Exception(f"Item no encontrado: {nombre}")

            if prod["stock"] < qty:
                raise Exception(f"Stock insuficiente para {nombre}")

            precios[nombre] = prod["price"]
            total += prod["price"] * qty

            inventory.update_one(
                {"item": nombre},
                {"$inc": {"stock": -qty}},
                session=session
            )

        orders.insert_one(
            {
                "cliente": cliente,
                "documento": documento,
                "fecha": fecha,
                "items": items,
                "precios": precios,
                "total": total,
                "status": "CREATED"
            },
            session=session
        )

        session.commit_transaction()
        return JsonResponse({"ok": True, "total": total})

    except Exception as e:
        session.abort_transaction()
        return JsonResponse({"error": str(e)}, status=400)

    finally:
        session.end_session()