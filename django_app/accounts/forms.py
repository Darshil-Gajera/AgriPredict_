from django.urls import path, include
from . import views

app_name = "accounts"

urlpatterns = [
    # Custom Profile and Dashboard Views
    path("profile/", views.profile, name="profile"),
    path("saved/", views.saved_results, name="saved_results"),
    path("saved/<int:pk>/delete/", views.delete_saved_result, name="delete_result"),
    
    # Inclusion of Django-allauth or standard auth
    # This provides 'account_login', 'account_logout', and 'account_signup'
    path("", include("allauth.urls")), 
]