import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from .config import Settings

log = logging.getLogger("meetpoint.mail")


def send_mail(settings: Settings, to: str, subject: str, body: str) -> None:
    """응답을 보낸 뒤 백그라운드에서 부른다. 실패해도 관리 주소는 화면에 나와 있으니 기록만 남긴다."""
    msg = EmailMessage()
    msg["From"] = formataddr(("Meetpoint", settings.mail_from or settings.smtp_user))
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        # ponytail: STARTTLS(587)만 쓴다. 465 전용 서버를 쓰게 되면 SMTP_SSL을 더한다.
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)
    except Exception:
        log.exception("관리 주소 메일을 보내지 못했습니다")
