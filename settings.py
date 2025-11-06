import os
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB  = os.getenv("MONGODB_DB", "wms_dev")
ALLOWED_HOSTS = ["*"]  # o tu IP/dominio
