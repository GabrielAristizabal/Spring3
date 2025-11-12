# project/urls.py
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

from orders.views import (
    home,
    order_list,
    order_detail,
    order_create,
    order_update,
    order_delete,
    register_user,
    verify,
    set_signer,
)


urlpatterns = [
    path("admin/", admin.site.urls),

    # Home -> lista
    path("", RedirectView.as_view(pattern_name="order_list", permanent=False), name="home"),

    # Usuarios
    path("users/register/", register_user, name="register_user"),
    path("firmante/usar/", set_signer, name="set_signer"),

    # Pedidos
    path("orders/", order_list, name="order_list"),
    path("orders/create/", order_create, name="order_create"),
    path("orders/<str:order_id>/", order_detail, name="order_detail"),  # opcional
]
