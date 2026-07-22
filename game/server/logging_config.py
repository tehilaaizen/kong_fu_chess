from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from server.event_log import Emit

DEFAULT_LOG_FILE = "logs/server.log"


def configure_logging(log_file: str = DEFAULT_LOG_FILE) -> Emit:
    """Point loguru at the console and a rotating log file, and return the
    emit callback (a thin wrapper over logger.info) that EventLog logs
    each line through. Called once at server startup - the only place that
    knows loguru exists, keeping the logging library out of the app and
    server logic. The message is passed as an argument (not as the format
    string) so any braces in a log line stay literal."""
    logger.remove()  # drop loguru's default handler so we own the sinks
    logger.add(sys.stderr, level="INFO")
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logger.add(log_file, level="INFO", rotation="10 MB", retention=5, encoding="utf-8")
    # depth=1 so each line is attributed to the code that called emit (the
    # EventLog), not to this wrapper lambda.
    return lambda message: logger.opt(depth=1).info("{}", message)
