import pytest
import time

from loguru import logger as global_logger
from codebase_suite.core.Logger import Logger, LogLevel

@pytest.fixture(autouse=True)
def reset_loguru(monkeypatch):
    """Resetuje instancję Logger singletona i loggera loguru przed każdym testem."""
    if "_instance" in Logger.__dict__:
        Logger._instance = None
    global_logger.remove()
    yield
    global_logger.remove()


def test_logger_silent_does_not_configure(caplog):
    logger_instance = Logger(log_level=LogLevel.SILENT)
    log = logger_instance.get_logger()
    log.info("This should not appear")
    assert "This should not appear" not in caplog.text


def test_logger_info_stdout_output(capfd):
    logger_instance = Logger(log_level=LogLevel.INFO)
    log = logger_instance.get_logger()
    log.info("Hello INFO")
    out, err = capfd.readouterr()
    assert "Hello INFO" in out
    assert "INFO" in out


def test_logger_trace_format_includes_function(capfd):
    logger_instance = Logger(log_level=LogLevel.TRACE)
    log = logger_instance.get_logger()
    log.trace("Trace me")
    out, err = capfd.readouterr()
    assert "Trace me" in out
    assert __name__ in out
    assert "test_logger_trace_format_includes_function" in out


def test_logger_with_log_file(tmp_path):
    log_file = tmp_path / "app.log"
    logger_instance = Logger(log_level=LogLevel.DEBUG, log_file=str(log_file))
    log = logger_instance.get_logger()
    log.debug("To file")

    time.sleep(0.1)

    assert log_file.exists()
    content = log_file.read_text()
    assert "To file" in content
    assert "DEBUG" in content


def test_logger_get_logger_returns_instance():
    logger_instance = Logger(log_level=LogLevel.INFO)
    log1 = logger_instance.get_logger()
    log2 = Logger().get_logger()
    assert log1 is log2
