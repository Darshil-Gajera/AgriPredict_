from django.urls import path
from . import views

urlpatterns = [
    path("", views.chat_proxy, name="chat_proxy"),
]