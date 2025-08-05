from notifier.tasks import send_notification_task


def send_notification(user, subject, message):

    send_notification_task.delay(user.id, subject, message)
