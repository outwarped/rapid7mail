import anyio
from click import command, group
from aiosmtpd.controller import Controller
from asyncio import create_task, Queue, sleep, get_event_loop
from signal import signal, SIGINT, SIGTERM

from rapid7mail.handler.smtp_server import begin_smptd_controller, stop_smptd_controller
from rapid7mail.handler.eval_worker import eval_worker
from rapid7mail.config import Config


@command()
def entrypoint():
    config = Config()
    eval_queue = Queue()

    loop = get_event_loop()

    eval_workers = [loop.create_task(eval_worker(eval_queue=eval_queue)) for _ in range(1)]

    controller:Controller = begin_smptd_controller(eval_tasks=eval_queue, config=config, loop=loop)

    # TODO: implement a callback to know when the server is ready
    # TODO: implement testable termination
    loop.add_signal_handler(SIGINT, loop.stop)
    loop.add_signal_handler(SIGTERM, loop.stop)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    stop_smptd_controller(controller)
    
    eval_queue.join()

    for worker in eval_workers:
        worker.cancel()

    loop.close()
    