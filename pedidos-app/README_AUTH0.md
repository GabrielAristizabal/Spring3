# Guía de Autenticación con Auth0

Esta aplicación requiere autenticación con Auth0 para acceder a las funcionalidades de creación de pedidos.

## ¿Cómo obtener el token JWT?

Tienes **4 opciones** para obtener el token JWT de Auth0:

### Opción 1: Desde la terminal (Recomendado para pruebas)

#### Usando el script Python (más fácil):
```bash
cd pedidos-app
python get_token.py
```

El script leerá las variables de entorno de tu archivo `.env` y te mostrará el token directamente.

#### Usando el script Bash:
```bash
cd pedidos-app
chmod +x get_token.sh
./get_token.sh
```

#### Manualmente con curl:
```bash
curl -X POST https://TU_DOMINIO.auth0.com/oauth/token \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "TU_CLIENT_ID",
    "client_secret": "TU_CLIENT_SECRET",
    "audience": "TU_AUDIENCE",
    "grant_type": "client_credentials"
  }'
```

Reemplaza:
- `TU_DOMINIO` → Tu dominio de Auth0 (ej: `mi-app.us.auth0.com`)
- `TU_CLIENT_ID` → El Client ID de tu aplicación en Auth0
- `TU_CLIENT_SECRET` → El Client Secret de tu aplicación
- `TU_AUDIENCE` → El Audience/API Identifier configurado en Auth0

### Opción 2: Desde Auth0 Dashboard

1. Ve a [Auth0 Dashboard](https://manage.auth0.com/)
2. Navega a **Applications** → Selecciona tu aplicación
3. Ve a la pestaña **"Test"** o **"Quick Start"**
4. Busca la sección **"Get Token"** o **"Try it out"**
5. Copia el token que aparece (empieza con `eyJ...`)

### Opción 3: Desde tu aplicación cliente

Si tienes una aplicación SPA, móvil o cualquier cliente configurado con Auth0:

- El token se obtiene automáticamente después del login
- Puedes copiarlo desde:
  - **Herramientas de desarrollador** del navegador (localStorage, sessionStorage)
  - El **callback de Auth0** después de la autenticación
  - Tu aplicación cliente que maneja el flujo OAuth

### Opción 4: Usando el proxy de autenticación

Si tienes el proxy de Auth0 (`auth_proxy.py`) configurado y funcionando, puedes obtener el token desde allí después de autenticarte.

## Configuración de variables de entorno

Asegúrate de tener estas variables en tu archivo `.env`:

```env
AUTH0_DOMAIN=tu-dominio.auth0.com
AUTH0_AUDIENCE=tu-audience
AUTH0_CLIENT_ID=tu-client-id
AUTH0_CLIENT_SECRET=tu-client-secret
AUTH_PROXY_URL=http://localhost:5000  # opcional
```

## Flujo de uso

1. **Obtén el token JWT** usando cualquiera de las opciones anteriores
2. **Ve a la página de login**: `http://localhost:8000/auth/login/`
3. **Pega el token** en el formulario
4. **Haz clic en "Iniciar sesión"**
5. Serás redirigido al registro de usuario (si es la primera vez) o a crear pedidos

## Alternativa: Usar el endpoint de callback

También puedes usar directamente el endpoint de callback con el token en la URL:

```
http://localhost:8000/auth/callback/?token=TU_TOKEN_AQUI
```

## Notas importantes

- Los tokens JWT tienen una **expiración** (normalmente 24 horas)
- Si el token expira, deberás obtener uno nuevo
- El token se guarda en la **sesión de Django** mientras navegas
- Puedes cerrar sesión usando el botón en la barra de navegación

## Solución de problemas

### Error: "Token expirado"
- Obtén un nuevo token usando cualquiera de las opciones anteriores

### Error: "Token inválido"
- Verifica que el token sea completo (no cortado)
- Asegúrate de que el token sea para la misma aplicación/audience configurada
- Verifica que las variables de entorno estén correctas

### Error: "No matching key found in JWKS"
- Verifica que `AUTH0_DOMAIN` esté correcto
- Asegúrate de que el token sea de Auth0 y no de otro proveedor

