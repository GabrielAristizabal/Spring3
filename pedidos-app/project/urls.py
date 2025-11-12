from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from orders.views import (
    create_order, register_user, set_signer,
    order_list, order_detail, order_update, order_delete, verify,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="order_create", permanent=False), name="home"),
    path("users/register/", register_user, name="register_user"),
    path("firmante/usar/", set_signer, name="set_signer"),
    path("orders/", order_list, name="order_list"),
    path("orders/create/", create_order, name="order_create"),
    path("orders/<str:order_id>/", order_detail, name="order_detail"),
    path("orders/<str:order_id>/edit/", order_update, name="order_update"),
    path("orders/<str:order_id>/delete/", order_delete, name="order_delete"),
    path("verify/", verify, name="verify"),
]
