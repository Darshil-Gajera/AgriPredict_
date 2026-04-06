from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("faq/", views.faq, name="faq"),
    path("contact/", views.contact, name="contact"),
    path("admission-guide/", views.admission_guide, name="admission_guide"),

    # ❌ REMOVE api/chat from here (important)
]