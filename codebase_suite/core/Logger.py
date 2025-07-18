import sys
import os

from singleton_decorator import singleton
from enum import Enum
from loguru import logger


class LogLevel(str, Enum):
    SILENT = "SILENT"
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    FATAL = "FATAL"


@singleton
class Logger:

    __logger = None

    def __init__(self, log_level=LogLevel.INFO, log_file=None, colorize=False):
        if log_level == LogLevel.SILENT:
            self.__logger = logger
            return

        logger.remove()

        format="<green>{time:MM-DD-YYYY HH:mm:ss}</green> [<level>{level: ^7}</level>] "
        if log_level == LogLevel.INFO:
            format+="{message}"
        else:
            # format+="{message}"
            format+="<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - {message}"
        
        logger.add(
            sys.stdout,
            level=log_level,
            colorize=colorize,
            format=format
        )

        if log_file:
            logger.add(
                log_file,
                level=log_level,
                rotation="10 MB",
                retention="1 day",
                compression="zip",
                enqueue=True,
                format="{time} | {level} | {name}:{function}:{line} | {message}"
            )

        self.__logger = logger 
        self.__logger.trace("✔️  Initial application logger successfully.")

    def get_logger(self):
        return self.__logger