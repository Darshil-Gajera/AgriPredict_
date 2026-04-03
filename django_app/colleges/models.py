from django.db import models
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields


class University(TranslatableModel):
    translations = TranslatedFields(
        name=models.CharField(max_length=200),
        short_name=models.CharField(max_length=20),
    )
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to="universities/", blank=True)

    class Meta:
        verbose_name = _("university")
        verbose_name_plural = _("universities")

    def __str__(self):
        return self.safe_translation_getter("short_name", any_language=True) or "University"


class College(TranslatableModel):
    CATEGORY_CHOICES = [
        ("1", _("Core Agriculture")),
        ("2", _("Technical Agriculture")),
        ("3", _("Home & Community Science")),
    ]

    translations = TranslatedFields(
        name=models.CharField(max_length=300),
        city=models.CharField(max_length=100),
        district=models.CharField(max_length=100),
    )
    code = models.CharField(max_length=10, unique=True, db_index=True)
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name="colleges")
    category = models.CharField(max_length=1, choices=CATEGORY_CHOICES)
    brochure = models.FileField(upload_to="brochures/", blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("college")
        verbose_name_plural = _("colleges")
        ordering = ["code"]

    def __str__(self):
        return f"[{self.code}] {self.safe_translation_getter('name', any_language=True)}"


class Course(TranslatableModel):
    translations = TranslatedFields(
        name=models.CharField(max_length=200),
    )
    code = models.CharField(max_length=20, unique=True)
    category = models.CharField(max_length=1, choices=College.CATEGORY_CHOICES)
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name="courses")
    seats_general = models.PositiveIntegerField(default=0)
    seats_sebc = models.PositiveIntegerField(default=0)
    seats_sc = models.PositiveIntegerField(default=0)
    seats_st = models.PositiveIntegerField(default=0)
    seats_ews = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _("course")

    def __str__(self):
        return f"{self.safe_translation_getter('name', any_language=True)} @ {self.college}"


class CutoffMerit(models.Model):
    """Historical cutoff data — one row per course × category × year × round."""

    ROUND_CHOICES = [("1", "Round 1"), ("2", "Round 2"), ("3", "Round 3"), ("M", "Mop-up")]
    STUDENT_CATEGORY_CHOICES = [
        ("OPEN", "Open / General"),
        ("SEBC", "SEBC"),
        ("SC", "SC"),
        ("ST", "ST"),
        ("EWS", "EWS"),
        ("PH", "PH-VH"),
        ("EX", "Ex-Serviceman"),
        ("OB", "Other Board"),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="cutoffs")
    year = models.PositiveSmallIntegerField()
    round_no = models.CharField(max_length=1, choices=ROUND_CHOICES)
    student_category = models.CharField(max_length=6, choices=STUDENT_CATEGORY_CHOICES)
    last_merit = models.FloatField(help_text="Last admitted merit score this round")
    first_merit = models.FloatField(null=True, blank=True)
    total_admitted = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ["course", "year", "round_no", "student_category"]
        verbose_name = _("cutoff merit")
        ordering = ["-year", "course", "round_no"]

    def __str__(self):
        return f"{self.course} | {self.year} R{self.round_no} | {self.student_category} | {self.last_merit}"
