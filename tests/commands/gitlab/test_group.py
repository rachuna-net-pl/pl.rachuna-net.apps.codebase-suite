import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from codebase_suite.commands.gitlab.group import group
from rich.console import Console
from rich.text import Text
from io import StringIO


@patch("codebase_suite.commands.gitlab.group.GitlabConnector")
@patch("codebase_suite.commands.gitlab.group.Console")
def test_list_badges_command(mock_console_class, mock_gitlab_connector_class):
    mock_logger = MagicMock()

    ctx_obj = MagicMock()
    ctx_obj.logger.return_value = mock_logger

    fake_badges = [
        {
            "id": 123,
            "name": "CI Passed",
            "link_url": "https://gitlab.com/pl.rachuna-net/app/badges/master/pipeline.svg",
            "image_url": "https://img.shields.io/gitlab/pipeline/status.svg",
        },
        {
            "id": 456,
            "name": "Coverage",
            "link_url": "https://gitlab.com/pl.rachuna-net/app/badges/master/coverage.svg",
            "image_url": "https://img.shields.io/coverage.svg",
        },
    ]

    mock_gl_instance = MagicMock()
    mock_gl_instance.get_group_badges.return_value = fake_badges
    mock_gitlab_connector_class.return_value = mock_gl_instance

    mock_console = MagicMock()
    mock_console_class.return_value = mock_console

    runner = CliRunner()
    result = runner.invoke(group, ['list-badges', '--full-path', 'pl.rachuna-net/app'], obj=ctx_obj)

    mock_gitlab_connector_class.assert_called_once_with(mock_logger)
    mock_gl_instance.get_group_badges.assert_called_once_with('pl.rachuna-net/app')
    assert result.exit_code == 0

    assert mock_console.print.called
    printed_table = mock_console.print.call_args[0][0]

    from io import StringIO
    from rich.console import Console

    string_io = StringIO()
    console = Console(file=string_io, force_terminal=True, width=120)
    console.print(printed_table)
    rendered_output = string_io.getvalue()

    assert "CI Passed" in rendered_output
    assert "Coverage" in rendered_output


@patch("codebase_suite.commands.gitlab.group.GitlabConnector")
@patch("codebase_suite.commands.gitlab.group.Console")
def test_list_ci_command(mock_console_class, mock_gitlab_connector_class):
    mock_logger = MagicMock()

    ctx_obj = MagicMock()
    ctx_obj.logger.return_value = mock_logger

    fake_projects = [
        {
            "id": "gid://gitlab/Project/111",
            "fullPath": "pl.rachuna-net/app/project-a",
            "ciConfigPathOrDefault": ".gitlab-ci.yml"
        },
        {
            "id": "gid://gitlab/Project/222",
            "fullPath": "pl.rachuna-net/app/project-b",
            "ciConfigPathOrDefault": "custom-ci.yml"
        }
    ]

    mock_gl_instance = MagicMock()
    mock_gl_instance.graphql_get_group_projects.return_value = fake_projects
    mock_gitlab_connector_class.return_value = mock_gl_instance

    mock_console = MagicMock()
    mock_console_class.return_value = mock_console

    runner = CliRunner()
    result = runner.invoke(group, ['list-ci', '--full-path', 'pl.rachuna-net/app'], obj=ctx_obj)

    # Assertions
    mock_gitlab_connector_class.assert_called_once_with(mock_logger)
    mock_gl_instance.graphql_get_group_projects.assert_called_once_with('pl.rachuna-net/app')
    assert result.exit_code == 0

    assert mock_console.print.called
    printed_table = mock_console.print.call_args[0][0]

    from io import StringIO
    from rich.console import Console

    string_io = StringIO()
    console = Console(file=string_io, force_terminal=True, width=120)
    console.print(printed_table)
    output = string_io.getvalue()

    assert "project-a" in output
    assert ".gitlab-ci.yml" in output
    assert "project-b" in output
    assert "custom-ci.yml" in output

@patch("codebase_suite.commands.gitlab.group.GitlabConnector")
@patch("codebase_suite.commands.gitlab.group.Console")
def test_list_labels_command(mock_console_class, mock_gitlab_connector_class):
    mock_logger = MagicMock()

    ctx_obj = MagicMock()
    ctx_obj.logger.return_value = mock_logger

    fake_labels = [
        {
            "id": "gid://gitlab/Label/101",
            "color": "#FF0000",
            "title": "bug",
            "description": "Something is not working"
        },
        {
            "id": "gid://gitlab/Label/102",
            "color": "#00FF00",
            "title": "feature",
            "description": "New feature or request"
        }
    ]

    mock_gl_instance = MagicMock()
    mock_gl_instance.graphql_get_group.return_value = {"labels": fake_labels}
    mock_gitlab_connector_class.return_value = mock_gl_instance

    mock_console = MagicMock()
    mock_console_class.return_value = mock_console

    runner = CliRunner()
    result = runner.invoke(group, ['list-labels', '--full-path', 'pl.rachuna-net/app'], obj=ctx_obj)

    # Assertions
    mock_gitlab_connector_class.assert_called_once_with(mock_logger)
    mock_gl_instance.graphql_get_group.assert_called_once_with('pl.rachuna-net/app')
    assert result.exit_code == 0

    assert mock_console.print.called
    printed_table = mock_console.print.call_args[0][0]

    # Render the Rich table to string and verify
    from io import StringIO
    from rich.console import Console

    string_io = StringIO()
    console = Console(file=string_io, force_terminal=True, width=120)
    console.print(printed_table)
    output = string_io.getvalue()

    assert "bug" in output
    assert "feature" in output
    assert "Something is not working" in output
    assert "New feature or request" in output

@patch("codebase_suite.commands.gitlab.group.GitlabConnector")
@patch("codebase_suite.commands.gitlab.group.Console")
def test_list_vars_command(mock_console_class, mock_gitlab_connector_class):
    mock_logger = MagicMock()

    ctx_obj = MagicMock()
    ctx_obj.logger.return_value = mock_logger

    fake_variables = [
        {
            "id": "var_101",
            "key": "SECRET_KEY",
            "value": "s3cr3t",
            "protected": True,
            "masked": False,
            "environmentScope": "*",
            "description": "Main secret"
        },
        {
            "id": "var_102",
            "key": "DEBUG",
            "value": "true",
            "protected": False,
            "masked": True,
            "environmentScope": "dev",
            "description": "Enable debug"
        },
        {
            "id": "var_103",
            "key": "FOO",
            "value": "bar",
            "protected": False,
            "masked": False,
            "environmentScope": "prod",
            "description": ""
        }
    ]

    mock_gl_instance = MagicMock()
    mock_gl_instance.graphql_get_group.return_value = {"ciVariables": fake_variables}
    mock_gitlab_connector_class.return_value = mock_gl_instance

    mock_console = MagicMock()
    mock_console_class.return_value = mock_console

    runner = CliRunner()
    result = runner.invoke(group, ['list-vars', '--full-path', 'pl.rachuna-net/app'], obj=ctx_obj)

    # Assertions
    mock_gitlab_connector_class.assert_called_once_with(mock_logger)
    mock_gl_instance.graphql_get_group.assert_called_once_with('pl.rachuna-net/app')
    assert result.exit_code == 0

    assert mock_console.print.called
    printed_table = mock_console.print.call_args[0][0]

    # Render Rich Table to string and verify contents
    string_io = StringIO()
    console = Console(file=string_io, force_terminal=True, width=120)
    console.print(printed_table)
    output = string_io.getvalue()

    assert "SECRET_KEY" in output
    assert "s3cr3t" in output
    assert "Yes" in output  # protected or masked
    assert "DEBUG" in output
    assert "true" in output
    assert "Enable debug" in output
    assert "FOO" in output
    assert "bar" in output