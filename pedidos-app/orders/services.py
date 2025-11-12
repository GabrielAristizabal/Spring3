# orders/services.py
from __future__ import annotations

import json
import base64
import hashlib
import datetime as dt
from types import SimpleNamespace

from django.conf import settings
from pymongo import MongoClient, ASCENDING

# ====== Conexión Mongo ======
_client = MongoClient(settings.MONGODB_URI)
_db = _client[settings.MONGODB_DB]

users  = _db["users"]
orders = _db["orders"]
audits = _db["audit_log"]

# Exponer un objeto db.* para usar en vistas
db = SimpleNamespace(users=users, orders=orders, audits=audits)

# ====== Utilidades básicas ======
def utcnow() -> dt.datetime:
    return dt.datetime.utcnow()

def ensure_indexes():
    users.create_index([("username", ASCENDING)], unique=False)
    users.create_index([("document", ASCENDING)], unique=True)
    users.create_index([("created_at", ASCENDING)])
    orders.create_index([("created_at", ASCENDING)])
    audits.create_index([("created_at", ASCENDING)])

def get_user_by_document(doc: str) -> dict | None:
    if not doc:
        return None
    return users.find_one({"document": doc})

def get_last_hash() -> str:
    last = audits.find_one(sort=[("created_at", -1)])
    return last["chain_hash"] if last and last.get("chain_hash") else ""

# ====== Cripto (firma RSA y hash) ======
def generar_llaves_rsa_pem(passphrase: str | None = None):
    """
    Envuelve la función que ya tengas en .crypto para generar llaves.
    Retorna (priv_pem, pub_pem) en bytes.
    """
    from .crypto import generate_rsa_pair
    return generate_rsa_pair(passphrase or None)

def _sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()

def make_operation_hash(payload: dict) -> str:
    """
    Hash estable del payload de operación (datos + timestamp + usuario).
    """
    # json ordenado para que el hash sea determinista
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    hash_result = _sha256_hex(body)
    
    # Log para demostración académica
    print(f"      Payload a hashear: {len(body)} bytes")
    print(f"      JSON ordenado (sort_keys=True) para determinismo")
    print(f"      Función hash: SHA-256")
    print(f"      Tamaño del hash: 256 bits (64 caracteres hex)")
    
    return hash_result

def _sign_rsa_b64(private_pem: str | bytes, data_to_sign: bytes | str) -> str:
    """
    Firma RSA-PSS/SHA256. Devuelve firma en base64.
    Requiere 'cryptography' (normal en proyectos Django).
    """
    if isinstance(private_pem, str):
        private_pem = private_pem.encode("utf-8")
    if isinstance(data_to_sign, str):
        data_to_sign = data_to_sign.encode("utf-8")

    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    key = serialization.load_pem_private_key(private_pem, password=None)
    signature = key.sign(
        data_to_sign,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("utf-8")

# ====== CRUD / consultas ======
def list_orders(limit: int = 50) -> list[dict]:
    return list(orders.find().sort("created_at", -1).limit(limit))

def find_order(_id: str) -> dict | None:
    from bson import ObjectId
    try:
        return orders.find_one({"_id": ObjectId(_id)})
    except Exception:
        return None

def insert_order(order_doc: dict) -> str:
    order_doc["created_at"] = utcnow()
    res = orders.insert_one(order_doc)
    return str(res.inserted_id)

# ====== Creador con no-repudio ======
def crear_pedido_firmado(
    *,
    cliente: str,
    documento: str,
    fecha: str,
    items_json: str,
    signer: dict,
) -> str:
    """
    - Parsea items_json
    - Inserta pedido
    - Genera hash de operación (datos + timestamp + usuario)
    - Firma el hash con la clave privada del usuario
    - Encadena en audit_log con chain_hash (tipo ledger)
    """
    # 1) Items
    try:
        items = json.loads(items_json)
    except Exception as e:
        raise ValueError(f"items_json inválido: {e}")

    # 2) Inserta pedido
    order_doc = {
        "client": cliente,
        "document": documento,
        "date": fecha,
        "items": items,
        "created_by": signer.get("document") if signer else None,
        "created_at": utcnow(),
    }
    order_id = insert_order(order_doc)

    # 3) Construye payload de la operación a auditar
    ts = utcnow().isoformat() + "Z"
    op_payload = {
        "action": "create_order",
        "order_id": order_id,
        "client": cliente,
        "document": documento,
        "date": fecha,
        "items": items,
        "user": {
            "document": signer.get("document"),
            "name": signer.get("name"),
        },
        "timestamp": ts,
    }

    # 4) Hash de la operación
    print("\n" + "="*80)
    print("PROCESO DE SEGURIDAD: HASH Y CIFRADO")
    print("="*80)
    
    print("\n[PASO 1] Generando hash SHA-256 de la operación...")
    op_hash = make_operation_hash(op_payload)
    print(f"   Hash generado: {op_hash[:32]}...{op_hash[-16:]}")
    print(f"   Longitud del hash: {len(op_hash)} caracteres (SHA-256)")
    print(f"   Algoritmo: SHA-256")
    
    # 5) Firma con la clave privada del usuario (si está guardada)
    priv_pem = signer.get("priv_key")
    if not priv_pem:
        # En algunos setups solo se guarda la pública; puedes cambiarla por una del sistema si aplicara.
        raise RuntimeError("El usuario no tiene clave privada almacenada para firmar (demo).")

    print("\n [PASO 2] Firmando el hash con clave privada RSA...")
    print(f"   Usuario firmante: {signer.get('name', 'N/A')} ({signer.get('document', 'N/A')})")
    print(f"   Algoritmo de firma: RSA-PSS con SHA-256")
    signature_b64 = _sign_rsa_b64(priv_pem, op_hash)
    print(f"   Firma generada: {signature_b64[:40]}...{signature_b64[-20:]}")
    print(f"   Longitud de la firma: {len(signature_b64)} caracteres (base64)")
    print(f"   No repudio garantizado: Solo el dueño de la clave privada pudo crear esta firma")

    # 6) Hash encadenado (ledger)
    prev_chain = get_last_hash()
    print("\n[PASO 3] Creando hash encadenado (Ledger/Blockchain)...")
    if prev_chain:
        print(f"  Hash anterior en la cadena: {prev_chain[:32]}...{prev_chain[-16:]}")
    else:
        print(f"  Hash anterior: (Primer registro en la cadena)")
    chain_hash = _sha256_hex((prev_chain + op_hash).encode("utf-8"))
    print(f"   Hash encadenado generado: {chain_hash[:32]}...{chain_hash[-16:]}")
    print(f"   Integridad: Cualquier modificación romperá toda la cadena")
    print(f"   Tipo: Ledger inmutable (similar a blockchain)")

    # 7) Inserta en audit_log
    audits.insert_one({
        "order_id": order_id,
        "action": "create_order",
        "op_payload": op_payload,
        "op_hash": op_hash,
        "signature": signature_b64,
        "signer_document": signer.get("document"),
        "chain_prev": prev_chain,
        "chain_hash": chain_hash,
        "created_at": utcnow(),
    })
    
    print("\n[PASO 4] Guardando en audit_log...")
    print(f"  Registro de auditoría guardado con ID: {order_id}")
    print(f"  Campos guardados:")
    print(f"   - op_hash: Hash de la operación")
    print(f"   - signature: Firma digital RSA-PSS")
    print(f"   - chain_prev: Hash del registro anterior")
    print(f"   - chain_hash: Hash encadenado (ledger)")
    
    print("\n" + "="*80)
    print("PROCESO DE SEGURIDAD COMPLETADO")
    print("="*80)
    print(f" Pedido ID: {order_id}")
    print(f" Hash SHA-256: {op_hash}")
    print(f"  Firma RSA-PSS: {signature_b64[:50]}...")
    print(f" Hash encadenado: {chain_hash}")
    print(f"  Seguridad garantizada: Integridad + No Repudio + Trazabilidad")
    print("="*80 + "\n")

    return order_id
