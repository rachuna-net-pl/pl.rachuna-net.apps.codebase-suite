from singleton_decorator import singleton
import logging

from typing import Union

from .Logger import Logger, LogLevel
from ..config import Config


@singleton
class Context:
    """
    Klasa kontekstowa do przechowywania stanu aplikacji.
    """
    
    def __init__(self, verbose: int = 0, colorize: bool = True) -> None:
        """
        Inicjalizacja kontekstu aplikacji.
        """
        log_level = LogLevel.INFO
        if verbose == 1:    # pragma: no cover
            log_level = LogLevel.DEBUG 
        elif verbose >= 2:    # pragma: no cover
            log_level = LogLevel.TRACE

        self.__logger = Logger(log_level=log_level, colorize=colorize)
        self.__logger.get_logger().trace("✔️  Initial application context successfully.")

    def get_config(self) -> Config:
        """Ustawia konfigurację GitLab."""
        return Config()

    def logger(self) -> Logger:
        """Zwraca logger z kontekstem."""
        return self.__logger.get_logger()    # pragma: no cover