import pytest
from unittest.mock import patch, MagicMock
from codebase_suite.core.Context import Context
from codebase_suite.core.Logger import LogLevel
from codebase_suite.config import Config
from functools import wraps


def reset_context_singleton(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        Context._singleton__instances = {}
        return func(*args, **kwargs)
    return wrapper

@patch("codebase_suite.core.Context.Config")
def test_get_config_returns_config_instance(mock_config_cls):
    mock_config_instance = MagicMock()
    mock_config_cls.return_value = mock_config_instance

    ctx = Context()
    config = ctx.get_config()

    mock_config_cls.assert_called_once()
    assert config is mock_config_instance

def test_context_is_singleton():
    ctx1 = Context()
    ctx2 = Context()
    assert ctx1 is ctx2
