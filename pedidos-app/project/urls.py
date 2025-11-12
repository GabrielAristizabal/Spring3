from django.contrib import admin
from django.urls import path
from orders.views import (
    home, order_list, order_detail, order_create, order_update, order_delete,
    register_user, verify
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="create_order", permanent=False), name="home"),
    path("orders/", order_list, name="order_list"),
    path("orders/create/", order_create, name="order_create"),
    path("orders/<str:order_id>/", order_detail, name="order_detail"),
    path("orders/<str:order_id>/edit/", order_update, name="order_update"),
    path("orders/<str:order_id>/delete/", order_delete, name="order_delete"),
    path("users/register/", register_user, name="register_user"),
    path("verify/", verify, name="verify"),
]
