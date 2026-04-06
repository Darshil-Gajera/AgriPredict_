from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("profile/", views.profile, name="profile"),
    path("saved/", views.saved_results, name="saved_results"),
    path("saved/<int:pk>/delete/", views.delete_saved_result, name="delete_result"),
    path("save-prediction/", views.save_prediction, name="save_prediction_api"),
]