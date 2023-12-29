from asyncio import CancelledError, TimeoutError, create_subprocess_shell, wait_for
from asyncio.streams import _DEFAULT_LIMIT as STREAM_DEFAULT_LIMIT
from asyncio.subprocess import PIPE
from logging import getLogger

from asynctempfile import TemporaryDirectory


logger = getLogger('rapid7mail.handler.py_eval')


async def run_subprocess_eval(eval_body: str, max_output_size: int = STREAM_DEFAULT_LIMIT, timeout_delay: float | None = 10) -> str:
    # TODO: Use subprocess and strict jail for eval.
    # TODO: Timeout for file creation.
    # TODO: WORKAROUND with tempdir, NamedTemporaryFile bug. https://github.com/Tinche/aiofiles/issues/166

    logger.debug('Running subprocess eval')

    async with TemporaryDirectory() as tmpdir:
        with open(f"{tmpdir}/eval.py", "w") as input:
            input.write(eval_body)

        try:
            process = await create_subprocess_shell(
                f"python {tmpdir}/eval.py",
                stdout=PIPE,
                stderr=PIPE,
                limit=max_output_size,
            )
            logger.debug('Created subprocess PID: %d', process.pid)
        except CancelledError:
            logger.debug('Creating subprocess cancelled')
            return ""
        except Exception as e:
            logger.error(f'Creating subprocess failed: {e}')
            return str(e)

        try:
            await wait_for(process.wait(), timeout=timeout_delay)
            logger.debug('Subprocess finished')
        except TimeoutError:
            logger.debug(f'Subprocess timed out after {timeout_delay} seconds, killing')
            process.terminate()
            # WORKAROUND: Process.communicate does not terminate. https://github.com/python/cpython/issues/88050
            process._transport.close()
        except CancelledError:
            logger.debug('Subprocess task cancelled, killing')
            process.terminate()
            # WORKAROUND: Process.communicate does not terminate. https://github.com/python/cpython/issues/88050
            process._transport.close()

        result = ""
        try:
            stdout, stderr = await process.communicate()
            result = stdout.decode() + stderr.decode()
        except TimeoutError:
            pass
        except CancelledError:
            pass
        except Exception as e:
            result = str(e)

        logger.debug(f'Read {len(result)} bytes from subprocess')
        return result
