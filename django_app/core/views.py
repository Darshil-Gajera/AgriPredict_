import json
import logging
import os
import httpx

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _, get_language
from django.conf import settings
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


def _load_faqs(lang="en"):
    fixture_path = os.path.join(settings.BASE_DIR, "core", "fixtures", "faq.json")
    try:
        with open(fixture_path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        key_q = "q_gu" if lang == "gu" else "q"
        key_a = "a_gu" if lang == "gu" else "a"

        return [
            {
                "q": item.get(key_q, item.get("q", "")),
                "a": item.get(key_a, item.get("a", "")),
            }
            for item in raw
        ]
    except Exception as e:
        logger.error(f"FAQ loading error: {e}")
        return []


def home(request):
    from notifications.models import Notification, AdmissionDate

    important_notifications = Notification.objects.filter(is_active=True, is_important=True)[:3]
    upcoming_dates = AdmissionDate.objects.filter(is_active=True).order_by("start_date")[:5]

    return render(request, "core/home.html", {
        "important_notifications": important_notifications,
        "upcoming_dates": upcoming_dates,
    })


def faq(request):
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
    """Forward chat request to FastAPI"""
    try:
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        payload.setdefault("lang", get_language())

        if request.user.is_authenticated:
            payload.setdefault("student_category", request.session.get("student_category"))
            payload.setdefault("user_merit", request.session.get("last_merit"))
            payload.setdefault("user_category", request.session.get("last_category"))

        logger.info(f"Sending to chatbot: {payload}")

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{settings.CHATBOT_API_URL}/chat",  # ✅ FIXED (no trailing slash issue)
                json=payload,
            )

        logger.info(f"Chatbot response: {resp.text}")

        return JsonResponse(resp.json(), status=resp.status_code)

    except Exception as e:
        logger.warning(f"Chatbot proxy error: {e}")

        return JsonResponse({
            "answer": _("Chatbot is temporarily unavailable. Please try again later."),
            "sources": []
        }, status=200)