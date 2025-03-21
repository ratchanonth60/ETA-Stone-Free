from django import forms
from django.utils.translation import gettext_lazy as _
from .models import UserAddress


class UserAddressForm(forms.ModelForm):
    # เปลี่ยน line4 เป็น city ในฟอร์ม
    city = forms.CharField(label=_("City"), max_length=255, required=False)

    class Meta:
        model = UserAddress
        fields = [
            "title",
            "first_name",
            "last_name",
            "phone_number",
            "line1",
            "line2",
            "line3",
            "line4",
            "city",  # ใช้ city แทน line4
            "state",
            "postcode",
            "country",
            "is_default_for_shipping",
            "is_default_for_billing",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # แมพ city ในฟอร์มไปที่ line4 ในโมเดล
        self.fields["city"].name = "line4"

    def clean(self):
        cleaned_data = super().clean()
        # แปลง city กลับไปเป็น line4 ใน cleaned_data
        if "city" in cleaned_data:
            cleaned_data["line4"] = cleaned_data.pop("city")
        return cleaned_data
