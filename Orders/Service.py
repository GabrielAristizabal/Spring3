from datetime import datetime
from pymongo import MongoClient, ReturnDocument
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern
from pymongo.read_preferences import ReadPreference
from django.conf import settings

client = MongoClient(settings.MONGODB_URI)
db = client[settings.MONGODB_DB]

class OutOfStock(Exception):
    def __init__(self, sku, requested, available):
        super().__init__(f"Sin disponibilidad para {sku}: requerido {requested}, disponible {available}")

def create_order_with_strict_stock(items):
    """
    Compara pedido vs bodega y descuenta stock solo si TODO alcanza.
    Si un ítem no alcanza, aborta la transacción y devuelve error.
    """
    with client.start_session() as s:

        def txn(sess):
            for it in items:
                sku, qty = it["sku"], int(it["qty"])
                updated = db.inventory.find_one_and_update(
                    {"sku": sku, "stock": {"$gte": qty}},   # comparación con bodega
                    {"$inc": {"stock": -qty}},              # descuento solo si alcanza
                    session=sess,
                    return_document=ReturnDocument.AFTER
                )
                if not updated:
                    current = db.inventory.find_one({"sku": sku}, session=sess) or {"stock": 0}
                    raise OutOfStock(sku, qty, current.get("stock", 0))

            order = {"items": items, "status": "CREATED", "createdAt": datetime.utcnow()}
            db.orders.insert_one(order, session=sess)
            return order

        try:
            wc = WriteConcern("majority")
            rc = ReadConcern("local")
            return s.with_transaction(
                txn, read_concern=rc, write_concern=wc, read_preference=ReadPreference.PRIMARY
            ), None
        except OutOfStock as e:
            return None, str(e)
