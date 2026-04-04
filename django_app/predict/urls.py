from django.urls import path
from . import views

app_name = "predict"

urlpatterns = [
    path("category<int:category>/", views.category_view, name="category"),
    path("calculate/", views.calculate_view, name="calculate"),
    path("save/", views.save_result_view, name="save"),
]