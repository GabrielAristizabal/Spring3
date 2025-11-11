# urls.py (en la raíz, junto a manage.py)
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth.views import LogoutView

# Vistas de tu app
from orders.views import home, create_order, approve_order  # agrega update_order si la tienes
from orders.health import health_liveness, health_readiness

# Atajo para iniciar login con Auth0 (social-auth)
def auth0_login(request):
    return redirect('social:begin', backend='auth0')

urlpatterns = [
    path("admin/", admin.site.urls),

    # Pedidos
    path("", home, name="home"),
    path("order/create/", create_order, name="order_create"),
    path("order/<str:order_id>/approve/", approve_order, name="order_approve"),
    # path("order/<str:order_id>/update/", update_order, name="order_update"),  # descomenta si existe

    # Health checks
    path("health/liveness", health_liveness, name="health_liveness"),
    path("health/readiness", health_readiness, name="health_readiness"),

    # Auth0 (social-auth)
    path("auth/", include("social_django.urls", namespace="social")),
    path("login/auth0", auth0_login, name="login_auth0"),
    path("logout/", LogoutView.as_view(next_page="/"), name="logout"),
]
