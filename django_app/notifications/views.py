from django.shortcuts import render
from .models import Notification, AdmissionDate

def notification_list(request):
    # Parler will automatically filter and serve the correct language
    notifications = Notification.objects.filter(is_active=True).order_by("-published_date")
    dates = AdmissionDate.objects.filter(is_active=True).order_by("start_date")
    
    return render(request, "notifications/list.html", {
        "notifications": notifications,
        "dates": dates,
    })