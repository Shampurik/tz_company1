import logging
import random
import time

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from marketing.models import MailingMessage

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_mailing_message(self, message_id: int) -> None:
    try:
        mailing_message = MailingMessage.objects.get(pk=message_id)
    except MailingMessage.DoesNotExist:
        logger.warning("Mailing message %s does not exist.", message_id)
        return

    try:
        delay_seconds = random.randint(
            settings.MARKETING_EMAIL_SEND_DELAY_MIN_SECONDS,
            settings.MARKETING_EMAIL_SEND_DELAY_MAX_SECONDS,
        )
        logger.info(
            "Simulating email service delay for mailing message %s: %s seconds.",
            mailing_message.id,
            delay_seconds,
        )
        time.sleep(delay_seconds)
        logger.info(
            "Delayed email to %s for user_id=%s. Subject: %s. Message: %s",
            mailing_message.email,
            mailing_message.user_id,
            mailing_message.subject,
            mailing_message.message,
        )
        mailing_message.status = MailingMessage.Status.SENT
        mailing_message.sent_at = timezone.now()
        mailing_message.error_message = ""
        mailing_message.save(update_fields=["status", "sent_at", "error_message", "updated_at"])
    except Exception as exc:
        mailing_message.status = MailingMessage.Status.FAILED
        mailing_message.error_message = str(exc)
        mailing_message.save(update_fields=["status", "error_message", "updated_at"])
        raise self.retry(exc=exc) from exc
