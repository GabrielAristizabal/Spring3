from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("orders.urls")),   # ← envía todo a la app Orders
]
