from django.contrib import admin
from django.urls import path

# --- Vista inline (no importa si orders es módulo o no) ---
from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    # Si ya tienes Templates/orders/home.html, úsalo:
    try:
        return render(request, "orders/home.html")
    except Exception:
        return HttpResponse("Home OK")  # fallback simple

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("order/create/", create_order, name="order_create"),  # <- NUEVA RUTA
]