from django.urls import path
from . import views
from django.urls import path, include

app_name = "predict"

urlpatterns = [
    path("category<int:category>/", views.category_view, name="category"),
    path("calculate/", views.calculate_view, name="calculate"),
    path("save/", views.save_result_view, name="save"),
    path("api/predict/", include("predict.api_urls")), 
]