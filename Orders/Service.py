from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pymongo import MongoClient, ReturnDocument
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern
from pymongo.read_preferences import ReadPreference
from django.conf import settings

client = MongoClient(settings.MONGODB_URI)
db = client[settings.MONGODB_DB]

class OutOfStock(Exception):
    def __init__(self, item, requested, available):
        super().__init__(f"Sin disponibilidad para {item}: requerido {requested}, disponible {available}")

class ItemNotFound(Exception):
    def __init__(self, item):
        super().__init__(f"Item no encontrado en bodega: {item}")

def _money(x) -> float:
    """Redondeo a 2 decimales para dinero."""
    return float(Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

def create_order_with_strict_stock(items_list, cliente, documento, fecha_str):
    """
    items_list = [{"nombre": "...", "qty": 2}, ...]
    Coteja contra bodega y descuenta stock SOLO si todos alcanzan.
    Inserta el documento del pedido con:
      cliente, documento, fecha (YYYY-MM-DD), items {nombre: qty},
      precios {nombre: precio_unitario}, total.
    """
    with client.start_session() as s:

        def txn(sess):
            precios = {}
            total = Decimal("0.00")

            for it in items_list:
                nombre, qty = it["nombre"], int(it["qty"])

                # 1) Verifica existencia del item y obtiene su precio
                current = db.inventory.find_one({"item": nombre}, session=sess)
                if not current:
                    raise ItemNotFound(nombre)

                # 2) Descontar stock si alcanza (operación atómica)
                updated = db.inventory.find_one_and_update(
                    {"item": nombre, "stock": {"$gte": qty}},
                    {"$inc": {"stock": -qty}},
                    session=sess,
                    return_document=ReturnDocument.AFTER
                )
                if not updated:
                    available = current.get("stock", 0)
                    raise OutOfStock(nombre, qty, available)

                # 3) Acumular precio y total
                unit_price = Decimal(str(current.get("price", 0.0)))
                precios[nombre] = _money(unit_price)
                total += unit_price * qty

            # Construir estructura EXACTA solicitada
            order_doc = {
                "cliente":   cliente,
                "documento": documento,
                "fecha":     fecha_str,  # YYYY-MM-DD
                "items":     {it["nombre"]: it["qty"] for it in items_list},
                "precios":   precios,
                "total":     _money(total),
                # Campos opcionales útiles:
                "createdAt": datetime.utcnow(),
                "status":    "CREATED"
            }

            db.orders.insert_one(order_doc, session=sess)
            # Retorna lo que nos interesa mostrar (sin _id si no quieres)
            return {k: order_doc[k] for k in ["cliente","documento","fecha","items","precios","total","status"]}

        wc = WriteConcern("majority")
        rc = ReadConcern("local")
        try:
            return s.with_transaction(
                txn,
                read_concern=rc,
                write_concern=wc,
                read_preference=ReadPreference.PRIMARY
            ), None
        except (OutOfStock, ItemNotFound) as e:
            return None, str(e)

