from django.shortcuts import render
from .forms import OrderForm
from .service import create_order_with_strict_stock

def home(request):
    ctx = {"ok": None, "message": None, "order": None}
    form = OrderForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        items_list = form.cleaned_items_list()     # [{"nombre":..., "qty":...}]
        cliente    = form.cleaned_data["cliente"]
        documento  = form.cleaned_data["documento"]
        fecha      = form.cleaned_data["fecha"].isoformat()  # YYYY-MM-DD

        order, err = create_order_with_strict_stock(items_list, cliente, documento, fecha)
        if err:
            ctx.update(ok=False, message=err)
        else:
            ctx.update(ok=True, message="Pedido creado correctamente", order=order)

    ctx["form"] = form
    return render(request, "orders/home.html", ctx)
