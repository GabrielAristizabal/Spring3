from django.contrib import admin
from django.urls import path
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json

def home(request):
    return HttpResponse("Home OK")

@csrf_exempt
def create_order(request):
    if request.method == "GET":
        return HttpResponse("Endpoint /order/create/ listo (usa POST)")
    if request.method != "POST":
        return JsonResponse({"detail": "Solo POST"}, status=405)
    data = json.loads(request.body or "{}")
    return JsonResponse({"ok": True, "payload": data})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("order/create/", create_order, name="order_create"),
]