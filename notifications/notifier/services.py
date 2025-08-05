import logging
from abc import ABC, abstractmethod
import requests

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from telegram import Bot
from telegram.error import TelegramError

from django.conf import settings

from notifier.models import NotificationPreference


logger = logging.getLogger(__name__)


class DeliveryError(Exception):

    def __init__(self, channel, reason):
        self.channel = channel
        self.reason = reason
        super().__init__(f"{channel} delivery failed: {reason}")


class BaseNotifier(ABC):
    CHANNEL_NAME = None

    @abstractmethod
    def send(self, target, subject, message):
        pass


class EmailNotifier(BaseNotifier):
    CHANNEL_NAME = 'email'

    def send(self, target, subject, message):

        # pref = NotificationPreference.objects.get(user=user)
        # if not (pref.email and pref.email_verified):
        #     raise DeliveryError("Email not configured")

        try:

            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            mail = Mail(
                from_email=settings.DEFAULT_FROM_EMAIL,
                to_emails=target,
                subject=subject,
                plain_text_content=message)
            response = sg.send(mail)

            logger.info(f"Email sent to {target}")
            return True

        except Exception as e:
            logger.error(f"Email delivery failed: {e}")
            raise DeliveryError(self.CHANNEL_NAME, str(e))


class SMSNotifier(BaseNotifier):
    CHANNEL_NAME = 'sms'

    def send(self, target, subject, message):

        # pref = NotificationPreference.objects.get(user=user)
        # if not (pref.phone and pref.phone_verified):
        #     raise DeliveryError("SMS not configured")

        try:
            payload = {
                'login': settings.SMSC_LOGIN,
                'psw': settings.SMSC_PASSWORD,
                'phones': target,
                'mes': message,
                'sender': settings.SMSC_SENDER,
                'fmt': 3
            }
            response = requests.get('https://smsc.ru/sys/send.php', params=payload, timeout=10)
            response_data = response.json()

            if 'error_code' in response_data:
                raise Exception(f"SMS Center error: {response_data.get('error')}")

            logger.info(f"SMS sent to {target}")
            return True

        except Exception as e:
            logger.error(f"SMS delivery failed: {e}")
            raise DeliveryError(self.CHANNEL_NAME, str(e))


class TelegramNotifier(BaseNotifier):
    CHANNEL_NAME = 'telegram'

    def send(self, target, subject, message):

        # pref = NotificationPreference.objects.get(user=user)
        # if not (pref.telegram_id and pref.telegram_verified):
        #     raise DeliveryError("Telegram not configured")

        try:
            bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
            full_message = f"*{subject}*\n\n{message}"
            bot.send_message(
                chat_id=target,
                text=full_message,
            )
            logger.info(f"Telegram sent to {target}")
            return True

        except TelegramError as e:
            logger.error(f"Telegram delivery failed: {e}")
            raise DeliveryError(self.CHANNEL_NAME, str(e))


class NotificationService:
    NOTIFIERS = {
            'email': EmailNotifier(),
            'sms': SMSNotifier(),
            'telegram': TelegramNotifier(),
        }

    def __init__(self, user):

        self.user = user

        try:
            self.preferences = NotificationPreference.objects.select_related('user').get(user=user)

        except NotificationPreference.DoesNotExist:
            logger.error(f"Notification preferences missing for user {user.id}")
            self.preferences = None


    def send(self, subject, message):

        if not self.preferences:
            return False

        priority_order = self.preferences.priority or ['email', 'sms', 'telegram']

        verified_channels = self.preferences.get_verified_channels()
        channels_to_try = [
            ch for ch in priority_order if ch in verified_channels
        ]

        for channel in channels_to_try:
            notifier = self.NOTIFIERS.get(channel)
            if not notifier:
                continue

            try:
                target = getattr(self.preferences, {
                    'email': 'email',
                    'sms': 'phone',
                    'telegram': 'telegram_id'
                }[channel])

                if notifier.send(target, subject, message):
                    logger.info(f"Notification delivered via {channel}")
                    return True

            except DeliveryError as e:
                last_error = e
                logger.warning(f"Channel {channel} failed: {str(e)}")
                continue

        logger.error(f"All delivery channels failed for user {self.user.id}")
        return False
