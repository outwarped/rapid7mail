from asyncio import Event as async_Event, Queue, new_event_loop, set_event_loop
from email import message_from_bytes
from io import BytesIO
from textwrap import dedent
from threading import Event as sync_Event, Thread
from time import sleep
from unittest import TestCase
from unittest.mock import ANY, MagicMock, patch

from rapid7mail.cmd.cli_main import main_loop
from rapid7mail.config import Config
from rapid7mail.handler.helpers import get_attachments

from tests.helpers import send_mail


class E2ETest(TestCase):
    @patch("rapid7mail.handler.worker.SMTP", autospec=True)
    def test_e2e(self, smtp_client_mock):
        # Given.
        config = Config(
            body_keywords=set(['eval']),
            allowed_emails=set(['test@localhost']),
            agent_email='agent@localhost',
        )

        sample_attachment = dedent("""
        print("Hello World")
        """).encode('utf8')
        sample_body = f"Here is the keyword _{list(config.body_keywords)[0]}_ in this body"
        send_from = list(config.allowed_emails)[0]
        send_to = [config.agent_email]

        # When.
        eval_queue = Queue()
        test_thread_event = sync_Event()
        loop_stop_event = async_Event()

        async def _mock_sendmail(*args, **kwargs):
            test_thread_event.set()
            loop_stop_event.set()
            return {}

        sendmail = MagicMock()
        sendmail.side_effect = _mock_sendmail
        smtp_client_mock.return_value.sendmail = sendmail

        def _run():
            loop = new_event_loop()
            set_event_loop(loop)
            main_loop(config=config, eval_queue=eval_queue, stop_async_waitable=loop_stop_event)

        thread = Thread(target=_run)
        thread.start()

        # TODO: implement a callback to know when the server is ready
        sleep(5)

        errors = send_mail(
            send_from=send_from,
            send_to=send_to,
            subject="Sujectb",
            text=sample_body,
            files=[BytesIO(sample_attachment)],
            server=config.smtpd_hostname,
            port=config.smtpd_port,
        )

        test_thread_event.wait(timeout=10)

        # Then.
        self.assertEqual(errors, {})
        self.assertTrue(test_thread_event.is_set())
        self.assertEqual(sendmail.call_count, 1)
        sendmail.assert_called_once_with(
            config.agent_email,
            [list(config.allowed_emails)[0]],
            ANY,
        )
        envelope = sendmail.call_args[0][2]
        envelope = envelope.encode('utf8')
        message = message_from_bytes(envelope)
        attachments = get_attachments(message)
        self.assertListEqual(attachments, ['Hello World\n'])
