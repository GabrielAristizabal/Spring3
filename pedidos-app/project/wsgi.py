# wsgi.py (en la raíz, junto a manage.py y settings.py)
import os
from django.core.wsgi import get_wsgi_application

# Si movieras settings a un paquete, cambia "settings" por "project.settings"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

application = get_wsgi_application()
