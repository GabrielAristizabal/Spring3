# orders/services.py
import datetime as dt
from typing import Optional, Dict, Any, List

from django.conf import settings
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConfigurationError
from bson import ObjectId

from .crypto import generate_rsa_pair, make_operation_hash, sha256_hex


# --- Conexión a MongoDB ------------------------------------------------------

if not getattr(settings, "MONGODB_URI", ""):
    raise ConfigurationError(
        "MONGODB_URI está vacío. Define la URI en settings.py o en tu .env"
    )

_client = MongoClient(
    settings.MONGODB_URI,
    serverSelectionTimeoutMS=20000,
    connectTimeoutMS=20000,
)

# Prueba conexión (lanza si no hay acceso)
_client.admin.command("ping")

_db = _client[settings.MONGODB_DB]
# Alias público para importar como: from orders.services import db
db = _db


# --- Colecciones --------------------------------------------------------------

users = db["users"]
orders = db["orders"]
audits = db["audit_log"]


# --- Índices ------------------------------------------------------------------

def ensure_indexes() -> None:
    """Crea índices si no existen (idempotente)."""
    users.create_index([("username", ASCENDING)], unique=True)
    users.create_index([("fingerprint", ASCENDING)], unique=True)

    orders.create_index([("created_at", ASCENDING)])
    audits.create_index([("created_at", ASCENDING)])


# --- Usuarios / Llaves --------------------------------------------------------

def create_user_with_keys(
    username: str,
    email: str,
    passphrase: Optional[str] = None
) -> Dict[str, Any]:
    """
    Crea el usuario con par RSA y devuelve fingerprint + PEMs.
    NOTA DEMO: Se guarda la privada cifrada en BD; en producción evita guardarla
    o protégela con HSM/KMS.
    """
    priv_pem, pub_pem = generate_rsa_pair(passphrase or None)
    fingerprint = sha256_hex(pub_pem)[:16]

    users.insert_one(
        {
            "username": username,
            "email": email,
            "public_key_pem": pub_pem.decode(),
            "fingerprint": fingerprint,
            "private_key_pem_enc": priv_pem.decode(),  # DEMO: no lo hagas así en prod
            "created_at": dt.datetime.utcnow(),
        }
    )
    return {
        "fingerprint": fingerprint,
        "public_pem": pub_pem,
        "private_pem": priv_pem,
    }


def get_user(username: str) -> Optional[Dict[str, Any]]:
    return users.find_one({"username": username})


# --- Auditoría encadenada -----------------------------------------------------

def get_last_hash() -> str:
    last = audits.find_one(sort=[("created_at", -1)])
    return last["hash"] if last else ""


def insert_audit_entry(
    audit_payload: Dict[str, Any],
    signature_b64: str,
    signer: str,
    pub_fingerprint: str,
    envelope: Dict[str, Any],
) -> None:
    """
    Inserta en el log de auditoría un registro con:
    - payload de auditoría (incluye `hash` y `prev_hash`)
    - firma base64
    - quién firmó y fingerprint
    - sobre/firma/verificación para el front
    """
    audits.insert_one(
        {
            **audit_payload,
            "signature": signature_b64,
            "signer": signer,
            "pub_fingerprint": pub_fingerprint,
            "envelope": envelope,
            "created_at": dt.datetime.utcnow(),
        }
    )


# --- Pedidos (CRUD) -----------------------------------------------------------

def insert_order(order_doc: Dict[str, Any]) -> str:
    order_doc["created_at"] = dt.datetime.utcnow()
    res = orders.insert_one(order_doc)
    return str(res.inserted_id)


def find_order(_id: str) -> Optional[Dict[str, Any]]:
    try:
        return orders.find_one({"_id": ObjectId(_id)})
    except Exception:
        return None


def list_orders(limit: int = 50) -> List[Dict[str, Any]]:
    return list(orders.find().sort("created_at", -1).limit(limit))


def update_order(_id: str, fields: Dict[str, Any]) -> bool:
    return (
        orders.update_one({"_id": ObjectId(_id)}, {"$set": fields}).modified_count == 1
    )


def delete_order(_id: str) -> bool:
    return orders.delete_one({"_id": ObjectId(_id)}).deleted_count == 1


# --- Exports públicos ---------------------------------------------------------

__all__ = [
    "db",
    "users",
    "orders",
    "audits",
    "ensure_indexes",
    "create_user_with_keys",
    "get_user",
    "get_last_hash",
    "insert_audit_entry",
    "insert_order",
    "find_order",
    "list_orders",
    "update_order",
    "delete_order",
]
