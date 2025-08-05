from django.db import models


from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class NotificationPreference(models.Model):
    # Порядок приоритета каналов доставки
    PRIORITY_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('telegram', 'Telegram'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notify_prefs')
    email = models.EmailField(blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    phone = models.CharField(max_length=20, blank=True, null=True)
    phone_verified = models.BooleanField(default=False)
    telegram_id = models.CharField(max_length=100, blank=True, null=True)
    telegram_verified = models.BooleanField(default=False)
    priority = models.JSONField(default=list, help_text="Порядок каналов для попытки доставки")

    def get_verified_channels(self):

        channels = []
        if self.email_verified: channels.append('email')
        if self.phone_verified: channels.append('sms')
        if self.telegram_verified: channels.append('telegram')
