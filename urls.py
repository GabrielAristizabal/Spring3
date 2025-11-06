from django.contrib import admin
from django.urls import path
from django.http import HttpResponse

# Importar la vista desde orders.views que tiene la lógica completa con MongoDB
from orders.views import create_order

def home(request):
    return HttpResponse("Home OK")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("order/create/", create_order, name="order_create"),
]