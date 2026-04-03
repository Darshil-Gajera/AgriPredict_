from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Extended user — stores admission-related profile data."""

    username = None  # use email as the unique identifier
    email = models.EmailField(_("email address"), unique=True)
    phone = models.CharField(_("phone number"), max_length=15, blank=True)
    preferred_language = models.CharField(
        max_length=5,
        choices=[("en", "English"), ("gu", "ગુજરાતી")],
        default="en",
    )
    # Notification preferences
    notify_email = models.BooleanField(default=True)
    notify_sms = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
        return self.email


class SavedResult(models.Model):
    """A merit calculation result saved by the user."""

    CATEGORY_CHOICES = [("1", "Core Agriculture"), ("2", "Technical"), ("3", "Home & Community")]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_results")
    category = models.CharField(max_length=1, choices=CATEGORY_CHOICES)
    theory_marks = models.FloatField()
    theory_total = models.IntegerField()
    gujcet_marks = models.FloatField()
    student_category = models.CharField(max_length=20)
    merit_score = models.FloatField()
    farming_bonus = models.BooleanField(default=False)
    subject_group = models.CharField(max_length=10, blank=True)  # PCM / PCB for cat 2
    city = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    label = models.CharField(max_length=120, blank=True, help_text="Optional user note")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("saved result")

    def __str__(self):
        return f"{self.user.email} | Cat {self.category} | Merit {self.merit_score}"
