from asyncio import CancelledError, Queue
from email import message_from_bytes
from email.mime.multipart import MIMEMultipart
from io import StringIO
from logging import getLogger

from aiosmtplib import SMTP

from rapid7mail.config import Config
from rapid7mail.handler.helpers import check_keywords, create_email_envelope, get_attachments
from rapid7mail.handler.py_eval import run_subprocess_eval


logger = getLogger('rapid7mail.handler.worker')


async def send_mail(smtp_client: SMTP, send_from, send_to, subject, text, files=None):
    logger.debug(f'Sending mail to {send_to}')
    msg = create_email_envelope(send_from, send_to, subject, text, files)
    try:
        await smtp_client.sendmail(send_from, send_to, msg.as_string())
    except Exception as e:
        logger.error(f'Error while sending email: {e}')


async def eval_one_envelope(smtp_client: SMTP, envelope: MIMEMultipart, config: Config):
    body_utf8 = envelope.content.decode('utf8', errors='replace')

    if not check_keywords(body_utf8, config.body_keywords):
        logger.warning(f'No allowed keywords found in body from {envelope.mail_from}')

        logger.debug('Connecting SMTP Client')
        await smtp_client.connect()
        await send_mail(
            smtp_client=smtp_client,
            send_from=config.agent_email,
            send_to=[envelope.mail_from],
            subject="Evaluation Output",
            text="No allowed keywords found in body."
        )
        logger.debug('Closing SMTP Client')
        smtp_client.close()
        return

    message = message_from_bytes(envelope.original_content)

    attachments = get_attachments(message)

    outputs = []

    for attachment in attachments:
        output = await run_subprocess_eval(attachment, max_output_size=config.max_allowed_output_size, timeout_delay=config.python_eval_timeout)
        outputs.append(StringIO(output))

    logger.debug('Connecting SMTP Client')
    await smtp_client.connect()
    await send_mail(
        smtp_client=smtp_client,
        send_from=config.agent_email,
        send_to=[envelope.mail_from],
        subject="Evaluation Output",
        text="",
        files=outputs,
    )
    logger.debug('Closing SMTP Client')
    smtp_client.close()


async def eval_worker(eval_queue: Queue[MIMEMultipart], config: Config):
    logger.debug('Starting eval worker')
    smtp_client = SMTP(hostname=config.smtp_client_hostname, port=config.smtp_client_port)

    while True:
        try:
            envelope = await eval_queue.get()
            logger.debug(f'Eval worker got envelope {id(envelope)}')
        except CancelledError:
            logger.debug('Eval worker cancelled')
            break

        logger.debug(f'Eval worker got envelope from {envelope.mail_from}')
        await eval_one_envelope(smtp_client, envelope, config)
        eval_queue.task_done()
        logger.debug('Eval worker task done')
