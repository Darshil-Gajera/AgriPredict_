from django.conf import settings


def global_context(request):
    """Inject variables available in every template."""
    return {
        "CHATBOT_ENABLED": bool(settings.CHATBOT_API_URL),
        "SITE_NAME": "AgriPredict",
    }
