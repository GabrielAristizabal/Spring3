# project/urls.py
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

from orders.views import (
    create_order,
    register_user,
    set_signer,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # Página principal redirige al formulario de pedidos
    path("", RedirectView.as_view(pattern_name="create_order", permanent=False), name="home"),

    # Usuarios
    path("users/register/", register_user, name="register_user"),
    path("firmante/usar/", set_signer, name="set_signer"),

    # Pedidos
    path("orders/create/", create_order, name="create_order"),
]
