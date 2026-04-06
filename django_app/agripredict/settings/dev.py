# agripredict/settings/dev.py
from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["*"]
# settings/dev.py
import os

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'agripredict', 'static'),  # ← your path
]

CHATBOT_API_URL = "http://127.0.0.1:8001"  # ← add this too