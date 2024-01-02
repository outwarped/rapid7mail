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

from tests.helpers import send_mail


class E2ETest(TestCase):
    '''End to end tests. Test start with Threaded unstarted async loop in separate thread.'''

    @patch("rapid7mail.handler.worker.SMTP", autospec=True)
    def test_e2e_ok(self, smtp_client_mock):
        '''Happy path test. Send an 'Hello world' attachment email to the agent.'''
        # Given.
        config = Config(
            body_keywords=set(['eval']),
            allowed_emails=set(['test@localhost']),
            agent_email='agent@localhost',
            python_eval_timeout=1,
        )

        sample_attachment = dedent("""
        print("Hello World")
        """).encode('utf8')

        sample_body = f"Here is the keyword _{list(config.body_keywords)[0]}_ in this body"
        send_from = list(config.allowed_emails)[0]
        send_to = [config.agent_email]

        # When.
        eval_queue = Queue()
        # sync (threading) Waitable to indicate end of test event from a thread
        test_thread_event = sync_Event()
        # async Waitable as signal substitude for graceful termination
        loop_stop_event = async_Event()

        # side-effect callback to simulate signal and indicate end of test
        async def _mock_sendmail(*args, **kwargs):
            test_thread_event.set()
            loop_stop_event.set()
            return {}

        # Monkey patching sendmail to stop the thread and the loop once the message is sent
        sendmail_mock = MagicMock()
        sendmail_mock.side_effect = _mock_sendmail
        smtp_client_mock.return_value.sendmail = sendmail_mock

        # running the main loop in a separate thread
        def _run_main_loop():
            loop = new_event_loop()
            set_event_loop(loop)
            main_loop(config=config, eval_queue=eval_queue, stop_async_waitable=loop_stop_event)

        thread = Thread(target=_run_main_loop)
        thread.start()

        # TODO: implement a callback to know when the server is ready
        # Let SMTP server start
        sleep(1)

        client_send_mail_errors = send_mail(
            send_from=send_from,
            send_to=send_to,
            subject="Suject",
            text=sample_body,
            files=[BytesIO(sample_attachment)],
            server=config.smtpd_hostname,
            port=config.smtpd_port,
        )

        # Wait for the Worker to eval the message and send the reply
        test_thread_event.wait(timeout=5)

        # Then.
        self.assertEqual(client_send_mail_errors, {})
        # check that the main thread exited gracefully
        self.assertTrue(test_thread_event.is_set())
        self.assertEqual(sendmail_mock.call_count, 1)
        # called once with the right sender, recipient
        sendmail_mock.assert_called_once_with(
            config.agent_email,
            [list(config.allowed_emails)[0]],
            ANY,
        )
        # check email body
        envelope = sendmail_mock.call_args[0][2]
        envelope = envelope.encode('utf8')
        message = message_from_bytes(envelope)
        message_body = message.get_payload(0).get_payload(decode=True).decode('utf8')
        self.assertIn('Hello World', message_body)
