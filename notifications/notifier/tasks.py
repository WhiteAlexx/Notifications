import logging

from celery import shared_task

from django.contrib.auth import get_user_model

from notifier.services import NotificationService


logger = logging.getLogger(__name__)

User = get_user_model()

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True
)
def send_notification_task(self, user_id, subject, message):

    try:
        user = User.objects.get(id=user_id)
        service = NotificationService(user)
        return service.send(subject, message)

    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")

    except Exception as e:
        self.retry(exc=e)
