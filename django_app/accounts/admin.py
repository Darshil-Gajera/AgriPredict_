from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, SavedResult


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["email"]
    list_display = ["email", "first_name", "last_name", "preferred_language", "notify_email", "notify_sms", "is_staff"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "phone")}),
        (_("Preferences"), {"fields": ("preferred_language", "notify_email", "notify_sms")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )
    search_fields = ["email", "first_name", "last_name"]


@admin.register(SavedResult)
class SavedResultAdmin(admin.ModelAdmin):
    list_display = ["user", "category", "merit_score", "student_category", "created_at"]
    list_filter = ["category", "student_category"]
    search_fields = ["user__email"]
    readonly_fields = ["created_at"]
