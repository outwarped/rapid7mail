from asyncio import AbstractEventLoop, Event, get_event_loop, new_event_loop, set_event_loop
from email import message_from_bytes
from email.mime.multipart import MIMEMultipart
from logging import getLogger
from signal import SIGINT, signal

from aiosmtpd.controller import Controller, UnthreadedController

from rapid7mail.handler.helpers import get_attachments


logger = getLogger('rapid7mail.tools.smtp_server')


class Handler:
    async def handle_RCPT(self, server, session, envelope: MIMEMultipart, address: str, rcpt_options):
        envelope.rcpt_tos.append(address)
        return '250 OK'

    async def handle_DATA(self, server, session, envelope: MIMEMultipart):
        message = message_from_bytes(envelope.original_content)
        attachments = get_attachments(message)
        logger.info(f'Email received: {message["Subject"]}, {message["From"]}, {message["To"]}, {attachments}')

        return '250 Message accepted for delivery'


def begin_smptd_controller(hostname, port, loop: AbstractEventLoop | None = None) -> UnthreadedController:
    logger.debug(f'Starting SMTP server at {hostname}:{port}')
    controller = UnthreadedController(Handler(), loop=loop, hostname=hostname, port=port)
    controller.begin()
    return controller


def stop_smptd_controller(controller: UnthreadedController):
    logger.debug('Stopping SMTP server')
    controller.end()


def schedule_tasks(hostname, port) -> callable:
    loop = get_event_loop()
    logger.debug('Scheduling tasks')
    controller: Controller = begin_smptd_controller(hostname=hostname, port=port, loop=loop)

    def stop_tasks():
        logger.debug('Called stop_tasks')
        stop_smptd_controller(controller)
    return stop_tasks


def main_loop(hostname, port, stop_async_waitable: Event | None = None):
    logger.info('Starting main loop')
    loop = get_event_loop()

    stop_tasks = schedule_tasks(hostname=hostname, port=port)

    if stop_async_waitable is None:
        loop.run_forever()
    else:
        stop_task = loop.create_task(stop_async_waitable.wait())
        loop.run_until_complete(stop_task)
    logger.info('Stopping main loop')
    stop_tasks()
    loop.run_until_complete(stop_task)
    logger.info('Main loop stopped')


def entrypoint(smtpd_port: int, smtpd_hostname: str):

    loop = new_event_loop()
    set_event_loop(loop)

    stop_waitable = Event()

    signal(SIGINT, lambda *_: get_event_loop().call_soon_threadsafe(stop_waitable.set))

    main_loop(stop_async_waitable=stop_waitable, hostname=smtpd_hostname, port=smtpd_port)

    get_event_loop().close()
