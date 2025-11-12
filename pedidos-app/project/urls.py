# project/urls.py
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

from orders.views import (
    create_order,
    register_user,
    set_signer,
    health,
    auth0_login,
    auth0_callback,
    auth0_logout,
    order_list,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # Página principal redirige al login de Auth0
    path("", RedirectView.as_view(pattern_name="auth0_login", permanent=False), name="home"),

    # Autenticación Auth0
    path("auth/login/", auth0_login, name="auth0_login"),
    path("auth/callback/", auth0_callback, name="auth0_callback"),
    path("auth/logout/", auth0_logout, name="auth0_logout"),

    # Usuarios
    path("users/register/", register_user, name="register_user"),
    path("firmante/usar/", set_signer, name="set_signer"),

    # Pedidos
    path("orders/create/", create_order, name="create_order"),
    path("orders/list/", order_list, name="order_list"),
    path("health/", health, name="health"),
]
