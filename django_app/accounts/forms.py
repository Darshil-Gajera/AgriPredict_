from django import forms
from .models import User, SavedResult


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "phone", "preferred_language", "notify_email", "notify_sms"]
        widgets = {
            "first_name":         forms.TextInput(attrs={"class": "form-control"}),
            "last_name":          forms.TextInput(attrs={"class": "form-control"}),
            "phone":              forms.TextInput(attrs={"class": "form-control"}),
            "preferred_language": forms.Select(attrs={"class": "form-select"}),
            "notify_email":       forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "notify_sms":         forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class SavedResultForm(forms.ModelForm):
    class Meta:
        model = SavedResult
        fields = [
            "label", "category", "theory_marks", "theory_total",
            "gujcet_marks", "student_category", "farming_bonus",
            "city", "district",
        ]
        widgets = {
            "label":            forms.TextInput(attrs={"class": "form-control",
                                                       "placeholder": "e.g. My Best Score"}),
            "category":         forms.Select(attrs={"class": "form-select"}),
            "theory_marks":     forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "theory_total":     forms.NumberInput(attrs={"class": "form-control"}),
            "gujcet_marks":     forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "student_category": forms.Select(attrs={"class": "form-select"}),
            "farming_bonus":    forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "city":             forms.TextInput(attrs={"class": "form-control"}),
            "district":         forms.TextInput(attrs={"class": "form-control"}),
        }   