#!/usr/bin/env python3
import os
import sys

def main():
    # Cambia "monitoring.settings" si tu proyecto se llama distinto
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "monitoring.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. ¿Está instalado y en el PYTHONPATH?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
