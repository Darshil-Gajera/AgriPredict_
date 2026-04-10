# agripredict/settings/dev.py
from .base import *  # noqa
import os

DEBUG = True
ALLOWED_HOSTS = ["*"]

CHATBOT_API_URL = os.getenv("CHATBOT_API_URL", "http://chatbot:8001")
EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"