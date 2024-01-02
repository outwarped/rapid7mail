from asyncio import wait_for
from textwrap import dedent
from unittest import IsolatedAsyncioTestCase

from rapid7mail.handler.py_eval import run_subprocess_eval


class EvalTest(IsolatedAsyncioTestCase):
    async def test_run_subprocess_eval_timeout(self):
        # Given.
        code = dedent("""
                      while True:
                        print("Hello World")
                      """)

        # When.
        result = await wait_for(run_subprocess_eval(code, timeout_delay=0.1, ), timeout=1)

        # Then.
        self.assertTrue(result.startswith("Hello World"))

    async def test_run_subprocess_eval_ok(self):
        # Given.
        code = dedent("""
                      print("Hello World")
                      """)

        # When.
        result = await wait_for(run_subprocess_eval(code, timeout_delay=0.1), timeout=1)

        # Then.
        self.assertEqual(result, "Hello World\n")

    async def test_run_subprocess_eval_exception(self):
        # Given.
        code = dedent("""
                      raise Exception("Hello World")
                      """)

        # When.
        result = await wait_for(run_subprocess_eval(code, timeout_delay=0.1), timeout=1)

        # Then.
        self.assertTrue(result.startswith('Traceback (most recent call last)'))
