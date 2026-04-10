from django import forms
from .models import User, SavedResult


# ───────────────── PROFILE FORM ─────────────────
class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "phone",
            "preferred_language",
            "notify_email",
            "notify_sms",
        ]

        widgets = {
            "first_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "First Name"
            }),
            "last_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Last Name"
            }),
            "phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Phone Number"
            }),
            "preferred_language": forms.Select(attrs={
                "class": "form-select"
            }),
            "notify_email": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
            "notify_sms": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }

    # ✅ Validation example
    def clean_phone(self):
        phone = self.cleaned_data.get("phone")

        if phone and not phone.isdigit():
            raise forms.ValidationError("Phone number must contain only digits.")

        if phone and len(phone) < 10:
            raise forms.ValidationError("Phone number must be at least 10 digits.")

        return phone


# ───────────────── SAVED RESULT FORM ─────────────────
class SavedResultForm(forms.ModelForm):
    class Meta:
        model = SavedResult
        fields = [
            "label",
            "category",
            "theory_marks",
            "theory_total",
            "gujcet_marks",
            "student_category",
            "farming_bonus",
            "city",
            "district",
        ]

        widgets = {
            "label": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. My Best Score"
            }),
            "category": forms.Select(attrs={"class": "form-select"}),

            "theory_marks": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0"
            }),
            "theory_total": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "1"
            }),
            "gujcet_marks": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
                "max": "120"
            }),

            "student_category": forms.Select(attrs={"class": "form-select"}),

            "farming_bonus": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),

            "city": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "City"
            }),
            "district": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "District"
            }),
        }

    # ✅ Custom validation (IMPORTANT)
    def clean(self):
        cleaned_data = super().clean()

        theory = cleaned_data.get("theory_marks")
        total = cleaned_data.get("theory_total")

        if theory and total and theory > total:
            self.add_error("theory_marks", "Obtained marks cannot exceed total marks.")

        return cleaned_data