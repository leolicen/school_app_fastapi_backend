import logging
import sys
import os


def setup_logging() -> logging.Logger:
    """Configure and return the root logger.

    Reads LOG_LEVEL from the environment (default: INFO). Clears any pre-existing
    handlers (including those added by Python, Uvicorn, or FastAPI) to avoid
    duplicate log entries on repeated calls. Propagation to parent loggers is
    disabled so only the handlers configured here emit logs.

    Two handlers are attached:
    - stdout: captures DEBUG and INFO records only (filtered to avoid overlap with stderr).
    - stderr: captures WARNING, ERROR, and CRITICAL records.

    Both handlers share the same formatter: ``timestamp - name - level - message``.
    """
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    logger: logging.Logger = logging.getLogger()

    if logger.handlers:
        logger.handlers.clear()

    logger.propagate = False
    logger.setLevel(log_level)

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # stdout: DEBUG/INFO only
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.setFormatter(formatter)
    stdout_handler.addFilter(lambda record: record.levelno <= logging.INFO)

    # stderr: WARNING and above
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(formatter)

    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)

    return logger
