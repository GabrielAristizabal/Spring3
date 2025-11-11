from django import forms

class OrderForm(forms.Form):
    cliente   = forms.CharField(max_length=100)
    documento = forms.CharField(max_length=30)
    fecha     = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    items     = forms.CharField(widget=forms.Textarea, help_text='JSON como {"Arroz":2,"Azúcar":1}')

class RegisterUserForm(forms.Form):
    username   = forms.CharField(max_length=50)
    email      = forms.EmailField()
    passphrase = forms.CharField(required=False, widget=forms.PasswordInput, help_text="Opcional para proteger la privada en PEM")

class VerifyForm(forms.Form):
    order_id = forms.CharField(label="ID del pedido")
