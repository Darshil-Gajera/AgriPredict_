from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from parler.admin import TranslatableAdmin, TranslatableTabularInline
from .models import University, College, Course, CutoffMerit

@admin.register(University)
class UniversityAdmin(TranslatableAdmin):
    list_display = ["get_short_name", "website"]

    def get_short_name(self, obj):
        return obj.safe_translation_getter("short_name", any_language=True) or "—"
    get_short_name.short_description = _("Short name")

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('translations')


class CourseInline(TranslatableTabularInline):
    model = Course
    extra = 1
    readonly_fields = ["get_course_id"]

    def get_course_id(self, obj):
        return obj.id if obj else _("New")
    get_course_id.short_description = _("ID")


@admin.register(College)
class CollegeAdmin(TranslatableAdmin):
    list_display = ["code", "get_name", "university", "category", "is_active"]
    list_filter = ["university", "category", "is_active"]
    # district is now searchable via the translations table
    search_fields = ["code", "translations__name", "translations__district"] 
    inlines = [CourseInline]

    def get_name(self, obj):
        return obj.safe_translation_getter("name", any_language=True) or "—"
    get_name.short_description = _("Name")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('university').prefetch_related('translations', 'university__translations')


@admin.register(Course)
class CourseAdmin(TranslatableAdmin):
    list_display = ["get_name", "college"]
    list_filter = ["college__university"]
    search_fields = ["translations__name", "college__code"]

    def get_name(self, obj):
        return obj.safe_translation_getter("name", any_language=True) or "—"
    get_name.short_description = _("Course Name")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('college').prefetch_related('translations', 'college__translations')


@admin.register(CutoffMerit)
class CutoffMeritAdmin(admin.ModelAdmin):
    list_display = ["course", "year", "round_no", "student_category", "last_merit"]
    list_filter = ["year", "round_no", "student_category", "course__college__university"]
    # Use translations__name for searching across the bridge to Parler
    search_fields = ["course__translations__name", "course__college__code"]
    list_editable = ["last_merit"]

    def get_queryset(self, request):
        # We prefetch the translations for the related course to avoid the DoesNotExist crash in the list view
        return super().get_queryset(request).select_related("course__college__university").prefetch_related("course__translations")