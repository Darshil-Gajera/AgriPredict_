# ── PythonAnywhere WSGI config ────────────────────────────────
# Place this content in your PythonAnywhere WSGI configuration file:
# /var/www/gajera06_pythonanywhere_com_wsgi.py

import sys
import os

# Add project to sys.path
project_home = '/home/gajera06/agripredict/django_app'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set Django settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'agripredict.settings.prod'

# Load .env
from dotenv import load_dotenv
load_dotenv('/home/gajera06/agripredict/.env')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
