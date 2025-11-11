import os
import json
import time
import boto3
import base64
import hashlib
from flask import Flask, request, jsonify, abort
import psycopg2
from psycopg2.extras import RealDictCursor

# Config from env (set via Terraform/SSM or export)
DB_HOST = os.environ.get("DB_HOST", "<REPLACE_WITH_RDS_ENDPOINT>")
DB_PORT = int(os.environ.get("DB_PORT", 5432))
DB_NAME = os.environ.get("DB_NAME", "wmsdb")
DB_USER = os.environ.get("DB_USER", "wmsadmin")
DB_PASS = os.environ.get("DB_PASS", "changeme")
KMS_KEY_ID = os.environ.get("KMS_KEY_ID", None)
AUTH0_AUDIENCE = os.environ.get("AUTH0_AUDIENCE", "<AUTH0_AUDIENCE>")
AUTH0_ISSUER = os.environ.get("AUTH0_ISSUER", "<https://your-auth0-domain/>")

app = Flask(__name__)

# KMS client
kms = boto3.client("kms", region_name=os.environ.get("AWS_REGION", "us-east-1"))

# DB connection helper
def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASS
    )

# Simple JWT verification (only checks signature and issuer/audience minimal)
# For production use Auth0 SDK / jwks and full validation. Here minimal placeholder.
def check_auth(req):
    auth = req.headers.get("Authorization", None)
    if not auth:
        abort(401, "Missing Authorization")
    # In real code validate JWT with Auth0 JWKS. For academic demo assume token contains sub header.
    # For now extract a fake user from header for tests: "Bearer user:email@example.com"
    parts = auth.split()
    if len(parts) != 2:
        abort(401)
    token = parts[1]
    # naive: if token contains "user:" then parse
    if token.startswith("user:"):
        return {"sub": token.split("user:")[1]}
    # else proceed (incomplete)
    return {"sub": "unknown"}

# Utility to compute SHA-256 hash of payload
def compute_hash(payload: dict):
    s = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    h = hashlib.sha256(s.encode("utf-8")).digest()
    return base64.b64encode(h).decode()

# Sign a hash using KMS: uses asymmetric CMK capable of Sign/Verify or Envelope approach.
def kms_sign(message_base64):
    # Here we assume KMS supports Sign for the key (asymmetric key)
    if not KMS_KEY_ID:
        raise Exception("KMS_KEY_ID not configured")
    msg = base64.b64decode(message_base64)
    resp = kms.sign(
        KeyId=KMS_KEY_ID,
        Message=msg,
        MessageType="RAW",
        SigningAlgorithm="RSASSA_PKCS1_V1_5_SHA_256"
    )
    signature = base64.b64encode(resp["Signature"]).decode()
    return signature

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status":"ok"})

@app.route("/orders", methods=["POST"])
def create_order():
    user = check_auth(request)
    payload = request.json
    if not payload:
        abort(400, "Missing payload")
    order = {
        "items": payload.get("items", []),
        "amount": payload.get("amount", 0),
        "status": "created",
        "created_by": user["sub"],
        "created_at": int(time.time())
    }
    # compute hash
    h = compute_hash(order)
    # sign hash with KMS
    sig = kms_sign(base64.b64encode(hashlib.sha256(json.dumps(order, sort_keys=True).encode()).digest()).decode())

    # persist to DB
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO orders (data, created_by, created_at, hash, signature)
        VALUES (%s, %s, to_timestamp(%s), %s, %s) RETURNING id;
    """, (json.dumps(order), user["sub"], order["created_at"], h, sig))
    order_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"order_id": order_id, "hash": h, "signature": sig})

@app.route("/orders/<int:order_id>/approve", methods=["POST"])
def approve_order(order_id):
    user = check_auth(request)
    # load order
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, data FROM orders WHERE id=%s;", (order_id,))
    record = cur.fetchone()
    if not record:
        abort(404, "Order not found")
    data = json.loads(record["data"])
    data["status"] = "approved"
    data["approved_by"] = user["sub"]
    data["approved_at"] = int(time.time())
    # recompute hash and sign
    h = compute_hash(data)
    sig = kms_sign(base64.b64encode(hashlib.sha256(json.dumps(data, sort_keys=True).encode()).digest()).decode())

    # update DB and audit table
    cur.execute("""
        UPDATE orders SET data=%s, hash=%s, signature=%s WHERE id=%s;
    """, (json.dumps(data), h, sig, order_id))
    cur.execute("""
        INSERT INTO audit (order_id, action, user_id, ts, old_data, new_data)
        VALUES (%s, %s, %s, now(), %s, %s);
    """, (order_id, "approve", user["sub"], record["data"], json.dumps(data)))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"order_id": order_id, "hash": h, "signature": sig})

if __name__ == "__main__":
    # For dev only; in production use gunicorn
    app.run(host="0.0.0.0", port=5000)
