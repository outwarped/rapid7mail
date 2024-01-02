from asyncio import Event, Queue, get_event_loop
from logging import getLogger

from aiosmtpd.controller import Controller

from rapid7mail.config import Config
from rapid7mail.handler.smtp_server import begin_smptd_controller, stop_smptd_controller
from rapid7mail.handler.worker import eval_worker_loop


logger = getLogger('rapid7mail.handler.tasks')


def schedule_tasks(eval_queue: Queue, config: Config) -> callable:
    '''Schedules tasks for the main loop, returns a callable to stop all tasks

    Creates a task for each worker and a task for the SMTP server controller.
    Returns a callable to gracefully stop all tasks.
    '''
    loop = get_event_loop()
    logger.debug('Scheduling tasks')
    eval_workers = [loop.create_task(eval_worker_loop(eval_queue=eval_queue, config=config)) for _ in range(config.python_workers)]
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


def main_loop(config: Config, eval_queue: Queue, stop_async_waitable: Event | None = None):
    '''Creates main application tasks and waits for stop event

    In the main async loop creates SMPT server task, worker tasks, a task to wait on stop event.
    After event is set, gracefully stops all tasks.
    '''
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
