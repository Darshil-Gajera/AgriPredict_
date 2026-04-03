from django import forms
from django.utils.translation import gettext_lazy as _
from .models import User


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone", "preferred_language", "notify_email", "notify_sms"]
        widgets = {
            "preferred_language": forms.Select(attrs={"class": "form-select"}),
        }
        labels = {
            "notify_email": _("Receive email notifications"),
            "notify_sms": _("Receive SMS notifications"),
        }
