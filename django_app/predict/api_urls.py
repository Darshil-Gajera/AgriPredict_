from django.urls import path
from .views import calculate_view, save_result_view

urlpatterns = [
    path("calculate/", calculate_view, name="api_calculate"),
    path("save/", save_result_view, name="api_save"),
]
