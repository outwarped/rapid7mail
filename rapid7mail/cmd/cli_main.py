from asyncio import Event, Queue, get_event_loop
from logging import getLogger
from signal import SIGINT, signal

from click import group, option, pass_context

from rapid7mail.config import Config
from rapid7mail.handler.tasks import schedule_tasks


logger = getLogger('rapid7mail.cmd')


def main_loop(config: Config, eval_queue: Queue, stop_async_waitable: Event | None = None):
    logger.info('Starting main loop')
    loop = get_event_loop()

    stop_tasks = schedule_tasks(eval_queue=eval_queue, config=config)

    if stop_async_waitable is None:
        loop.run_forever()
    else:
        stop_task = loop.create_task(stop_async_waitable.wait())
        loop.run_until_complete(stop_task)
    logger.info('Stopping main loop')
    stop_tasks()
    loop.run_until_complete(stop_task)
    logger.info('Main loop stopped')


def entrypoint(config: Config):
    eval_queue = Queue()

    stop_waitable = Event()

    signal(SIGINT, lambda *_: get_event_loop().call_soon_threadsafe(stop_waitable.set))

    main_loop(stop_async_waitable=stop_waitable, config=config, eval_queue=eval_queue)

    get_event_loop().close()


@group(invoke_without_command=True)
@pass_context
@option('--smtpd-port', type=int, default=8025, help='Receiving SMTP server port (for receiving evaluation requests)')
@option('--smtpd-hostname', type=str, default='127.0.0.1', help='Receiving SMTP server hostname (for receiving evaluation requests)')
@option('--smtp-client-port', type=int, default=8026, help='Sending SMTP server port (for sending evaluation results)')
@option('--smtp-client-hostname', type=str, default='127.0.0.1', help='Sending SMTP server hostname (for sending evaluation results)')
@option('--python-workers', type=int, default=1, help='Number of concurrent python exec workers')
@option('--python-eval-timeout', type=int, default=10, help='Python exec timeout in seconds')
@option('--max-allowed-output-size', type=int, default=1024 * 1024, help='Maximum allowed output size in bytes')
@option('--agent-email', type=str, help='Receiver email address for evaluation requests, other emails will be rejected')
@option('--allowed-emails', type=str, multiple=True, help='Allowed sender email addresses for evaluation requests, other emails will be rejected')
@option('--body-keywords', type=str, multiple=True, help='Allowed keywords in email body, emails without any of these keywords will be rejected')
@option('--log-level', type=str, default='INFO', help='Logging level')
def cli(ctx, smtpd_port: int, smtpd_hostname: str, smtp_client_port: int, smtp_client_hostname: str,
        python_workers: int, python_eval_timeout: int, max_allowed_output_size: int, agent_email: str,
        allowed_emails: list[str], body_keywords: list[str], log_level: str):

    getLogger('root').setLevel(log_level)

    ctx.obj = Config(
        smtpd_port=smtpd_port,
        smtpd_hostname=smtpd_hostname,
        smtp_client_port=smtp_client_port,
        smtp_client_hostname=smtp_client_hostname,
        python_workers=python_workers,
        python_eval_timeout=python_eval_timeout,
        max_allowed_output_size=max_allowed_output_size,
        agent_email=agent_email,
        allowed_emails=allowed_emails,
        body_keywords=body_keywords,
    )

    if ctx.invoked_subcommand is None:
        entrypoint(config=ctx.obj)


@cli.command()
@pass_context
def run(ctx):
    entrypoint(config=ctx.obj)
