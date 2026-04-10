import logging
import os
from typing import Iterable

from rich.logging import RichHandler

_FILE_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_FILE_LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"


class _PybaseballFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.name.startswith("pybaseball")


def _coerce_log_level(level: int | str) -> int:
    if isinstance(level, int):
        return level
    normalized = level.upper()
    if normalized in logging._nameToLevel:
        return logging._nameToLevel[normalized]
    raise ValueError(f"Invalid log level: {level}")


def _iter_pybaseball_loggers() -> Iterable[logging.Logger]:
    for name, logger in logging.root.manager.loggerDict.items():
        if isinstance(logger, logging.Logger) and name.startswith("pybaseball"):
            yield logger


def _root_has_handler(
    root: logging.Logger, handler_type: type, log_filepath: str | None = None
) -> bool:
    for handler in root.handlers:
        if isinstance(handler, handler_type):
            if log_filepath is None:
                return True
            if getattr(handler, "baseFilename", None) == os.path.abspath(log_filepath):
                return True
    return False


def _apply_file_formatter(root: logging.Logger, log_filepath: str) -> None:
    formatter = logging.Formatter(_FILE_LOG_FORMAT, datefmt=_FILE_LOG_DATEFMT)
    for handler in root.handlers:
        if isinstance(handler, logging.FileHandler):
            if getattr(handler, "baseFilename", None) == os.path.abspath(log_filepath):
                handler.setFormatter(formatter)


def initialize_logger(
    console_level: int | str = logging.INFO,
    log_filepath: str = ".pybaseball_logs/pybaseball.log",
    plain: bool = False,
) -> None:
    """
    Initialize the logger for the pybaseball package.
    """
    console_level = _coerce_log_level(console_level)
    log_dir = os.path.dirname(log_filepath)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    log_filter = _PybaseballFilter()

    if not _root_has_handler(root_logger, RichHandler):
        console_handler = RichHandler(level=console_level)
        console_handler.addFilter(log_filter)
        root_logger.addHandler(console_handler)

    if not _root_has_handler(root_logger, logging.FileHandler, log_filepath):
        file_handler = logging.FileHandler(log_filepath, mode="a")
        file_handler.setLevel(logging.DEBUG)
        file_handler.addFilter(log_filter)
        file_handler.setFormatter(
            logging.Formatter(_FILE_LOG_FORMAT, datefmt=_FILE_LOG_DATEFMT)
        )
        root_logger.addHandler(file_handler)
    else:
        _apply_file_formatter(root_logger, log_filepath)

    for child in _iter_pybaseball_loggers():
        child.setLevel(logging.NOTSET)
        child.propagate = True
