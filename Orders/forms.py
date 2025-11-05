from django import forms

class OrderForm(forms.Form):
    item1_sku = forms.CharField(max_length=64, required=False)
    item1_qty = forms.IntegerField(min_value=1, required=False)
    item2_sku = forms.CharField(max_length=64, required=False)
    item2_qty = forms.IntegerField(min_value=1, required=False)
    item3_sku = forms.CharField(max_length=64, required=False)
    item3_qty = forms.IntegerField(min_value=1, required=False)

    def cleaned_items(self):
        items = []
        for i in (1,2,3):
            sku = self.cleaned_data.get(f"item{i}_sku")
            qty = self.cleaned_data.get(f"item{i}_qty")
            if sku and qty:
                items.append({"sku": sku.strip(), "qty": int(qty)})
        return items
