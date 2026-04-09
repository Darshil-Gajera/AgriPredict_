# agripredict/settings/dev.py
from .base import *  # noqa
import os

DEBUG = True
ALLOWED_HOSTS = ["*"]

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'agripredict', 'static'),
]

CHATBOT_API_URL = os.getenv("CHATBOT_API_URL", "http://chatbot:8001")