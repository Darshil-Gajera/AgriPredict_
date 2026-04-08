from django.urls import path
from .views import save_prediction

app_name = "accounts_api"  # ✅ unique namespace

urlpatterns = [
    path("save/", save_prediction, name="save_prediction"),
]