import datetime as dt
from django.conf import settings
from pymongo import MongoClient, ASCENDING
from .crypto import generate_rsa_pair, make_operation_hash

_client = MongoClient(settings.MONGODB_URI)
_db = _client[settings.MONGODB_DB]

users  = _db["users"]
orders = _db["orders"]
audits = _db["audit_log"]

def ensure_indexes():
    users.create_index([("username", ASCENDING)], unique=True)
    users.create_index([("fingerprint", ASCENDING)], unique=True)
    orders.create_index([("created_at", ASCENDING)])
    audits.create_index([("created_at", ASCENDING)])

def create_user_with_keys(username: str, email: str, passphrase: str | None) -> dict:
    from .crypto import sha256_hex
    priv_pem, pub_pem = generate_rsa_pair(passphrase or None)
    fingerprint = sha256_hex(pub_pem)[:16]
    users.insert_one({
        "username": username,
        "email": email,
        "public_key_pem": pub_pem.decode(),
        "fingerprint": fingerprint,
        "private_key_pem_enc": priv_pem.decode(),  # DEMO: en prod NO guardes la privada
        "created_at": dt.datetime.utcnow(),
    })
    return {"fingerprint": fingerprint, "public_pem": pub_pem, "private_pem": priv_pem}

def get_user(username: str) -> dict | None:
    return users.find_one({"username": username})

def get_last_hash() -> str:
    last = audits.find_one(sort=[("created_at", -1)])
    return last["hash"] if last else ""

def insert_audit_entry(audit_payload: dict, signature_b64: str, signer: str, pub_fingerprint: str, envelope: dict):
    audits.insert_one({
        **audit_payload,
        "signature": signature_b64,
        "signer": signer,
        "pub_fingerprint": pub_fingerprint,
        "envelope": envelope,
        "created_at": dt.datetime.utcnow(),
    })

def insert_order(order_doc: dict) -> str:
    order_doc["created_at"] = dt.datetime.utcnow()
    res = orders.insert_one(order_doc)
    return str(res.inserted_id)

def find_order(_id: str) -> dict | None:
    from bson import ObjectId
    try: return orders.find_one({"_id": ObjectId(_id)})
    except Exception: return None

def list_orders(limit=50):
    return list(orders.find().sort("created_at", -1).limit(limit))

def update_order(_id: str, fields: dict) -> bool:
    from bson import ObjectId
    return orders.update_one({"_id": ObjectId(_id)}, {"$set": fields}).modified_count == 1

def delete_order(_id: str) -> bool:
    from bson import ObjectId
    return orders.delete_one({"_id": ObjectId(_id)}).deleted_count == 1
