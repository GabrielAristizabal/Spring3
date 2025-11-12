import os
import json
import jwt
import requests
import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify

# Cargar variables de entorno desde .env
load_dotenv()

app = Flask(__name__)

# === CONFIGURACIÓN ===
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
ALGORITHMS = ["RS256"]

# Dirección del microservicio de pedidos/verificador
VERIFICADOR_URL = os.getenv("VERIFICADOR_URL", "http://172.31.78.135:8080/create_order")

# Archivo de logs
LOG_FILE = "auth_logs.txt"


# === FUNCIONES AUXILIARES ===

def log_event(event_type, message):
    """Guarda los eventos en un archivo de logs local."""
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.datetime.now()}] [{event_type}] {message}\n")


def get_jwks():
    """Obtiene las llaves públicas de Auth0."""
    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    response = requests.get(jwks_url)
    response.raise_for_status()
    return response.json()


JWKS = get_jwks()


def verify_token(token):
    """Verifica y decodifica un token JWT de Auth0."""
    header = jwt.get_unverified_header(token)
    key = next((k for k in JWKS["keys"] if k["kid"] == header["kid"]), None)
    if not key:
        raise Exception("No matching key found in JWKS")

    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
    payload = jwt.decode(
        token,
        public_key,
        algorithms=ALGORITHMS,
        audience=AUTH0_AUDIENCE,
        issuer=f"https://{AUTH0_DOMAIN}/"
    )
    return payload


# === ENDPOINTS ===

@app.route("/health", methods=["GET"])
def health():
    """Verifica si el servicio Auth Proxy está operativo."""
    return jsonify({"status": "Auth proxy OK"}), 200


@app.before_request
def check_auth():
    """Valida el token JWT en todas las peticiones, excepto /health."""
    if request.path == "/health":
        return

    auth_header = request.headers.get("Authorization", None)
    if not auth_header or not auth_header.startswith("Bearer "):
        log_event("AUTH_FAIL", "Token ausente o mal formado")
        return jsonify({"error": "Token missing"}), 401

    token = auth_header.split()[1]
    try:
        payload = verify_token(token)
        log_event("AUTH_OK", f"Usuario autenticado: {payload.get('sub')}")
    except Exception as e:
        log_event("AUTH_FAIL", f"Token inválido: {str(e)}")
        return jsonify({"error": f"Invalid token: {str(e)}"}), 401


@app.route("/proxy_request", methods=["POST"])
def proxy_request():
    """Redirige la petición al microservicio de verificador/pedidos."""
    data = request.json
    try:
        response = requests.post(VERIFICADOR_URL, json=data, timeout=5)
        log_event("FORWARD_OK", f"Petición reenviada a {VERIFICADOR_URL} con estado {response.status_code}")
        return jsonify(response.json()), response.status_code
    except Exception as e:
        log_event("FORWARD_ERROR", f"Error al redirigir petición: {str(e)}")
        return jsonify({"error": f"Error forwarding request: {str(e)}"}), 500


# === MAIN ===
if __name__ == "__main__":
    print("🚀 Auth Proxy ejecutándose en http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000)
