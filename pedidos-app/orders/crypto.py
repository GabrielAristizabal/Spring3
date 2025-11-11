import os, json, base64, hashlib, datetime as dt
from typing import Optional, Tuple
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import (
    Encoding, PublicFormat, PrivateFormat, BestAvailableEncryption, NoEncryption,
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def b64e(b: bytes) -> str: return base64.b64encode(b).decode()
def b64d(s: str) -> bytes: return base64.b64decode(s)

def generate_rsa_pair(passphrase: Optional[str] = None) -> Tuple[bytes, bytes]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    enc = BestAvailableEncryption(passphrase.encode()) if passphrase else NoEncryption()
    priv_pem = key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, enc)
    pub_pem  = key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
    return priv_pem, pub_pem

def sign_payload(payload: dict, private_pem: bytes, passphrase: Optional[str] = None) -> str:
    key = serialization.load_pem_private_key(private_pem, password=passphrase.encode() if passphrase else None)
    sig = key.sign(
        canonical(payload),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
        hashes.SHA256(),
    )
    return b64e(sig)

def verify_signature(payload: dict, signature_b64: str, public_pem: bytes) -> bool:
    try:
        pub = serialization.load_pem_public_key(public_pem)
        pub.verify(
            base64.b64decode(signature_b64),
            canonical(payload),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False

def sign_hash(hex_hash: str, private_pem: bytes, passphrase: Optional[str] = None) -> str:
    return sign_payload({"operation_hash": hex_hash}, private_pem, passphrase)

def verify_hash_signature(hex_hash: str, signature_b64: str, public_pem: bytes) -> bool:
    return verify_signature({"operation_hash": hex_hash}, signature_b64, public_pem)

def hybrid_encrypt(payload: dict, public_pem: bytes) -> dict:
    data = canonical(payload)
    key   = os.urandom(32)
    nonce = os.urandom(12)
    ct = AESGCM(key).encrypt(nonce, data, None)

    pub = serialization.load_pem_public_key(public_pem)
    wrapped = pub.encrypt(
        key,
        padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )
    return {
        "alg": "AES-256-GCM+RSA-OAEP",
        "nonce": b64e(nonce),
        "ciphertext": b64e(ct),
        "wrapped_key": b64e(wrapped),
    }

def hybrid_decrypt(envelope: dict, private_pem: bytes, passphrase: Optional[str] = None) -> dict:
    key = serialization.load_pem_private_key(private_pem, password=passphrase.encode() if passphrase else None)\
        .decrypt(
            base64.b64decode(envelope["wrapped_key"]),
            padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
        )
    data = AESGCM(key).decrypt(base64.b64decode(envelope["nonce"]), base64.b64decode(envelope["ciphertext"]), None)
    return json.loads(data.decode())

def make_operation_hash(order_doc: dict, user_id: str, prev_hash: str) -> dict:
    ts = dt.datetime.utcnow().isoformat()
    payload = {"order": order_doc, "user": user_id, "timestamp": ts, "prev_hash": prev_hash or ""}
    payload["hash"] = sha256_hex(canonical(payload))
    return payload
