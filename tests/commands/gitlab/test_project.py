import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from click.testing import CliRunner

from codebase_suite.commands.gitlab import project


@pytest.fixture
def mock_logger():
    m = MagicMock()
    m.trace = MagicMock()
    m.error = MagicMock()
    return m

@patch("codebase_suite.commands.gitlab.project.Git")
@patch("codebase_suite.commands.gitlab.project.GitlabConnector")
@patch("codebase_suite.commands.gitlab.project.Console")
def test_project_info_command(mock_console_class, mock_gitlab_connector_class, mock_git_class, mock_logger):
    mock_console_instance = MagicMock()
    mock_console_class.return_value = mock_console_instance

    class CtxObj:
        def logger(self):
            return mock_logger

    runner = CliRunner()

    mock_git = MagicMock()
    mock_git.get_remote_url.return_value = "mygroup/myproject"
    mock_git_class.return_value = mock_git

    mock_gitlab_instance = MagicMock()
    mock_gitlab_instance.graphql_get_project.return_value = {
        "id": "123",
        "name": "Test Project",
        "archived": False,
        "description": "Test description",
        "visibility": "private",
        "topics": ["topic1", "topic2"],
        "fullPath": "mygroup/myproject"
    }
    mock_gitlab_instance.get_project_inherited_variables.return_value = {
        "VAR1:*:False": {
            "id": "1",
            "path": "mygroup/myproject",
            "key": "VAR1",
            "value": "value1",
            "masked": False,
            "protected": False,
            "environmentScope": "*",
            "description": "desc1"
        }
    }
    mock_gitlab_connector_class.return_value = mock_gitlab_instance

    result = runner.invoke(project, ['info', '--full-path', 'mygroup/myproject'], obj=CtxObj())

    assert result.exit_code == 0

    mock_git_class.assert_not_called()

    mock_gitlab_instance.graphql_get_project.assert_called_once_with("mygroup/myproject")
    mock_gitlab_instance.get_project_inherited_variables.assert_called_once_with("mygroup/myproject")

    assert mock_console_instance.print.call_count > 0


@patch("codebase_suite.commands.gitlab.project.Git")
@patch("codebase_suite.commands.gitlab.project.GitlabConnector")
@patch("codebase_suite.commands.gitlab.project.Console")
def test_project_info_command_with_src(mock_console_class, mock_gitlab_connector_class, mock_git_class, mock_logger):

    mock_console_instance = MagicMock()
    mock_console_class.return_value = mock_console_instance

    class CtxObj:
        def logger(self):
            return mock_logger

    runner = CliRunner()

    mock_git = MagicMock()
    mock_git.get_remote_url.return_value = "mygroup/myproject"
    mock_git_class.return_value = mock_git

    mock_gitlab_instance = MagicMock()
    mock_gitlab_instance.graphql_get_project.return_value = {
        "id": "123",
        "name": "Test Project",
        "archived": False,
        "description": "Test description",
        "visibility": "private",
        "topics": ["topic1", "topic2"],
        "fullPath": "mygroup/myproject"
    }
    mock_gitlab_instance.get_project_inherited_variables.return_value = {}
    mock_gitlab_connector_class.return_value = mock_gitlab_instance

    result = runner.invoke(project, ['info', '--src', str(Path("/fake/path"))], obj=CtxObj())

    assert result.exit_code == 0
    mock_git_class.assert_called_once()
    mock_git.get_remote_url.assert_called_once()
    mock_gitlab_instance.graphql_get_project.assert_called_once_with("mygroup/myproject")

    assert mock_console_instance.print.call_count > 0


@patch("codebase_suite.commands.gitlab.project.console.print")
def test_project_info_command_no_arguments(mock_print, mock_logger):
    class CtxObj:
        def logger(self):
            return mock_logger

    runner = CliRunner()

    result = runner.invoke(project, ['info'], obj=CtxObj())

    assert result.exit_code == 1
    mock_logger.error.assert_called_once_with("❌   No arguments. Specify --src or --full-path")
    assert mock_print.call_count == 0


@patch("codebase_suite.commands.gitlab.project.Git")
@patch("codebase_suite.commands.gitlab.project.console.print")
def test_project_info_command_src_path_not_found(mock_print, mock_git_class, mock_logger):

    class CtxObj:
        def logger(self):
            return mock_logger

    mock_git_instance = MagicMock()
    mock_git_instance.get_remote_url.side_effect = FileNotFoundError("not found")
    mock_git_class.return_value = mock_git_instance

    runner = CliRunner()

    fake_path = Path("/fake/path")

    result = runner.invoke(project, ['info', '--src', str(fake_path)], obj=CtxObj())

    assert result.exit_code == 1

    mock_logger.error.assert_called_with(f"❌  Repository path '{fake_path}' does not exist.")

    assert mock_print.call_count == 0

@patch("codebase_suite.commands.gitlab.project.GitlabConnector")
@patch("codebase_suite.commands.gitlab.project.Console")
def test_project_info_command_project_not_found(mock_console_class, mock_gitlab_connector_class, mock_logger):
    mock_console_instance = MagicMock()
    mock_console_class.return_value = mock_console_instance

    class CtxObj:
        def logger(self):
            return mock_logger

    runner = CliRunner()

    mock_gitlab_instance = MagicMock()
    mock_gitlab_instance.graphql_get_project.return_value = None
    mock_gitlab_connector_class.return_value = mock_gitlab_instance

    result = runner.invoke(project, ['info', '--full-path', 'mygroup/missing-project'], obj=CtxObj())

    assert result.exit_code == 1
    mock_logger.error.assert_called_once_with("❌    Project 'mygroup/missing-project' not found in gitlab.")
    assert mock_console_instance.print.call_count == 0