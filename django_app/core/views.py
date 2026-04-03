import json
import logging
import os
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _, get_language # Added get_language
from django.conf import settings
from django.views.decorators.http import require_POST # Added for better security

logger = logging.getLogger(__name__)

def _load_faqs(lang="en"):
    """
    Load FAQs from the fixture file. 
    Corrected to handle language fallback more gracefully.
    """
    fixture_path = os.path.join(settings.BASE_DIR, "core", "fixtures", "faq.json")
    try:
        with open(fixture_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        
        # Determine keys based on language
        key_q = "q_gu" if lang == "gu" else "q"
        key_a = "a_gu" if lang == "gu" else "a"
        
        # Fallback to English if Gujarati keys are missing in specific items
        return [
            {
                "q": item.get(key_q, item.get("q", "")), 
                "a": item.get(key_a, item.get("a", ""))
            } for item in raw
        ]
    except Exception as e:
        logger.error(f"FAQ loading error: {e}")
        return []

def home(request):
    # Moved imports to the top if possible, but keeping them here if you prefer
    from notifications.models import Notification, AdmissionDate
    
    important_notifications = Notification.objects.filter(is_active=True, is_important=True)[:3]
    upcoming_dates = AdmissionDate.objects.filter(is_active=True).order_by("start_date")[:5]
    
    return render(request, "core/home.html", {
        "important_notifications": important_notifications,
        "upcoming_dates": upcoming_dates,
    })

def faq(request):
    # Use get_language() which is more reliable than checking request.LANGUAGE_CODE manually
    lang = get_language() or "en"
    faqs = _load_faqs(lang)
    return render(request, "core/faq.html", {"faq_list": faqs})

def contact(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        message_body = request.POST.get("message", "").strip()
        
        if name and email and message_body:
            from core.tasks import send_contact_email
            send_contact_email.delay(name, email, message_body)
            # Use _() for success messages so they translate in the template
            messages.success(request, _("Your message has been sent. We'll get back to you soon."))
        else:
            messages.error(request, _("Please fill in all fields."))
            
    return render(request, "core/contact.html")

def admission_guide(request):
    from notifications.models import AdmissionDate
    dates = AdmissionDate.objects.filter(is_active=True).order_by("start_date")
    return render(request, "core/admission_guide.html", {"dates": dates})

@require_POST
def chat_proxy(request):
    """Forward chat request to FastAPI chatbot service, injecting session context."""
    try:
        import httpx
        # Handle cases where request.body might be empty or invalid JSON
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        # Inject language into chatbot payload so AgriBot knows to reply in Gujarati
        payload.setdefault("lang", get_language())

        if request.user.is_authenticated:
            payload.setdefault("student_category", request.session.get("student_category"))
            payload.setdefault("user_merit", request.session.get("last_merit"))
            payload.setdefault("user_category", request.session.get("last_category"))

        # Using a context manager for httpx is better practice
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{settings.CHATBOT_API_URL}/chat/",
                json=payload,
            )
            return JsonResponse(resp.json(), status=resp.status_code)
            
    except Exception as e:
        logger.warning(f"Chatbot proxy error: {e}")
        # Translate the fallback error message as well
        return JsonResponse(
            {
                "answer": _("Chatbot is temporarily unavailable. Please try again later."), 
                "sources": []
            },
            status=200,
        )