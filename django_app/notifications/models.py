from django.db import models
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields
# Import the auto_translate_fields from your colleges.models or common utils
from colleges.models import auto_translate_fields 

class Notification(TranslatableModel):
    """Official admission notification with optional PDF attachment."""

    translations = TranslatedFields(
        title=models.CharField(max_length=400),
        summary=models.TextField(blank=True),
    )
    pdf = models.FileField(upload_to="notifications/pdfs/", blank=True)
    external_url = models.URLField(blank=True)
    published_date = models.DateField()
    is_active = models.BooleanField(default=True)
    is_important = models.BooleanField(default=False, help_text="Show highlighted on homepage")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published_date"]
        verbose_name = _("notification")
        verbose_name_plural = _("notifications")

    def save(self, *args, **kwargs):
        # Save the main record first
        super().save(*args, **kwargs)
        # Generate Gujarati translation automatically if it's missing
        auto_translate_fields(self, ['title', 'summary'])

    def __str__(self):
        # Parler helper to get title in any available language
        return self.safe_translation_getter("title", any_language=True) or f"Notification {self.pk}"


class AdmissionDate(models.Model):
    """Key dates in the admission calendar shown as a timeline."""

    EVENT_TYPES = [
        ("form", _("Form Submission")),
        ("merit", _("Merit List")),
        ("round", _("Admission Round")),
        ("fee", _("Fee Payment")),
        ("other", _("Other")),
    ]

    title = models.CharField(max_length=200) # English only, or consider TranslatableModel
    event_type = models.CharField(max_length=10, choices=EVENT_TYPES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    year = models.PositiveSmallIntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["start_date"]
        verbose_name = _("admission date")

    def __str__(self):
        return f"{self.title} ({self.year})"