from typing import Union, List, Generator
from typing import Union
import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import message_from_bytes
from asyncio import Queue
from aiosmtpd.controller import Controller, UnthreadedController
from asyncio import AbstractEventLoop


from rapid7mail.config import Config
from rapid7mail.handler.records import EvalRequestTask


def attachments_to_eval_task(envelope) -> Generator[List[EvalRequestTask], None, None]:
    
    message = message_from_bytes(envelope.original_content)
    attachments = []
    for part in message.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue
        attachments.append(part)

    
    for attachment in attachments:
        eval_task = EvalRequestTask(
            eval_body=attachment.get_payload(decode=True),
            task_from_email=envelope.mail_from,
        )
        yield eval_task


class Handler:
    def __init__(self, eval_tasks:Queue, config:Union[None, Config]=None):
        self._config = config
        self._eval_tasks = eval_tasks
    
    async def handle_RCPT(self, server, session, envelope, address, rcpt_options):
        if not envelope.mail_from.endswith('@rapid7.com'):
            return '550 not relaying from that domain'
        
        envelope.rcpt_tos.append(address)
        return '250 OK'
    
    async def handle_DATA(self, server, session, envelope):
        body_utf8 = envelope.content.decode('utf8', errors='replace')

        if 'banana' in body_utf8:
            return '550 Message contains virus'

        for task in attachments_to_eval_task(envelope):
            self._queue_task(task)

        return '250 Message accepted for delivery'

    def _queue_task(self, task:EvalRequestTask):
        self._eval_tasks.put_nowait(task)

def begin_smptd_controller(eval_tasks:Queue[EvalRequestTask], loop:AbstractEventLoop | None = None, config:Union[None, Config]=None) -> Controller:
    controller = UnthreadedController(Handler(eval_tasks=eval_tasks, config=config), loop=loop, hostname='localhost', port=8025)
    controller.begin()
    return controller

def stop_smptd_controller(controller:Controller):
    controller.stop()