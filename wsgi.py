import os
import sys
from pathlib import Path
from django.core.wsgi import get_wsgi_application

# Asegurar que el directorio del proyecto esté en el PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
application = get_wsgi_application()
