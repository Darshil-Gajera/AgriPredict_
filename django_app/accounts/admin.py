from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, SavedResult

# --- CUSTOM USER ADMIN ---
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["email"]
    list_display = ["email", "first_name", "last_name", "preferred_language", "is_staff"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "phone")}),
        (_("Preferences"), {"fields": ("preferred_language", "notify_email", "notify_sms")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2"),
        }),
    )

    search_fields = ["email", "first_name", "last_name"]


# --- SAVED RESULTS ADMIN (ADD THIS) ---
@admin.register(SavedResult)
class SavedResultAdmin(admin.ModelAdmin):
    # Display these columns in the list view
    list_display = (
        "user", 
        "category", 
        "merit_score", 
        "student_category", 
        "farming_bonus",
        "created_at"
    )
    
    # Sidebar filters for quick navigation
    list_filter = (
        "category", 
        "student_category", 
        "farming_bonus", 
        "created_at"
    )
    
    # Search functionality (searching user email via foreign key)
    search_fields = ("user__email", "city", "district", "label")
    
    # Organize the detail view into logical sections
    fieldsets = (
        (_("User Details"), {
            "fields": ("user", "label", "category")
        }),
        (_("Merit Calculation Data"), {
            "fields": ("theory_marks", "theory_total", "gujcet_marks", "merit_score", "farming_bonus")
        }),
        (_("Admission Context"), {
            "fields": ("student_category", "subject_group", "city", "district")
        }),
        (_("Metadata"), {
            "fields": ("created_at",),
            "classes": ("collapse",)  # Hidden by default to keep it clean
        }),
    )
    
    # Prevent editing of the creation timestamp
    readonly_fields = ("created_at",)

    # Optimization: Speed up the user dropdown if you have many users
    raw_id_fields = ("user",)