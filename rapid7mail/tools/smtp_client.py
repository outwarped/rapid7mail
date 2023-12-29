from io import BytesIO
from logging import getLogger
from pathlib import Path
from smtplib import SMTP

from rapid7mail.handler.helpers import create_email_envelope


logger = getLogger('rapid7mail.tools.smtp_client')


def entrypoint(smtpd_port: int, smtpd_hostname: str, email_from: str, email_to: list[str], email_subject: str, email_body: str, email_attachment: list[Path]):

    files = []
    logger.debug(f'Reading attachments: {email_attachment}')
    for attachment in email_attachment:
        with open(attachment, 'rb') as f:
            files.append(BytesIO(f.read()))
            logger.debug(f'Read {(files[-1].getbuffer().nbytes)} bytes from {attachment}')
    msg = create_email_envelope(email_from, email_to, email_subject, email_body, files)

    try:
        smtp = SMTP(smtpd_hostname, smtpd_port)
        logger.info(f'Sending email to {email_to}')
        errors = smtp.sendmail(email_from, email_to, msg.as_string())
    except Exception as e:
        logger.error(f'Error while sending email: {e}')
        return

    if errors:
        logger.warning(f'Errors while sending email: {errors}')
    else:
        logger.info('Email sent successfully')

    smtp.close()
