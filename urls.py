from django.contrib import admin
from django.urls import path
from Orders.views import home  # ajusta si tu vista se llama distinto

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
]
