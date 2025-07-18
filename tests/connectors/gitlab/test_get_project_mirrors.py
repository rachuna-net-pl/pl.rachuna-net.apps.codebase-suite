import pytest
import gitlab
from unittest.mock import patch, MagicMock
from unittest.mock import ANY

from codebase_suite.connectors.Gitlab import GitlabConnector
from codebase_suite.connectors.Gitlab.Exceptions import GitlabInstanceUnavailableException, GitlabGraphQLUnavailableException
from codebase_suite.connectors.Gitlab.Graphql import *


@pytest.fixture
def mock_logger():
    return MagicMock()

@pytest.fixture
def mock_config():
    mock = MagicMock()
    mock.gitlab_url = "https://gitlab.example.com"
    mock.gitlab_token.get_secret_value.return_value = "secret-token"
    mock.ssl_verify = False
    mock.api_version = "4"
    return mock

@pytest.fixture
def mock_gitlab_client():
    mock = MagicMock()
    mock.auth.return_value = True
    return mock


@patch("codebase_suite.connectors.Gitlab.GitlabConnector.gitlab.Gitlab")
@patch("codebase_suite.connectors.Gitlab.GitlabConnector.Config")
def test_get_project_mirrors(mock_config_class, mock_gitlab_class, mock_logger, mock_config):
    # Arrange
    mock_config_class.return_value = mock_config
    mock_gitlab_client = MagicMock()
    mock_gitlab_class.return_value = mock_gitlab_client

    project_path = "my-group/my-project"
    expected_mirrors = [MagicMock(), MagicMock()]

    mock_project = MagicMock()
    mock_project.remote_mirrors.list.return_value = expected_mirrors
    mock_gitlab_client.projects.get.return_value = mock_project

    connector = GitlabConnector(logger=mock_logger)

    # Act
    result = connector.get_project_mirrors(project_path)

    # Assert
    assert result == expected_mirrors
    mock_gitlab_client.projects.get.assert_called_once_with(project_path)
    mock_project.remote_mirrors.list.assert_called_once()