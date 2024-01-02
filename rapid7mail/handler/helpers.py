from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE
from email.utils import formatdate
from io import BufferedReader
from typing import List, Set, Tuple


def create_email_envelope(send_from: str, send_to: list | tuple, subject: str, text: str, files: List[BufferedReader] | None = None) -> MIMEMultipart:
    '''Creates an email envelope with attachments'''
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
    '''Checks if any of the keywords are in the body of the email'''
    return any(keyword in body_utf8 for keyword in keywords)


def get_attachments(message: MIMEMultipart) -> list[Tuple[str, str]]:
    '''Returns a list of attachments from an email message

    Returns a list of tuples of the form (filename, file_contents)
    '''
    attachments = []
    for part in message.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue

        attachment_str = part.get_payload(decode=True).decode('utf8', errors='replace')
        attachment_name = part.get_filename()
        attachments.append((attachment_name, attachment_str))
    return attachments
