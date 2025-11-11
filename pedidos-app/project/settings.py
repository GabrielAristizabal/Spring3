import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret")
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin","django.contrib.auth","django.contrib.contenttypes",
    "django.contrib.sessions","django.contrib.messages","django.contrib.staticfiles",
    "social_django",
    "orders",
]

LOGIN_URL = "/login/auth0"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "http://<IP_PUBLICA_APP>:8080"

SOCIAL_AUTH_TRAILING_SLASH = False
SOCIAL_AUTH_AUTH0_DOMAIN  = os.getenv("AUTH0_DOMAIN")          # p.ej. dev-xxx.auth0.com
SOCIAL_AUTH_AUTH0_KEY     = os.getenv("AUTH0_CLIENT_ID")
SOCIAL_AUTH_AUTH0_SECRET  = os.getenv("AUTH0_CLIENT_SECRET")
SOCIAL_AUTH_AUTH0_SCOPE   = ["openid","profile","email","role"]

AUTHENTICATION_BACKENDS = (
    "orders.auth0_backend.Auth0",   # tu backend (igual al del lab)
    "django.contrib.auth.backends.ModelBackend",
)

# Mongo / DB
MONGODB_URI = os.getenv("MONGODB_URI")  # ej: mongodb://...
MONGODB_DB  = os.getenv("MONGODB_DB","wms_dev")

# Firma de la bitácora (elige una)
AUDIT_SIGNING_MODE = os.getenv("AUDIT_SIGNING_MODE","ED25519")  # ED25519 | HMAC
AUDIT_SIGNING_SECRET = os.getenv("AUDIT_SIGNING_SECRET")        # si HMAC
AUDIT_ED25519_PRIVATE_KEY_PEM = os.getenv("AUDIT_ED25519_PRIV") # si Ed25519 (PEM)
