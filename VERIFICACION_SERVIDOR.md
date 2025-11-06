# Verificación de Instalación en Servidor Linux

## Checklist antes de ejecutar Django:

### 1. Estructura de Directorios
Verifica que existe el directorio `orders/` con estos archivos (todos en **minúsculas**):
```
orders/
├── __init__.py      (¡IMPORTANTE! Debe existir)
├── apps.py
├── forms.py
├── service.py       (minúscula, NO Service.py)
├── urls.py          (minúscula, NO Urls.py)
└── views.py         (minúscula, NO Views.py)
```

### 2. Archivos en la Raíz
Asegúrate de tener en la raíz del proyecto:
```
manage.py
settings.py
urls.py
wsgi.py
requirements.txt
```

### 3. Verificación de Archivos
Ejecuta en el servidor Linux:
```bash
cd /home/ubuntu/pedidos-app
ls -la orders/    # Verifica que __init__.py existe
ls -la orders/*.py  # Verifica que todos los archivos están en minúsculas
```

### 4. Verificar que no hay archivos duplicados con mayúsculas
```bash
find orders/ -name "*[A-Z]*.py"  # No debería encontrar nada
```

### 5. Verificar permisos
```bash
chmod 644 orders/*.py
chmod 755 manage.py
```

### 6. Ejecutar desde el directorio correcto
Siempre ejecuta `manage.py` desde el directorio donde está `manage.py`:
```bash
cd /home/ubuntu/pedidos-app
python manage.py check
```

### 7. Si el error persiste
Verifica que el PYTHONPATH incluye el directorio del proyecto:
```bash
python -c "import sys; print(sys.path)"
```

El directorio `/home/ubuntu/pedidos-app` debería estar en la lista.

