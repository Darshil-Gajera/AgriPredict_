from django.urls import path
from . import views

app_name = "colleges"

urlpatterns = [
    path("", views.college_list, name="list"),
    path("<str:code>/", views.college_detail, name="detail"),
]
