#!/bin/bash
# Script para obtener un token JWT de Auth0 usando Client Credentials
# Uso: ./get_token.sh

# Cargar variables de entorno desde .env si existe
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Variables (ajusta según tu configuración)
AUTH0_DOMAIN="${AUTH0_DOMAIN:-tu-dominio.auth0.com}"
AUTH0_CLIENT_ID="${AUTH0_CLIENT_ID:-tu-client-id}"
AUTH0_CLIENT_SECRET="${AUTH0_CLIENT_SECRET:-tu-client-secret}"
AUTH0_AUDIENCE="${AUTH0_AUDIENCE:-tu-audience}"

echo "🔐 Obteniendo token de Auth0..."
echo "Dominio: $AUTH0_DOMAIN"
echo ""

# Hacer la petición para obtener el token
RESPONSE=$(curl -s -X POST "https://${AUTH0_DOMAIN}/oauth/token" \
  -H "Content-Type: application/json" \
  -d "{
    \"client_id\": \"${AUTH0_CLIENT_ID}\",
    \"client_secret\": \"${AUTH0_CLIENT_SECRET}\",
    \"audience\": \"${AUTH0_AUDIENCE}\",
    \"grant_type\": \"client_credentials\"
  }")

# Extraer el token del JSON
TOKEN=$(echo $RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Error obteniendo el token:"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
    exit 1
fi

echo "✅ Token obtenido exitosamente:"
echo ""
echo "$TOKEN"
echo ""
echo "📋 Copia el token de arriba y pégalo en el formulario de login."
echo ""
echo "💡 Tip: También puedes usar:"
echo "   curl -H 'Authorization: Bearer $TOKEN' http://localhost:8000/auth/callback/?token=$TOKEN"

