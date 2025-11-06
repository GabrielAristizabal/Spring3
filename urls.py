from django.contrib import admin
from django.urls import path
from .views import home  # ajusta si tu vista se llama distinto

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("orders.urls")),   # ← envía todo a la app Order
]