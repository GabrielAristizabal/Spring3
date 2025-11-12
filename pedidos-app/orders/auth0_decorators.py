# orders/auth0_decorators.py
"""
Decoradores para proteger vistas con autenticación Auth0.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .auth0_client import (
    get_token_from_session,
    verify_token,
    get_auth0_user_from_session,
)


def auth0_required(view_func):
    """
    Decorador que requiere que el usuario esté autenticado con Auth0.
    Redirige a /auth/login/ si no hay token válido.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        token = get_token_from_session(request)
        
        if not token:
            messages.error(request, "Debes iniciar sesión con Auth0 para acceder a esta página.")
            return redirect("auth0_login")
        
        # Verificar que el token sigue siendo válido
        try:
            payload = verify_token(token)
            # Token válido, continuar
            return view_func(request, *args, **kwargs)
        except Exception as e:
            # Token inválido o expirado, limpiar sesión y redirigir
            from .auth0_client import clear_auth0_session
            clear_auth0_session(request)
            messages.error(request, "Tu sesión ha expirado. Por favor, inicia sesión nuevamente.")
            return redirect("auth0_login")
    
    return wrapper


def auth0_optional(view_func):
    """
    Decorador que permite acceso sin autenticación, pero agrega información
    de Auth0 al contexto si está disponible.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # No bloquea el acceso, solo agrega info si está disponible
        return view_func(request, *args, **kwargs)
    
    return wrapper

