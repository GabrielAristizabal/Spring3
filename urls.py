from django.contrib import admin
from django.urls import path
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from pymongo import MongoClient

# Conexión lazy a MongoDB (solo se conecta cuando se necesita)
_client = None
_db = None

def get_mongo_client():
    """Obtiene el cliente de MongoDB, inicializándolo si es necesario."""
    global _client, _db
    if _client is None:
        # Intentar obtener desde variables de entorno, sino usar el valor por defecto
        # Usar la IP pública del servidor MongoDB: 34.201.94.84
        # Opciones de authSource comunes: admin, wms_dev, o el nombre de la BD
        mongo_uri = os.getenv(
            "MONGODB_URI", 
            "mongodb://wms_app:WmsApp!2025@34.201.94.84:27017/wms_dev?authSource=wms_dev"
        )
        mongo_db = os.getenv("MONGODB_DB", "wms_dev")
        
        try:
            # Conectar con timeout más largo
            _client = MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=10000,  # 10 segundos para selección de servidor
                connectTimeoutMS=15000,          # 15 segundos para conectar
                socketTimeoutMS=30000,          # 30 segundos para operaciones
                retryWrites=True,
                retryReads=True
            )
            # Verificar conexión
            _client.server_info()
            _db = _client[mongo_db]
        except Exception as e:
            _client = None
            _db = None
            raise Exception(f"Error conectando a MongoDB: {str(e)}")
    
    return _client, _db

def home(request):
    return HttpResponse("Home OK")

@csrf_exempt
def test_mongo(request):
    """Endpoint de prueba para verificar conexión a MongoDB"""
    try:
        client, db = get_mongo_client()
        # Intentar una operación simple
        result = db.inventory.count_documents({})
        return JsonResponse({
            "ok": True,
            "message": "Conexión a MongoDB exitosa",
            "items_en_inventario": result
        })
    except Exception as e:
        error_msg = str(e)
        sugerencias = [
            "Verifica que MongoDB esté corriendo",
            "Verifica que la IP y puerto sean correctos",
            "Verifica que el firewall permita conexiones al puerto 27017"
        ]
        
        # Agregar sugerencias específicas para errores de autenticación
        if "Authentication failed" in error_msg or "Authentication" in error_msg:
            sugerencias.extend([
                "Verifica que el usuario 'wms_app' exista en MongoDB",
                "Verifica que la contraseña sea correcta",
                "Prueba con authSource=admin en la URI: mongodb://user:pass@host:port/db?authSource=admin",
                "O prueba con authSource=wms_dev: mongodb://user:pass@host:port/db?authSource=wms_dev",
                "Verifica que el usuario tenga permisos sobre la base de datos wms_dev"
            ])
        
        return JsonResponse({
            "ok": False,
            "error": f"Error conectando a MongoDB: {error_msg}",
            "sugerencias": sugerencias,
            "uri_actual": os.getenv("MONGODB_URI", "mongodb://wms_app:***@34.201.94.84:27017/wms_dev?authSource=wms_dev")
        }, status=503)

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

    # Obtener conexión a MongoDB
    try:
        client, db = get_mongo_client()
        inventory = db.inventory
        orders_collection = db.orders
    except Exception as e:
        return JsonResponse({"error": f"Error de conexión a la base de datos: {str(e)}"}, status=503)

    session = client.start_session()
    session.start_transaction()

    try:
        total = 0
        precios = {}

        for nombre, qty in items.items():
            # Convertir qty a entero (puede venir como string desde JSON)
            try:
                qty = int(qty)
                if qty <= 0:
                    raise Exception(f"La cantidad para {nombre} debe ser mayor a 0")
            except (ValueError, TypeError):
                raise Exception(f"La cantidad para {nombre} debe ser un número válido")
            
            # Buscar producto en inventario
            prod = inventory.find_one({"item": nombre}, session=session)
            if not prod:
                raise Exception(f"Item no encontrado: {nombre}")

            # Obtener stock actual (asegurarse de que sea entero)
            stock_actual = int(prod.get("stock", 0))
            
            # Validación de stock ANTES de intentar actualizar
            if stock_actual < qty:
                raise Exception(f"Stock insuficiente para {nombre}. Disponible: {stock_actual}, solicitado: {qty}")

            # Registrar precio y calcular total
            precio_unitario = float(prod.get("price", 0))
            precios[nombre] = precio_unitario
            total += precio_unitario * qty

            # Actualizar stock de forma atómica (solo si hay disponibilidad suficiente)
            # Esta es una segunda validación dentro de la actualización
            resultado = inventory.update_one(
                {"item": nombre, "stock": {"$gte": qty}},
                {"$inc": {"stock": -qty}},
                session=session
            )

            # Si no se actualizó, significa que el stock no era suficiente
            if resultado.modified_count == 0:
                # Verificar nuevamente el stock por si cambió entre la validación y la actualización
                stock_actualizado = inventory.find_one({"item": nombre}, session=session)
                stock_disponible = int(stock_actualizado.get("stock", 0)) if stock_actualizado else 0
                raise Exception(f"Stock insuficiente para {nombre}. Disponible: {stock_disponible}, solicitado: {qty}")

        # Insertar el pedido solo si todo salió bien
        orders_collection.insert_one(
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

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("order/create/", create_order, name="order_create"),
    path("test/mongo/", test_mongo, name="test_mongo"),  # Endpoint de prueba
]