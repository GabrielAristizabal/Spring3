#!/usr/bin/env python3
"""
Script para obtener un token JWT de Auth0 usando Client Credentials.
Uso: python get_token.py
"""
import os
import json
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de Auth0
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "tu-dominio.auth0.com")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID", "tu-client-id")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET", "tu-client-secret")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "tu-audience")

def get_token():
    """Obtiene un token de Auth0 usando Client Credentials."""
    url = f"https://{AUTH0_DOMAIN}/oauth/token"
    
    payload = {
        "client_id": AUTH0_CLIENT_ID,
        "client_secret": AUTH0_CLIENT_SECRET,
        "audience": AUTH0_AUDIENCE,
        "grant_type": "client_credentials"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"🔐 Obteniendo token de Auth0...")
    print(f"Dominio: {AUTH0_DOMAIN}")
    print()
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        token = data.get("access_token")
        
        if not token:
            print("❌ Error: No se recibió access_token en la respuesta")
            print(json.dumps(data, indent=2))
            return None
        
        print("✅ Token obtenido exitosamente:")
        print()
        print(token)
        print()
        print("📋 Copia el token de arriba y pégalo en el formulario de login.")
        print()
        print(f"💡 Tip: También puedes usar:")
        print(f"   curl -H 'Authorization: Bearer {token}' http://localhost:8000/auth/callback/?token={token}")
        
        return token
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error obteniendo el token: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(e.response.text)
        return None

if __name__ == "__main__":
    get_token()

