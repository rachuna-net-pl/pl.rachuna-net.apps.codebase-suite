import pytest
import click
from unittest.mock import MagicMock, patch, ANY
from pathlib import Path
from click.testing import CliRunner

from codebase_suite.commands.terraform.generate.gitlab import (
    gitlab,
    generate_group,
    generate_project,
    groups
)

# === Fixtures ===

@pytest.fixture
def ctx_mock():
    logger = MagicMock()
    config = MagicMock()
    config.templates_dir = Path("/templates")

    mock = MagicMock()
    mock.logger.return_value = logger
    mock.get_config.return_value = config
    return mock

@pytest.fixture
def fake_group():
    return {
        "fullPath": "pl.rachuna-net/group",
        "name": "Fake Group"
    }

@pytest.fixture
def fake_project():
    return {
        "fullPath": "pl.rachuna-net/group/project",
        "name": "Fake Project"
    }

# === Tests for generate_group ===

@patch("codebase_suite.commands.terraform.generate.gitlab.GitlabGroup")
@patch("codebase_suite.commands.terraform.generate.gitlab.GitlabConnector")
def test_generate_group_hcl(GitlabConnectorMock, GitlabGroupMock, ctx_mock, fake_group):
    gl = GitlabConnectorMock.return_value
    gl.graphql_get_group.return_value = fake_group
    gl.get_group_badges.return_value = []

    generator = GitlabGroupMock.return_value

    generate_group(
        ctx=ctx_mock,
        gl = gl,
        full_path=fake_group["fullPath"],
        repository_path=Path("/repo"),
        template_path=None,
        force=True,
        json=False
    )

    gl.graphql_get_group.assert_called_once_with(fake_group["fullPath"])
    generator.generate_hcl.assert_called_once_with(True)


@patch("codebase_suite.commands.terraform.generate.gitlab.GitlabGroup")
@patch("codebase_suite.commands.terraform.generate.gitlab.GitlabConnector")
def test_generate_group_json(GitlabConnectorMock, GitlabGroupMock, ctx_mock, fake_group):
    gl = GitlabConnectorMock.return_value
    gl.graphql_get_group.return_value = fake_group
    gl.get_group_badges.return_value = []

    generator = GitlabGroupMock.return_value

    generate_group(
        ctx=ctx_mock,
        gl = gl,
        full_path=fake_group["fullPath"],
        repository_path=Path("/repo"),
        template_path=None,
        force=False,
        json=True
    )

    generator.generate_json.assert_called_once_with(False)

# === Tests for generate_project ===

@patch("codebase_suite.commands.terraform.generate.gitlab.GitlabProject")
@patch("codebase_suite.commands.terraform.generate.gitlab.GitlabConnector")
def test_generate_project_hcl(GitlabConnectorMock, GitlabProjectMock, ctx_mock, fake_project):
    gl = GitlabConnectorMock.return_value
    gl.graphql_get_project.return_value = fake_project
    gl.get_project_badges.return_value = []
    gl.get_project_protected_tags.return_value = []

    generator = GitlabProjectMock.return_value

    generate_project(
        ctx=ctx_mock,
        gl = gl,
        full_path=fake_project["fullPath"],
        repository_path=Path("/repo"),
        template_path=None,
        force=True,
        json=False
    )

    generator.generate_hcl.assert_called_once_with(True)


@patch("codebase_suite.commands.terraform.generate.gitlab.GitlabProject")
@patch("codebase_suite.commands.terraform.generate.gitlab.GitlabConnector")
def test_generate_project_json(GitlabConnectorMock, GitlabProjectMock, ctx_mock, fake_project):
    gl = GitlabConnectorMock.return_value
    gl.graphql_get_project.return_value = fake_project
    gl.get_project_badges.return_value = []
    gl.get_project_protected_tags.return_value = ["v1.0"]

    generator = GitlabProjectMock.return_value

    generate_project(
        ctx=ctx_mock,
        gl = gl,
        full_path=fake_project["fullPath"],
        repository_path=Path("/repo"),
        template_path=None,
        force=False,
        json=True
    )

    generator.generate_json.assert_called_once_with(False)

@patch("codebase_suite.commands.terraform.generate.gitlab.generate_project")
@patch("codebase_suite.commands.terraform.generate.gitlab.generate_group")
@patch("codebase_suite.commands.terraform.generate.gitlab.GitlabConnector")
def test_groups_command(GitlabConnectorMock, generate_group_mock, generate_project_mock, fake_group, fake_project):
    gl = GitlabConnectorMock.return_value
    gl.graphql_get_descendantGroups.return_value = [fake_group]
    gl.graphql_get_group_projects.return_value = [fake_project]

    runner = CliRunner()
    result = runner.invoke(
        gitlab,
        [
            "groups",
            "-p", "pl.rachuna-net/group",
            "-r", "/repo"
        ],
        obj=MagicMock()
    )

    assert result.exit_code == 0
    assert generate_group_mock.call_count == 2
    generate_project_mock.assert_called_once()
    

@patch("codebase_suite.commands.terraform.generate.gitlab.generate_project")
@patch("codebase_suite.commands.terraform.generate.gitlab.GitlabConnector")
def test_project_command_calls_generate_project(mock_gitlab_connector, mock_generate_project):
    runner = CliRunner()

    mock_logger = MagicMock()
    mock_config = MagicMock()
    mock_config.templates_dir = Path("/templates")

    class DummyObj:
        def logger(self):
            return mock_logger
        def get_config(self):
            return mock_config

    dummy_obj = DummyObj()
    mock_gitlab_connector.return_value = MagicMock()

    result = runner.invoke(
        gitlab,
        [
            "project",
            "-p", "pl.rachuna-net/my-project",
            "-r", "/repo",
            "-f",
            "--json"
        ],
        obj=dummy_obj
    )

    # Walidacja
    assert result.exit_code == 0
    mock_generate_project.assert_called_once()

    args, _ = mock_generate_project.call_args

    assert isinstance(args[0], click.Context)
    assert isinstance(args[1], MagicMock)    
    assert args[2] == "pl.rachuna-net/my-project"
    assert args[3] == Path("/repo")              
    assert args[4] is None                       
    assert args[5] is True                       
    assert args[6] is True                       


@patch("codebase_suite.commands.terraform.generate.gitlab.generate_group")
@patch("codebase_suite.commands.terraform.generate.gitlab.GitlabConnector")
def test_group_command_calls_generate_group(mock_gitlab_connector, mock_generate_group):
    from codebase_suite.commands.terraform.generate.gitlab import gitlab

    runner = CliRunner()

    # Przygotuj mocki
    mock_logger = MagicMock()
    mock_config = MagicMock()
    mock_config.templates_dir = Path("/templates")

    # Dummy obiekt ctx.obj
    class DummyObj:
        def logger(self):
            return mock_logger
        def get_config(self):
            return mock_config

    dummy_obj = DummyObj()
    mock_gitlab_connector.return_value = MagicMock()

    # Wywołanie CLI
    result = runner.invoke(
        gitlab,
        [
            "group",
            "-p", "pl.rachuna-net/my-group",
            "-r", "/repo",
            "--json"
        ],
        obj=dummy_obj
    )

    # Walidacja
    assert result.exit_code == 0
    mock_generate_group.assert_called_once()

    args, _ = mock_generate_group.call_args

    assert isinstance(args[0], click.Context)                  # ctx
    assert isinstance(args[1], MagicMock)                      # gl
    assert args[2] == "pl.rachuna-net/my-group"                # full_path
    assert args[3] == Path("/repo")                            # repository_path
    assert args[4] is None                                     # template_path
    assert args[5] is False                                    # force
    assert args[6] is True                                     # json

