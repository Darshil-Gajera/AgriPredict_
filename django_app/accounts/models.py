#save
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None  # ❌ REMOVE USERNAME
    email = models.EmailField(_("email address"), unique=True)

    # Optional fields
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(_("phone number"), max_length=15, blank=True)

    preferred_language = models.CharField(
        max_length=5,
        choices=[("en", "English"), ("gu", "ગુજરાતી")],
        default="en",
    )

    notify_email = models.BooleanField(default=True)
    notify_sms = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


from django.db import models
from django.conf import settings # Best practice: reference User via settings

class SavedResult(models.Model):
    CATEGORY_CHOICES = [
        ("1", "Core Agriculture"),
        ("2", "Technical"),
        ("3", "Home & Community"),
    ]

    # Use choices for student categories to match your predictor logic
    STUDENT_CAT_CHOICES = [
        ('OPEN', 'General / Open'),
        ('SEBC', 'SEBC'),
        ('SC', 'SC'),
        ('ST', 'ST'),
        ('EWS', 'EWS'),
        ('OB', 'Other Board'),
        ('PH', 'PH-VH'),
        ('EX', 'Ex-Serviceman'),
    ]

    # Relationships
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="saved_results"
    )

    # Basic Info
    category = models.CharField(
        max_length=1,
        choices=CATEGORY_CHOICES,
        default="1"
    )
    label = models.CharField(max_length=120, blank=True, help_text="Custom name for this result")

    # Score Data - Using DecimalField for precision (prevents 85.000000002 errors)
    theory_marks = models.DecimalField(max_digits=6, decimal_places=2)
    theory_total = models.PositiveIntegerField(default=300)
    gujcet_marks = models.DecimalField(max_digits=5, decimal_places=2)
    merit_score = models.DecimalField(max_digits=7, decimal_places=4)
    
    # Selection Data
    student_category = models.CharField(
        max_length=10, 
        choices=STUDENT_CAT_CHOICES, 
        default='OPEN'
    )
    farming_bonus = models.BooleanField(default=False)
    subject_group = models.CharField(max_length=10, blank=True)
    # Location Info
    city = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Saved Prediction"
        verbose_name_plural = "Saved Predictions"

    def __str__(self):
        # Using .format or f-string for a clean admin display
        return f"{self.user.email} | {self.get_category_display()} | Merit: {self.merit_score}"