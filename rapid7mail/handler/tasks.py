from asyncio import Queue, get_event_loop
from logging import getLogger

from aiosmtpd.controller import Controller

from rapid7mail.config import Config
from rapid7mail.handler.smtp_server import begin_smptd_controller, stop_smptd_controller
from rapid7mail.handler.worker import eval_worker


logger = getLogger('rapid7mail.handler.tasks')


def schedule_tasks(eval_queue: Queue, config: Config) -> callable:
    loop = get_event_loop()
    logger.debug('Scheduling tasks')
    eval_workers = [loop.create_task(eval_worker(eval_queue=eval_queue, config=config)) for _ in range(config.python_workers)]
    controller: Controller = begin_smptd_controller(eval_tasks=eval_queue, config=config, loop=loop)

    def stop_tasks():
        logger.debug('Called stop_tasks')
        stop_smptd_controller(controller)
        logger.debug('Waiting for queue to empty')
        loop.run_until_complete(loop.create_task(eval_queue.join()))
        for worker in eval_workers:
            logger.debug('Cancelling worker')
            worker.cancel()
            logger.debug('Waiting for worker to stop')
            loop.run_until_complete(worker)
            logger.debug('Worker stopped')
    return stop_tasks
