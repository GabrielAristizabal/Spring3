from flask import Flask, request, jsonify
import requests, json, datetime, os

app = Flask(__name__)

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUDIENCE = os.getenv("API_IDENTIFIER")
LOG_FILE = "/home/ubuntu/logs/auth_proxy.log"

def log_event(message):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.datetime.utcnow()}] {message}\n")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "Auth proxy OK"}), 200

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    # ejemplo: {"username": "user@example.com", "password": "1234"}
    payload = {
        "grant_type": "password",
        "username": data["username"],
        "password": data["password"],
        "audience": AUDIENCE,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    url = f"https://{AUTH0_DOMAIN}/oauth/token"
    r = requests.post(url, json=payload)

    log_event(f"Login attempt: {data['username']} - Status {r.status_code}")
    return jsonify(r.json()), r.status_code

@app.route("/validate", methods=["POST"])
def validate_token():
    token = request.json.get("token")
    url = f"https://{AUTH0_DOMAIN}/userinfo"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers)
    log_event(f"Token validation - Status {r.status_code}")
    return jsonify(r.json()), r.status_code

if __name__ == "__main__":
    os.makedirs("/home/ubuntu/logs", exist_ok=True)
    app.run(host="0.0.0.0", port=5000)
