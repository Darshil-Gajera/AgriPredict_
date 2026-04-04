from django.db import models
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields


class Scholarship(TranslatableModel):
    # Translatable fields are stored in a separate table automatically
    translations = TranslatedFields(
        name=models.CharField(_("Name"), max_length=200),
        eligible_courses=models.TextField(_("Eligible Courses"), blank=True),
        eligibility_criteria=models.TextField(_("Eligibility Criteria")),
        benefits=models.TextField(_("Benefits")),
        how_to_apply=models.TextField(_("How to Apply"), blank=True),
        notes=models.CharField(_("Notes"), max_length=300, blank=True),
    )
    
    # Common fields across all languages
    apply_url = models.URLField(blank=True)
    student_categories = models.CharField(
        max_length=100, 
        blank=True,
        help_text=_("Comma-separated: OPEN, SC, ST, SEBC, EWS, GIRL, MINORITY"),
    )
    min_percentage = models.FloatField(null=True, blank=True, help_text=_("Min 12th percentage"))
    max_income_lakh = models.FloatField(null=True, blank=True, help_text=_("Max family income in lakhs"))
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "pk"]
        verbose_name = _("scholarship")
        verbose_name_plural = _("scholarships")

    def __str__(self):
        # Fallback to ID if translation doesn't exist yet
        return self.safe_translation_getter("name", any_language=True) or f"Scholarship {self.pk}"