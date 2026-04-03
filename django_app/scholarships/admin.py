from django.contrib import admin
from parler.admin import TranslatableAdmin
from .models import Scholarship


@admin.register(Scholarship)
class ScholarshipAdmin(TranslatableAdmin):
    list_display = ["get_name", "min_percentage", "max_income_lakh", "is_active", "display_order"]
    list_filter = ["is_active"]
    list_editable = ["is_active", "display_order"]

    def get_name(self, obj):
        return obj.safe_translation_getter("name", any_language=True)
    get_name.short_description = "Name"
