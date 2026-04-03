import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agripredict.settings.dev")

app = Celery("agripredict")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
