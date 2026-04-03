from django.contrib import admin
from parler.admin import TranslatableAdmin
from .models import University, College, Course, CutoffMerit


@admin.register(University)
class UniversityAdmin(TranslatableAdmin):
    list_display = ["get_short_name", "website"]

    def get_short_name(self, obj):
        return obj.safe_translation_getter("short_name", any_language=True)
    get_short_name.short_description = "Short name"


class CourseInline(admin.TabularInline):
    model = Course
    extra = 1


@admin.register(College)
class CollegeAdmin(TranslatableAdmin):
    list_display = ["code", "get_name", "university", "category", "is_active"]
    list_filter = ["university", "category", "is_active"]
    search_fields = ["code", "translations__name"]
    inlines = [CourseInline]

    def get_name(self, obj):
        return obj.safe_translation_getter("name", any_language=True)
    get_name.short_description = "Name"


@admin.register(CutoffMerit)
class CutoffMeritAdmin(admin.ModelAdmin):
    list_display = ["course", "year", "round_no", "student_category", "last_merit"]
    list_filter = ["year", "round_no", "student_category", "course__college__university"]
    search_fields = ["course__translations__name", "course__college__code"]
    list_editable = ["last_merit"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("course__college__university")
