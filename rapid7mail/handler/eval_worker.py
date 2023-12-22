from io import StringIO
from contextlib import redirect_stdout
from threading import Thread, Event
from asyncio import Queue, create_task, CancelledError, sleep
from io import StringIO
from typing import Union, List, Generator
from typing import Union
import aiosmtplib as smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from io import StringIO
from contextlib import redirect_stdout

from rapid7mail.handler.records import EvalRequestTask
from rapid7mail.config import Config


async def send_eval_output(send_to_email, eval_output:StringIO, config:Union[None, Config]=None):
    msg = MIMEMultipart()
    msg['From'] = "a@b.c"
    msg['To'] = send_to_email
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = "subject"
    msg.attach(MIMEText(eval_output.getvalue()))

    try:
        smtp = smtplib.SMTP(hostname="127.0.0.1", port=8025)
        await smtp.connect()
    except Exception as e:
        print("SMTP Server not running")
        return

    smtp.sendmail("a@b.c", send_to_email, msg.as_string())
    smtp.close()


async def run_eval(eval_body:str, timeout:float | None=10) -> StringIO:
    def _run(event:Event, output:StringIO):
        with redirect_stdout(StringIO()) as f:
            exec(eval_body)
            output.write(f.getvalue())
        event.set()
        pass

    output = StringIO()

    event = Event()
    # TODO: Use subprocess and strict jail for eval.
    thread = Thread(target=_run, args=(event, output))
    thread.start()

    timeout_event = create_task(sleep(timeout)) if timeout is not None else None
    
    try:
        # TODO: find a better way of waiting for the finish state
        while not event.is_set() and (timeout_event is None or not timeout_event.done()):
            await sleep(0.1)
    except CancelledError:
        raise NotImplementedError("cancelling eval not implemented")
    finally:
        if timeout_event is not None:
            timeout_event.cancel()
        pass
    
    thread.join()

    return output


async def eval_one(source:str, timeout:float | None=10):
    output = await run_eval(source, timeout=timeout)
    await send_eval_output(send_to_email="a@b.c", eval_output=output)
    

async def eval_worker(eval_queue:Queue[EvalRequestTask]):
    while True:
        try:
            task = await eval_queue.get()
            await eval_one(task.eval_body, timeout=10)
        except CancelledError:
            break
