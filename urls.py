from django.contrib import admin
from django.urls import path
from orders.views import home  # importa la vista directamente

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),   # home en la raíz
    # path("order/create/", create_order, name="order_create"),
]