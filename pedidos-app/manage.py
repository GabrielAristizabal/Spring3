#!/usr/bin/env python3
import os
import sys
from pathlib import Path

def main():
    # Asegura que el directorio del proyecto esté en el PYTHONPATH
    BASE_DIR = Path(__file__).resolve().parent
    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))

    # Carga variables de entorno desde .env (si tienes python-dotenv)
    try:
        from dotenv import load_dotenv
        load_dotenv(BASE_DIR / ".env")
    except Exception:
        pass

    # Usa DJANGO_SETTINGS_MODULE de entorno si existe; si no, 'settings'
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", "settings"))

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django no está instalado o no está en el PYTHONPATH.\n"
            "Activa tu venv e instala dependencias (pip install -r requirements.txt)."
        ) from exc

    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
