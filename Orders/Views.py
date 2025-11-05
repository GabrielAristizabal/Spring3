from django.shortcuts import render
from .forms import OrderForm
from .service import create_order_with_strict_stock

def home(request):
    ctx = {"ok": None, "message": None, "order": None}
    form = OrderForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        items = form.cleaned_items()
        order, err = create_order_with_strict_stock(items)
        if err:
            ctx.update(ok=False, message=err)
        else:
            ctx.update(ok=True, message="Pedido creado correctamente", order=order)
    ctx["form"] = form
    return render(request, "orders/home.html", ctx)
