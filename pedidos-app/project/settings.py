# --- Básicos ---
SECRET_KEY = "dev-secret"
DEBUG = True
ALLOWED_HOSTS = ["*"]

ROOT_URLCONF = "project.urls"          # o "urls" si están en raíz
WSGI_APPLICATION = "project.wsgi.application"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 3rd party
    "social_django",        # si usas Auth0
    # Apps propias
    "orders",
]

# ⚠️ Orden requerido por admin:
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",             # ← antes de Auth
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",          # ← después de Session
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Opcional si usas social-auth:
    # "social_django.middleware.SocialAuthExceptionMiddleware",
]

# Requerido por admin: backend DjangoTemplates y messages/auth context processors
from pathlib import Path
import os
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parent.parent


# Cargar variables desde .env (si existe)
load_dotenv(BASE_DIR / ".env")

# *** Mongo ***
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    # Valor por defecto (cámbialo o deja vacío para obligar a definir en .env)
    ""
)
MONGODB_DB = os.getenv("MONGODB_DB", "wms_dev")
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],   # opcional
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # opcionales para social-auth:
                # "social_django.context_processors.backends",
                # "social_django.context_processors.login_redirect",
            ],
        },
    },
]

# DB mínima para admin/sesiones (usa sqlite local)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

STATIC_URL = "static/"
