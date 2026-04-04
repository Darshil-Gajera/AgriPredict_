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


class SavedResult(models.Model):
    CATEGORY_CHOICES = [
        ("1", "Core Agriculture"),
        ("2", "Technical"),
        ("3", "Home & Community"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_results")
    category = models.CharField(
    max_length=1,
    choices=CATEGORY_CHOICES,
    default="1"   # ✅ prevents future issues
)
    theory_marks = models.FloatField()
    theory_total = models.IntegerField()
    gujcet_marks = models.FloatField()
    student_category = models.CharField(max_length=20)
    merit_score = models.FloatField()
    farming_bonus = models.BooleanField(default=False)
    subject_group = models.CharField(max_length=10, blank=True)
    city = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    label = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} | Cat {self.category} | Merit {self.merit_score}"