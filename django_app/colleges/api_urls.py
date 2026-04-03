from django.urls import path
from .api_views import CollegeListAPIView, CutoffAPIView

urlpatterns = [
    path("", CollegeListAPIView.as_view(), name="api_college_list"),
    path("cutoffs/", CutoffAPIView.as_view(), name="api_cutoffs"),
]
