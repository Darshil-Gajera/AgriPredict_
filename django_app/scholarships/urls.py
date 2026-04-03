from django.urls import path
from . import views

app_name = "scholarships"

urlpatterns = [
    path("", views.scholarship_list, name="list"),
]
