from django import forms
from datetime import date

class OrderForm(forms.Form):
    cliente = forms.CharField(max_length=120)
    documento = forms.CharField(max_length=40)
    fecha = forms.DateField(initial=date.today, widget=forms.DateInput(attrs={"type": "date"}))

    # Para demo: 3 renglones
    item1_nombre = forms.CharField(max_length=64, required=False, label="Item 1")
    item1_qty    = forms.IntegerField(min_value=1, required=False, label="Cant 1")
    item2_nombre = forms.CharField(max_length=64, required=False, label="Item 2")
    item2_qty    = forms.IntegerField(min_value=1, required=False, label="Cant 2")
    item3_nombre = forms.CharField(max_length=64, required=False, label="Item 3")
    item3_qty    = forms.IntegerField(min_value=1, required=False, label="Cant 3")

    def cleaned_items_list(self):
        items = []
        for i in (1, 2, 3):
            nombre = self.cleaned_data.get(f"item{i}_nombre")
            qty    = self.cleaned_data.get(f"item{i}_qty")
            if nombre and qty:
                items.append({"nombre": nombre.strip(), "qty": int(qty)})
        return items

    def cleaned_items_dict(self):
        """Devuelve {nombre: qty} como lo pide el documento en Mongo."""
        result = {}
        for it in self.cleaned_items_list():
            result[it["nombre"]] = it["qty"]
        return result
