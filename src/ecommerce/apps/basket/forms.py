from django import forms

from ecommerce.core.defults import STATUS_CHOICES_BASKET

from .models import Basket, Line, LineAttribute


class BasketForm(forms.ModelForm):
    class Meta:
        model = Basket
        fields = [
            "status",
            "vouchers",  # ManyToManyField
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ปรับแต่งฟอร์มถ้าต้องการ เช่น จำกัด choices ของ status
        self.fields["status"].choices = STATUS_CHOICES_BASKET


class LineForm(forms.ModelForm):
    class Meta:
        model = Line
        fields = [
            "basket",
            "product",
            "stockrecord",
            "quantity",
            "price_currency",
            "price_excl_tax",
            "price_incl_tax",
        ]


class LineAttributeForm(forms.ModelForm):
    class Meta:
        model = LineAttribute
        fields = [
            "line",
            "option",
            "value",
        ]
