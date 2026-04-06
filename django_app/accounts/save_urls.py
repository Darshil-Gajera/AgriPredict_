from django.urls import path
from accounts import views

urlpatterns = [
    path("", views.save_prediction),
]