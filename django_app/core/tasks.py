import logging
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import translation

logger = logging.getLogger(__name__)


def _twilio():
    from twilio.rest import Client
    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_merit_result_email(self, user_id: int, merit_data: dict):
    from accounts.models import User
    try:
        user = User.objects.get(pk=user_id)
        if not user.notify_email:
            return
        lang = user.preferred_language or "en"
        with translation.override(lang):
            subject = "Your AgriPredict Merit Result" if lang == "en" else "તમારું AgriPredict Merit Result"
            ctx = {"user": user, **merit_data}
            html_body = render_to_string("emails/merit_result.html", ctx)
            text_body = render_to_string("emails/merit_result.txt", ctx)
        msg = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [user.email])
        msg.attach_alternative(html_body, "text/html")
        msg.send()
        logger.info(f"Merit email sent to {user.email}")
    except Exception as exc:
        logger.error(f"Merit email failed (user={user_id}): {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def send_admission_alert_sms(self, notification_id: int):
    from notifications.models import Notification
    from accounts.models import User
    try:
        notif = Notification.objects.get(pk=notification_id)
        phones = list(User.objects.filter(notify_sms=True).exclude(phone="").values_list("phone", flat=True))
        if not phones:
            return
        client = _twilio()
        title = notif.safe_translation_getter("title", any_language=True) or "New notification"
        body = f"AgriPredict: {title}\nDetails: agripredict.in/notifications/"
        sent = 0
        for phone in phones:
            try:
                to = f"+91{phone}" if not phone.startswith("+") else phone
                client.messages.create(body=body, from_=settings.TWILIO_PHONE_NUMBER, to=to)
                sent += 1
            except Exception as e:
                logger.warning(f"SMS failed for {phone}: {e}")
        logger.info(f"SMS sent to {sent}/{len(phones)} users.")
    except Exception as exc:
        logger.error(f"SMS task error: {exc}")
        raise self.retry(exc=exc)


@shared_task
def send_welcome_email(user_id: int):
    from accounts.models import User
    try:
        user = User.objects.get(pk=user_id)
        lang = user.preferred_language or "en"
        with translation.override(lang):
            subject = "Welcome to AgriPredict!" if lang == "en" else "AgriPredict માં આપનું સ્વાગત છે!"
            html_body = render_to_string("emails/welcome.html", {"user": user})
            text_body = render_to_string("emails/welcome.txt", {"user": user})
        msg = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [user.email])
        msg.attach_alternative(html_body, "text/html")
        msg.send()
    except Exception as e:
        logger.error(f"Welcome email failed (user={user_id}): {e}")


@shared_task
def send_contact_email(name: str, email: str, message_body: str):
    from django.core.mail import send_mail
    send_mail(
        subject=f"AgriPredict Contact: {name}",
        message=f"From: {name} <{email}>\n\n{message_body}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.DEFAULT_FROM_EMAIL],
        fail_silently=True,
    )
