from asyncio import AbstractEventLoop, Queue
from email.mime.multipart import MIMEMultipart
from logging import getLogger

from aiosmtpd.controller import UnthreadedController

from rapid7mail.config import Config


logger = getLogger('rapid7mail.handler.smtp_server')


class Handler:
    def __init__(self, eval_tasks: Queue[MIMEMultipart], config: Config):
        self._config = config
        self._eval_tasks = eval_tasks
        self.__event_counter = 0

    async def handle_RCPT(self, server, session, envelope: MIMEMultipart, address: str, rcpt_options):
        logger.debug(f'Recipient: {address}, From: {envelope.mail_from}')
        if address != self._config.agent_email:
            logger.warning(f'Invalid recipient: {address}')
            return '550 no such user'

        if envelope.mail_from not in self._config.allowed_emails:
            logger.warning(f'Invalid sender: {envelope.mail_from}')
            return '550 not relaying from that user'

        envelope.rcpt_tos.append(address)
        return '250 OK'

    async def handle_DATA(self, server, session, envelope: MIMEMultipart):
        self.__event_counter += 1
        if self.__event_counter % 100 == 0:
            logger.info(f'Handled {self.__event_counter} events')
        self._queue_task(envelope)
        return '250 Message accepted for delivery'

    def _queue_task(self, envelope: MIMEMultipart):
        logger.debug(f'Queuing task {id(envelope)}')
        self._eval_tasks.put_nowait(envelope)


def begin_smptd_controller(eval_tasks: Queue[MIMEMultipart], loop: AbstractEventLoop | None = None, config: Config | None = None) -> UnthreadedController:
    '''Starts an SMTP server task

    Creates unthreaded controller in the main loop, async loop must NOT be running
    '''
    logger.debug('Starting SMTP server')
    controller = UnthreadedController(Handler(eval_tasks=eval_tasks, config=config), loop=loop, hostname=config.smtpd_hostname, port=config.smtpd_port)
    controller.begin()
    return controller


def stop_smptd_controller(controller: UnthreadedController):
    '''Stops an SMTP server task'''
    logger.debug('Stopping SMTP server')
    controller.end()
