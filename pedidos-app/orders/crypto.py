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
    """
    Cifrado híbrido: AES-256-GCM (simétrico) + RSA-OAEP (asimétrico).
    Combina la velocidad del cifrado simétrico con la seguridad del asimétrico.
    """
    print("\n" + "="*80)
    print("PROCESO DE CIFRADO SIMÉTRICO (Híbrido)")
    print("="*80)
    
    data = canonical(payload)
    print(f"\n[PASO 1] Preparando datos para cifrado...")
    print(f"   Tamaño de datos: {len(data)} bytes")
    
    # Generar clave simétrica aleatoria
    key = os.urandom(32)
    nonce = os.urandom(12)
    print(f"\n[PASO 2] Generando clave simétrica AES-256...")
    print(f"   Clave AES generada: {len(key)} bytes (256 bits)")
    print(f"   Nonce/IV generado: {len(nonce)} bytes (96 bits)")
    print(f"   Algoritmo simétrico: AES-256-GCM (Galois/Counter Mode)")
    print(f"   Características: Autenticación + Cifrado")
    
    # Cifrar con AES-GCM
    print(f"\n[PASO 3] Cifrando datos con AES-256-GCM...")
    ct = AESGCM(key).encrypt(nonce, data, None)
    print(f"   Ciphertext generado: {len(ct)} bytes")
    print(f"   Tamaño original: {len(data)} bytes")
    print(f"   Tamaño cifrado: {len(ct)} bytes")
    print(f"   Modo: GCM (incluye autenticación integrada)")

    # Cifrar la clave simétrica con RSA
    pub = serialization.load_pem_public_key(public_pem)
    print(f"\n[PASO 4] Cifrando clave simétrica con RSA-OAEP...")
    print(f"   Algoritmo asimétrico: RSA-OAEP")
    print(f"   Padding: OAEP con MGF1-SHA256")
    print(f"   Hash: SHA-256")
    wrapped = pub.encrypt(
        key,
        padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )
    print(f"   Clave envuelta: {len(wrapped)} bytes")
    
    result = {
        "alg": "AES-256-GCM+RSA-OAEP",
        "nonce": b64e(nonce),
        "ciphertext": b64e(ct),
        "wrapped_key": b64e(wrapped),
    }
    
    print(f"\n[RESULTADO] Cifrado híbrido completado:")
    print(f"   Algoritmo: {result['alg']}")
    print(f"   Ciphertext (base64): {result['ciphertext'][:50]}...")
    print(f"   Clave envuelta (base64): {result['wrapped_key'][:50]}...")
    print(f"   Nonce (base64): {result['nonce']}")
    print(f"    Seguridad: Cifrado simétrico rápido + Clave protegida con RSA")
    print("="*80 + "\n")
    
    return result

def hybrid_decrypt(envelope: dict, private_pem: bytes, passphrase: Optional[str] = None) -> dict:
    """
    Descifrado híbrido: Primero descifra la clave con RSA, luego los datos con AES.
    """
    print("\n" + "="*80)
    print("PROCESO DE DESCIFRADO SIMÉTRICO (Híbrido)")
    print("="*80)
    
    print(f"\n[PASO 1] Descifrando clave simétrica con RSA-OAEP...")
    print(f"   Usando clave privada RSA para descifrar la clave envuelta")
    key = serialization.load_pem_private_key(private_pem, password=passphrase.encode() if passphrase else None)\
        .decrypt(
            base64.b64decode(envelope["wrapped_key"]),
            padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
        )
    print(f"   Clave simétrica recuperada: {len(key)} bytes (256 bits)")
    
    print(f"\n[PASO 2] Descifrando datos con AES-256-GCM...")
    print(f"   Algoritmo: AES-256-GCM")
    print(f"   Nonce usado: {envelope['nonce']}")
    data = AESGCM(key).decrypt(base64.b64decode(envelope["nonce"]), base64.b64decode(envelope["ciphertext"]), None)
    print(f"   Datos descifrados: {len(data)} bytes")
    print(f"   Verificación: GCM valida autenticidad automáticamente")
    
    result = json.loads(data.decode())
    print(f"\n[RESULTADO] Descifrado completado exitosamente")
    print(f"   Datos recuperados: {len(result)} campos")
    print("="*80 + "\n")
    
    return result

def make_operation_hash(order_doc: dict, user_id: str, prev_hash: str) -> dict:
    ts = dt.datetime.utcnow().isoformat()
    payload = {"order": order_doc, "user": user_id, "timestamp": ts, "prev_hash": prev_hash or ""}
    payload["hash"] = sha256_hex(canonical(payload))
    return payload
