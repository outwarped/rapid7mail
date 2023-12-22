from unittest import TestCase, TestSuite, TextTestRunner, IsolatedAsyncioTestCase
from unittest.mock import patch, MagicMock, ANY
import smtplib
from click.testing import CliRunner
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from textwrap import dedent
from io import StringIO, BytesIO
from asyncio import create_task, get_event_loop, new_event_loop, set_event_loop
from time import sleep
from threading import Thread, Event
import signal

from rapid7mail.cmd.cli_main import entrypoint

def send_mail(send_from, send_to, subject, text, files=None, server="127.0.0.1", port=8025):
    assert isinstance(send_to, list)

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
        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="some_file"'
        msg.attach(part)


    smtp = smtplib.SMTP(server, port)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()


class E2ETest(TestCase):
    def test_e2e(self):
        runner = CliRunner()
        def _run():
            # TODO: implement loop termination
            loop = new_event_loop()
            set_event_loop(loop)
            runner.invoke(entrypoint)

        thread = Thread(target=_run)
        thread.start()
        
        # TODO: implement a callback to know when the server is ready
        sleep(1)

        event = Event()
        async def _mock_send_mail(*args, **kwargs):
            event.set()
            return send_mail(*args, **kwargs)

        send_eval_output_mock = MagicMock()
        send_eval_output_mock.side_effect = _mock_send_mail
        with patch("rapid7mail.handler.eval_worker.send_eval_output", send_eval_output_mock):

            sample_attachment = dedent("""
            print("Hello World")
            """).encode('utf8')

            send_mail(
                send_from="a@rapid7.com",
                send_to=["a@b.c"],
                subject="Hello",
                text="World",
                files=[BytesIO(sample_attachment)],
            )
            
            event.wait(timeout=10)
        
        self.assertTrue(event.is_set())
        self.assertEqual(send_eval_output_mock.call_count, 1)
        send_eval_output_mock.assert_called_once_with(
            send_to_email="a@b.c",
            eval_output=ANY,
        )
        output = send_eval_output_mock.call_args[1]['eval_output']
        output.seek(0)
        self.assertEqual(output.read(), b'Hello World\n')