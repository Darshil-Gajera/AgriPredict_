from django.contrib import admin
from parler.admin import TranslatableAdmin
from .models import Notification, AdmissionDate


@admin.register(Notification)
class NotificationAdmin(TranslatableAdmin):
    list_display = ["get_title", "published_date", "is_active", "is_important"]
    list_filter = ["is_active", "is_important"]
    list_editable = ["is_active", "is_important"]
    date_hierarchy = "published_date"

    def get_title(self, obj):
        return obj.safe_translation_getter("title", any_language=True)
    get_title.short_description = "Title"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.is_important:
            from core.tasks import send_admission_alert_sms
            send_admission_alert_sms.delay(obj.pk)


@admin.register(AdmissionDate)
class AdmissionDateAdmin(admin.ModelAdmin):
    list_display = ["title", "event_type", "start_date", "end_date", "year", "is_active"]
    list_filter = ["year", "event_type", "is_active"]
    list_editable = ["is_active"]
