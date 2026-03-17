import logging
import threading

from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _send_mail_async(**kwargs):
    try:
        send_mail(**kwargs)
    except Exception:
        logger.exception("Failed to send email to %s", kwargs.get('recipient_list'))


def send_verification_email(customer, request=None):
    token = customer.verification_token
    if request:
        base_url = request.build_absolute_uri('/verify/')
    else:
        base_url = 'http://localhost:8000/verify/'
    verify_url = f"{base_url}?token={token}"
    threading.Thread(
        target=_send_mail_async,
        kwargs=dict(
            subject='Verify your UNIMarket account',
            message=(
                f'Hi {customer.username},\n\n'
                f'Click the link below to verify your account:\n{verify_url}\n\n'
                f'If you did not register, please ignore this email.'
            ),
            from_email=None,
            recipient_list=[customer.email],
            fail_silently=False,
        ),
        daemon=True,
    ).start()


def send_password_reset_email(customer, request=None):
    token = customer.password_reset_token
    if request:
        base_url = request.build_absolute_uri('/reset-password/')
    else:
        base_url = 'http://localhost:8000/reset-password/'
    reset_url = f"{base_url}?token={token}"
    threading.Thread(
        target=_send_mail_async,
        kwargs=dict(
            subject='Reset your UNIMarket password',
            message=(
                f'Hi {customer.username},\n\n'
                f'Click the link below to reset your password:\n{reset_url}\n\n'
                f'This link expires in 1 hour.\n'
                f'If you did not request a reset, please ignore this email.'
            ),
            from_email=None,
            recipient_list=[customer.email],
            fail_silently=False,
        ),
        daemon=True,
    ).start()
