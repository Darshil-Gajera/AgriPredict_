from django.db import models
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields
from googletrans import Translator  # pip install googletrans==4.0.0-rc1

def auto_translate_fields(instance, fields):
    """
    Helper function to translate English fields to Gujarati.
    Only triggers if the Gujarati ('gu') translation doesn't exist.
    """
    if not instance.has_translation('gu'):
        translator = Translator()
        
        # 1. Capture original English values safely
        translation_data = {}
        for field in fields:
            # Get value specifically from English context
            val = instance.safe_translation_getter(field, language_code='en')
            if val:
                try:
                    res = translator.translate(val, src='en', dest='gu')
                    translation_data[field] = res.text
                except Exception as e:
                    print(f"Translation failed for {field}: {e}")

        # 2. Create the Gujarati translation row directly
        if translation_data:
            try:
                instance.create_translation('gu', **translation_data)
                # create_translation automatically saves the new row to the DB
            except Exception as e:
                print(f"Failed to create 'gu' translation row: {e}")

class University(TranslatableModel):
    translations = TranslatedFields(
        name=models.CharField(_("University Name"), max_length=200),
        short_name=models.CharField(_("Short Name"), max_length=20),
    )
    website = models.URLField(_("Website"), blank=True)
    logo = models.ImageField(_("Logo"), upload_to="universities/", blank=True)

    class Meta:
        verbose_name = _("university")
        verbose_name_plural = _("universities")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        auto_translate_fields(self, ['name', 'short_name'])

    def __str__(self):
        return self.safe_translation_getter("short_name", any_language=True) or "University"


class College(TranslatableModel):
    CATEGORY_CHOICES = [
        ("1", _("Core Agriculture")),
        ("2", _("Technical Agriculture")),
        ("3", _("Home & Community Science")),
    ]

    translations = TranslatedFields(
        name=models.CharField(_("College Name"), max_length=300),
        city=models.CharField(_("City"), max_length=100),
        # district remains optional as requested
        district=models.CharField(_("District"), max_length=100, null=True, blank=True),
    )
    code = models.CharField(_("College Code"), max_length=10, unique=True, db_index=True)
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name="colleges")
    category = models.CharField(_("Category"), max_length=1, choices=CATEGORY_CHOICES)
    brochure = models.FileField(_("Brochure PDF"), upload_to="brochures/", blank=True)
    is_active = models.BooleanField(_("Is Active"), default=True)

    class Meta:
        verbose_name = _("college")
        verbose_name_plural = _("colleges")
        ordering = ["code"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        auto_translate_fields(self, ['name', 'city', 'district'])

    def __str__(self):
        name = self.safe_translation_getter('name', any_language=True)
        return f"[{self.code}] {name}"


class Course(TranslatableModel):
    translations = TranslatedFields(
        name=models.CharField(_("Course Name"), max_length=200),
    )
    code = models.CharField(_("Course Code"), max_length=20, unique=True)
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name="courses")
    
    # Seats
    seats_general = models.PositiveIntegerField(_("General Seats"), default=0)
    seats_sebc = models.PositiveIntegerField(_("SEBC Seats"), default=0)
    seats_sc = models.PositiveIntegerField(_("SC Seats"), default=0)
    seats_st = models.PositiveIntegerField(_("ST Seats"), default=0)
    seats_ews = models.PositiveIntegerField(_("EWS Seats"), default=0)

    class Meta:
        verbose_name = _("course")
        verbose_name_plural = _("courses")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        auto_translate_fields(self, ['name'])

    def __str__(self):
        name = self.safe_translation_getter('name', any_language=True)
        return f"{name} @ {self.college.code}"


class CutoffMerit(models.Model):
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
    year = models.PositiveSmallIntegerField(_("Year"))
    round_no = models.CharField(_("Round"), max_length=1, choices=ROUND_CHOICES)
    student_category = models.CharField(_("Student Category"), max_length=6, choices=STUDENT_CATEGORY_CHOICES)
    last_merit = models.FloatField(_("Closing Merit Score"))
    first_merit = models.FloatField(_("Opening Merit Score"), null=True, blank=True)
    total_admitted = models.PositiveIntegerField(_("Total Admitted"), null=True, blank=True)

    class Meta:
        unique_together = ["course", "year", "round_no", "student_category"]
        verbose_name = _("cutoff merit")
        verbose_name_plural = _("cutoff merits")
        ordering = ["-year", "course", "round_no"]

    def __str__(self):
        return f"{self.course.code} | {self.year} R{self.round_no} | {self.student_category}: {self.last_merit}"