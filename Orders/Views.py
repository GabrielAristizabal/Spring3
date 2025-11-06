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

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    cliente = data.get("cliente")
    documento = data.get("documento")
    fecha = data.get("fecha")
    items = data.get("items", {})

    # Validación básica
    if not cliente or not items:
        return JsonResponse({"error": "cliente e items son obligatorios"}, status=400)

    session = client.start_session()
    session.start_transaction()

    try:
        total = 0
        precios = {}

        for nombre, qty in items.items():
            # Buscar producto en inventario
            prod = inventory.find_one({"item": nombre}, session=session)
            if not prod:
                raise Exception(f"Item no encontrado: {nombre}")

            stock_actual = int(prod.get("stock", 0))
            if stock_actual < qty:
                raise Exception(f"Stock insuficiente para {nombre}. Disponible: {stock_actual}, solicitado: {qty}")

            # Registrar precio y calcular total
            precios[nombre] = prod["price"]
            total += prod["price"] * qty

            # Actualizar stock solo si hay disponibilidad suficiente
            resultado = inventory.update_one(
                {"item": nombre, "stock": {"$gte": qty}},
                {"$inc": {"stock": -qty}},
                session=session
            )

            if resultado.modified_count == 0:
                raise Exception(f"No se pudo actualizar el stock de {nombre}. Revisa la disponibilidad.")

        # Insertar el pedido solo si todo salió bien
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