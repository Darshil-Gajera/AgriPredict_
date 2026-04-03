from django.db import models
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields


class Scholarship(TranslatableModel):
    translations = TranslatedFields(
        name=models.CharField(max_length=200),
        eligible_courses=models.TextField(blank=True),
        eligibility_criteria=models.TextField(),
        benefits=models.TextField(),
        how_to_apply=models.TextField(blank=True),
        notes=models.CharField(max_length=300, blank=True),
    )
    apply_url = models.URLField(blank=True)
    student_categories = models.CharField(
        max_length=100, blank=True,
        help_text="Comma-separated: OPEN, SC, ST, SEBC, EWS, GIRL, MINORITY",
    )
    min_percentage = models.FloatField(null=True, blank=True, help_text="Min 12th percentage")
    max_income_lakh = models.FloatField(null=True, blank=True, help_text="Max family income in lakhs")
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "pk"]
        verbose_name = _("scholarship")

    def __str__(self):
        return self.safe_translation_getter("name", any_language=True) or f"Scholarship {self.pk}"
