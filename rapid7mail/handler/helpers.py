from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE
from email.utils import formatdate
from typing import Set


def create_email_envelope(send_from, send_to, subject, text, files=None) -> MIMEMultipart:
    assert isinstance(send_to, list) or isinstance(send_to, tuple)

    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

    for f in files or []:
        part = MIMEApplication(
                f.read(),
                Name="some_file",
            )
        part['Content-Disposition'] = 'attachment; filename="some_file"'
        msg.attach(part)

    return msg


def check_keywords(body_utf8: str, keywords: Set[str]) -> bool:
    return any(keyword in body_utf8 for keyword in keywords)


def get_attachments(message: MIMEMultipart) -> list[str]:
    attachments = []
    for part in message.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue

        attachment_str = part.get_payload(decode=True).decode('utf8', errors='replace')
        attachments.append(attachment_str)
    return attachments
