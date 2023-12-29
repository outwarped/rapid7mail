from logging import Formatter, StreamHandler, getLogger

from rapid7mail.cmd.cli_main import cli
import rapid7mail.cmd.cli_tools  # noqa


c_handler = StreamHandler()
c_handler.setFormatter(Formatter('%(name)s - %(levelname)s - %(message)s'))
getLogger("root").addHandler(c_handler)


if __name__ == '__main__':
    cli(obj={})
