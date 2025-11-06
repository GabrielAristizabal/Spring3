from django.urls import path
from .views import home

app_name = "orders" #minuscula
urlpatterns = [
    path("", home, name="home"),  # "/" muestra el Home
]
