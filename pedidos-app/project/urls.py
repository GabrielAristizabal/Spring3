# project/urls.py
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView

from orders.views import (
    register_user,
    set_signer,
    create_order,   # <-- esta sí existe
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="order_create", permanent=False), name="home"),
    path("users/register/", register_user, name="register_user"),
    path("firmante/usar/", set_signer, name="set_signer"),
    path("orders/create/", create_order, name="order_create"),
]
