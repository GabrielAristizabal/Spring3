# orders/services.py
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple

from django.conf import settings
from pymongo import MongoClient, ReturnDocument, ASCENDING
from pymongo.client_session import ClientSession

from .audit import AuditEvent, write_event


# ---------- Conexión y utilidades ----------

_client = MongoClient(settings.MONGODB_URI)
_db = _client[settings.MONGODB_DB]

def db():
    """Acceso a la DB (para tests puedes 'mockear' este getter)."""
    return _db

def _money(x) -> float:
    return float(Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

def ensure_indexes() -> None:
    """
    Crea índices útiles (idempotente). Llama esto en AppConfig.ready()
    o una vez al inicio.
    """
    d = db()
    d.inventory.create_index([("item", ASCENDING)], unique=True)
    # Idempotencia por request: opcional/sparse para no forzar su presencia en todos
    d.orders.create_index([("client_request_id", ASCENDING)], unique=True, sparse=True)


# ---------- Excepciones de dominio ----------

class OutOfStock(Exception):
    def __init__(self, item: str, requested: int, available: int):
        super().__init__(f"Sin disponibilidad para {item}: requerido {requested}, disponible {available}")
        self.item = item
        self.requested = requested
        self.available = available

class ItemNotFound(Exception):
    def __init__(self, item: str):
        super().__init__(f"Item no encontrado en bodega: {item}")
        self.item = item


# ---------- Lecturas de apoyo ----------

def list_inventory_names() -> List[str]:
    """Para autocompletar: nombres de items en inventario."""
    return [d["item"] for d in db().inventory.find({}, {"_id": 0, "item": 1}).sort("item", 1)]

def get_order(order_id: str) -> Optional[dict]:
    return db().orders.find_one({"_id": order_id})


# ---------- Creación de pedido (transaccional, con auditoría) ----------

def create_order_with_strict_stock(
    *,
    order_id: str,
    cliente: str,
    documento: str,
    fecha: str,  # "YYYY-MM-DD"
    items: Dict[str, int],  # {"Arroz":2, "Azúcar":1}
    actor_sub: str,
    client_request_id: Optional[str] = None,  # idempotencia opcional
) -> Tuple[Optional[dict], Optional[str]]:
    """
    Crea un pedido si y solo si TODO el stock alcanza. Descuenta inventario,
    persiste el pedido y registra evento de auditoría encadenado.

    Retorna (pedido, None) en éxito; (None, "mensaje de error") si falla.
    """

    inv = db().inventory
    ords = db().orders

    with _client.start_session() as s:

        def txn(sess: ClientSession):
            # Idempotencia: si se envió client_request_id y ya existe, devuelve el existente
            if client_request_id:
                existing = ords.find_one({"client_request_id": client_request_id}, session=sess)
                if existing:
                    return existing

            precios: Dict[str, float] = {}
            total = Decimal("0.00")

            # Verificación + descuento de stock
            for nombre, qty in items.items():
                qty = int(qty)
                if qty <= 0:
                    raise ValueError(f"Cantidad inválida para {nombre}: {qty}")

                current = inv.find_one({"item": nombre}, session=sess)
                if not current:
                    raise ItemNotFound(nombre)

                updated = inv.find_one_and_update(
                    {"item": nombre, "stock": {"$gte": qty}},
                    {"$inc": {"stock": -qty}},
                    session=sess,
                    return_document=ReturnDocument.AFTER,
                )
                if not updated:
                    available = current.get("stock", 0)
                    raise OutOfStock(nombre, qty, available)

                unit_price = Decimal(str(current.get("price", 0.0)))
                precios[nombre] = _money(unit_price)
                total += unit_price * qty

            order_doc = {
                "_id":        order_id,  # string legible (p.ej. UUID generado por la capa superior)
                "cliente":    cliente,
                "documento":  documento,
                "fecha":      fecha,
                "items":      {k: int(v) for k, v in items.items()},
                "precios":    precios,
                "total":      _money(total),
                "status":     "CREATED",
                "createdAt":  datetime.utcnow(),
            }
            if client_request_id:
                order_doc["client_request_id"] = client_request_id

            ords.insert_one(order_doc, session=sess)

            # Auditoría: evento CREATE (prev_hash = None)
            ev = AuditEvent(
                order_id=order_id,
                action="CREATE",
                actor_sub=actor_sub,
                ts=datetime.utcnow().timestamp(),
                before=None,
                after={
                    "status": "CREATED",
                    "items": order_doc["items"],
                    "total": order_doc["total"],
                },
                prev_hash=None,
            )
            head = write_event(db(), ev)  # ancla last_event_hash en el pedido
            order_doc["last_event_hash"] = head
            return order_doc

        try:
            created = s.with_transaction(txn)
            return created, None
        except (OutOfStock, ItemNotFound, ValueError) as e:
            return None, str(e)


# ---------- Actualización de items (transaccional, con auditoría) ----------

def update_order_items(
    *,
    order_id: str,
    new_items: Dict[str, int],
    actor_sub: str,
) -> Tuple[Optional[dict], Optional[str]]:
    """
    Reemplaza el conjunto/cantidades de items de un pedido:
    - Calcula deltas contra el pedido actual
    - Aumenta/Reduce inventario según deltas (≥ 0) en transacción
    - Recalcula precios/total
    - Registra evento AUDIT "UPDATE"
    """

    inv = db().inventory
    ords = db().orders

    with _client.start_session() as s:

        def txn(sess: ClientSession):
            current = ords.find_one({"_id": order_id}, session=sess)
            if not current:
                raise ValueError("Pedido no existe")

            if current.get("status") == "APPROVED":
                raise ValueError("Pedido ya aprobado; no se puede modificar")

            old_items: Dict[str, int] = {k: int(v) for k, v in current.get("items", {}).items()}
            new_items_n = {k: int(v) for k, v in new_items.items() if int(v) > 0}

            # Calcula deltas
            # delta[item] = new - old
            all_names = set(old_items) | set(new_items_n)
            deltas = {name: new_items_n.get(name, 0) - old_items.get(name, 0) for name in all_names}

            # 1) Aumentar stock por reducciones (delta<0)
            for name, d in deltas.items():
                if d < 0:
                    inv.update_one({"item": name}, {"$inc": {"stock": abs(d)}}, session=sess)

            # 2) Verificar y reducir stock por incrementos (delta>0)
            for name, d in deltas.items():
                if d > 0:
                    doc = inv.find_one({"item": name}, session=sess)
                    if not doc:
                        raise ItemNotFound(name)
                    ok = inv.find_one_and_update(
                        {"item": name, "stock": {"$gte": d}},
                        {"$inc": {"stock": -d}},
                        session=sess,
                        return_document=ReturnDocument.AFTER,
                    )
                    if not ok:
                        available = doc.get("stock", 0)
                        raise OutOfStock(name, d, available)

            # Recalcular precios y total
            precios = {}
            total = Decimal("0.00")
            for name, qty in new_items_n.items():
                doc = inv.find_one({"item": name}, session=sess)
                if not doc:
                    raise ItemNotFound(name)
                unit_price = Decimal(str(doc.get("price", 0.0)))
                precios[name] = _money(unit_price)
                total += unit_price * qty

            after = {
                "items": new_items_n,
                "precios": precios,
                "total": _money(total),
                "status": current.get("status", "CREATED"),
            }

            # Update del pedido
            ords.update_one(
                {"_id": order_id},
                {"$set": {"items": new_items_n, "precios": precios, "total": _money(total)}},
                session=sess,
            )

            # Auditoría
            ev = AuditEvent(
                order_id=order_id,
                action="UPDATE",
                actor_sub=actor_sub,
                ts=datetime.utcnow().timestamp(),
                before={"items": old_items, "total": current.get("total")},
                after={"items": new_items_n, "total": _money(total)},
                prev_hash=current.get("last_event_hash"),
            )
            head = write_event(db(), ev)
            ords.update_one({"_id": order_id}, {"$set": {"last_event_hash": head}}, session=sess)

            updated = ords.find_one({"_id": order_id}, session=sess)
            return updated

        try:
            updated = s.with_transaction(txn)
            return updated, None
        except (OutOfStock, ItemNotFound, ValueError) as e:
            return None, str(e)


# ---------- Aprobación (status) con auditoría ----------

def approve_order(
    *,
    order_id: str,
    actor_sub: str,
) -> Tuple[Optional[dict], Optional[str]]:
    """
    Marca el pedido como APPROVED (sin tocar inventario) y registra evento de auditoría.
    """
    ords = db().orders

    with _client.start_session() as s:
        def txn(sess: ClientSession):
            curr = ords.find_one({"_id": order_id}, session=sess)
            if not curr:
                raise ValueError("Pedido no existe")
            if curr.get("status") == "APPROVED":
                return curr  # idempotente

            ords.update_one({"_id": order_id}, {"$set": {"status": "APPROVED"}}, session=sess)

            ev = AuditEvent(
                order_id=order_id,
                action="APPROVE",
                actor_sub=actor_sub,
                ts=datetime.utcnow().timestamp(),
                before={"status": curr.get("status")},
                after={"status": "APPROVED"},
                prev_hash=curr.get("last_event_hash"),
            )
            head = write_event(db(), ev)
            ords.update_one({"_id": order_id}, {"$set": {"last_event_hash": head}}, session=sess)

            return ords.find_one({"_id": order_id}, session=sess)

        try:
            approved = s.with_transaction(txn)
            return approved, None
        except ValueError as e:
            return None, str(e)
