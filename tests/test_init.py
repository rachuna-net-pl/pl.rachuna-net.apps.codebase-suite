import sys
from unittest import mock

from codebase_suite import main

def test_main_calls_commands_and_reconfigures_stdio(monkeypatch):
    # Mock stdin, stdout
    mock_stdin = mock.Mock()
    mock_stdout = mock.Mock()
    mock_stdin.reconfigure = mock.Mock()
    mock_stdout.reconfigure = mock.Mock()

    monkeypatch.setattr(sys, "stdin", mock_stdin)
    monkeypatch.setattr(sys, "stdout", mock_stdout)

    # Mock commands, żeby nie odpalało prawdziwego Clicka
    with mock.patch("codebase_suite.commands") as mock_commands:
        main()
        mock_commands.assert_called_once()

    mock_stdin.reconfigure.assert_called_once_with(encoding="utf-8")
    mock_stdout.reconfigure.assert_called_once_with(encoding="utf-8")
