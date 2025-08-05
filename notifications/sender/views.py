from notifier.utils import send_notification


def some_view(request):

    user = request.user
    subject = 'Уведомление'
    message = 'Системное уведомление'

    send_notification(user, subject, message)
