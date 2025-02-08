"""First entry point of the app."""

import inspect
import sys

from src.cli import init_argparse
from src.controller import logger as controller_logger
from src.filehandler import logger as fh_logger
from src.loghandler import LogLevel, set_loglevel
from src.packethandler import logger as ph_logger

loggers = [fh_logger, ph_logger, controller_logger]


if __name__ == "__main__":
    parser = init_argparse()
    args = parser.parse_args()

    [set_loglevel(logger, LogLevel.DEBUG) for logger in loggers if args.debug]

    # check if a cli parameter runs a function
    if hasattr(args, "func"):
        # check if a function has no argument
        sig = inspect.signature(args.func)
        if len(sig.parameters) == 0:
            args.func()
        else:
            args.func(args)
    # default function without a parameter
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
