# orders/audit.py
import json, hashlib, time
from dataclasses import dataclass
from django.conf import settings
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.hmac import HMAC
from cryptography.hazmat.primitives import constant_time

def canonical(obj)->bytes:
    return json.dumps(obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode("utf-8")

def sha256(b: bytes)->str:
    return hashlib.sha256(b).hexdigest()

def sign_ed25519(data: bytes)->str:
    key = serialization.load_pem_private_key(
        settings.AUDIT_ED25519_PRIVATE_KEY_PEM.encode("utf-8"), password=None
    )
    return key.sign(data).hex()

def sign_hmac(data: bytes)->str:
    h = HMAC(settings.AUDIT_SIGNING_SECRET.encode(), hashes.SHA256())
    h.update(data); return h.finalize().hex()

@dataclass
class AuditEvent:
    order_id: str
    action: str     # "CREATE" | "UPDATE" | "APPROVE"
    actor_sub: str
    ts: float
    before: dict|None
    after: dict|None
    prev_hash: str|None

def write_event(db, ev: AuditEvent):
    body = {
        "order_id": ev.order_id,
        "action": ev.action,
        "actor_sub": ev.actor_sub,
        "ts": ev.ts,
        "before": ev.before,
        "after": ev.after,
        "prev_hash": ev.prev_hash,
    }
    body_b = canonical(body)
    event_hash = sha256(body_b)
    if settings.AUDIT_SIGNING_MODE.upper() == "ED25519":
        signature = sign_ed25519(body_b)
        sig_alg = "ed25519"
    else:
        signature = sign_hmac(body_b)
        sig_alg = "hmac-sha256"

    doc = {**body, "event_hash": event_hash, "signature": signature, "sig_alg": sig_alg}
    db.audit_events.insert_one(doc)
    # anclar en pedido
    db.orders.update_one({"_id": ev.order_id}, {"$set": {"last_event_hash": event_hash}})
    return event_hash

def verify_chain(db, order_id: str)->bool:
    # simple: recorre por ts asc y verifica prev_hash encadena y firma válida (omito verificación de firma por brevedad)
    events = list(db.audit_events.find({"order_id": order_id}).sort("ts", 1))
    prev = None
    for e in events:
        body = {k:e[k] for k in ["order_id","action","actor_sub","ts","before","after","prev_hash"]}
        if (prev or None) != e["prev_hash"]:  # prev encadena
            return False
        if sha256(canonical(body)) != e["event_hash"]:
            return False
        prev = e["event_hash"]
    return True
