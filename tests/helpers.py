import smtplib

from rapid7mail.handler.helpers import create_email_envelope


def send_mail(send_from, send_to, subject, text, files=None, server="0.0.0.0", port=8025) -> dict:
    msg = create_email_envelope(send_from, send_to, subject, text, files)

    smtp = smtplib.SMTP(server, port)
    errors = smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()

    return errors
