from pathlib import Path

from click import option

from rapid7mail.cmd.cli_main import cli
from rapid7mail.tools.smtp_client import entrypoint as smtp_client_entrypoint
from rapid7mail.tools.smtp_server import entrypoint as smtp_server_entrypoint


@cli.command()
@option('--smtpd-port', type=int, default=8026, help='Sending SMTP server port (for sending evaluation results)')
@option('--smtpd-hostname', type=str, default='127.0.0.1', help='Sending SMTP server hostname (for sending evaluation results)')
def server(smtpd_port: int, smtpd_hostname: str):
    smtp_server_entrypoint(
        smtpd_port=smtpd_port,
        smtpd_hostname=smtpd_hostname,
    )


@cli.command()
@option('--smtpd-port', type=int, default=8025, help='Receiving SMTP server port (for receiving evaluation requests)')
@option('--smtpd-hostname', type=str, default='127.0.0.1', help='Receiving SMTP server hostname (for receiving evaluation requests)')
@option('--email-from', type=str, help='Receiver email address for evaluation requests, other emails will be rejected')
@option('--email-to', type=str, multiple=True, help='Allowed sender email addresses for evaluation requests, other emails will be rejected')
@option('--email-subject', type=str, help='Subject of the email')
@option('--email-body', type=str, help='Body of the email')
@option('--email-attachment', type=Path, multiple=True, help='Attachment to send')
def client(smtpd_port: int, smtpd_hostname: str, email_from: str, email_to: list[str], email_subject: str, email_body: str, email_attachment: list[Path]):
    smtp_client_entrypoint(
        smtpd_port=smtpd_port,
        smtpd_hostname=smtpd_hostname,
        email_from=email_from,
        email_to=email_to,
        email_subject=email_subject,
        email_body=email_body,
        email_attachment=email_attachment,
    )
