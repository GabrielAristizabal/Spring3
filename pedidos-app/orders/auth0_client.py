# orders/auth0_client.py
"""
Cliente para validar tokens JWT de Auth0 usando JWKS.
Similar al proxy Flask pero integrado en Django.
"""
import os
import json
import jwt
import requests
from typing import Optional, Dict
from django.conf import settings
from django.core.cache import cache

# Configuración de Auth0
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", getattr(settings, "AUTH0_DOMAIN", ""))
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", getattr(settings, "AUTH0_AUDIENCE", ""))
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID", getattr(settings, "AUTH0_CLIENT_ID", ""))
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET", getattr(settings, "AUTH0_CLIENT_SECRET", ""))
AUTH0_ALGORITHMS = ["RS256"]

# URL del proxy Auth0 (si está disponible)
AUTH_PROXY_URL = os.getenv("AUTH_PROXY_URL", "http://localhost:5000")


def get_jwks():
    """Obtiene las llaves públicas de Auth0 (con caché)."""
    cache_key = "auth0_jwks"
    jwks = cache.get(cache_key)
    
    if jwks is None:
        jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
        try:
            response = requests.get(jwks_url, timeout=5)
            response.raise_for_status()
            jwks = response.json()
            # Cachear por 1 hora
            cache.set(cache_key, jwks, 3600)
        except Exception as e:
            raise Exception(f"Error obteniendo JWKS de Auth0: {e}")
    
    return jwks


def verify_token(token: str) -> Dict:
    """
    Verifica y decodifica un token JWT de Auth0.
    Retorna el payload del token si es válido.
    """
    try:
        # Obtener header del token
        header = jwt.get_unverified_header(token)
        
        # Obtener JWKS
        jwks = get_jwks()
        
        # Buscar la llave correspondiente
        key = next((k for k in jwks["keys"] if k["kid"] == header["kid"]), None)
        if not key:
            raise Exception("No matching key found in JWKS")
        
        # Convertir JWK a llave pública RSA
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
        
        # Verificar y decodificar el token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=AUTH0_ALGORITHMS,
            audience=AUTH0_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/"
        )
        
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token expirado")
    except jwt.InvalidTokenError as e:
        raise Exception(f"Token inválido: {str(e)}")
    except Exception as e:
        raise Exception(f"Error verificando token: {str(e)}")


def validate_token_from_request(request) -> Optional[Dict]:
    """
    Extrae y valida el token JWT del header Authorization de la petición.
    Retorna el payload si es válido, None si no hay token o es inválido.
    """
    auth_header = request.headers.get("Authorization", None)
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split()[1]
    try:
        return verify_token(token)
    except Exception:
        return None


def get_token_from_session(request) -> Optional[str]:
    """Obtiene el token de Auth0 almacenado en la sesión."""
    return request.session.get("auth0_token")


def set_token_in_session(request, token: str, payload: Dict):
    """Guarda el token y datos del usuario en la sesión."""
    request.session["auth0_token"] = token
    request.session["auth0_user"] = {
        "sub": payload.get("sub"),
        "email": payload.get("email"),
        "name": payload.get("name"),
        "nickname": payload.get("nickname"),
    }
    request.session["auth0_authenticated"] = True


def clear_auth0_session(request):
    """Limpia los datos de Auth0 de la sesión."""
    request.session.pop("auth0_token", None)
    request.session.pop("auth0_user", None)
    request.session.pop("auth0_authenticated", None)


def get_auth0_user_from_session(request) -> Optional[Dict]:
    """Obtiene los datos del usuario de Auth0 desde la sesión."""
    if request.session.get("auth0_authenticated"):
        return request.session.get("auth0_user")
    return None

