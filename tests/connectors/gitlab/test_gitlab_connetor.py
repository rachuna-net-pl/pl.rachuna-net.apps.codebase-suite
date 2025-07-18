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

@pytest.fixture
def mock_graphql():
    mock = MagicMock()
    mock.execute.return_value = {
        "project": {
            "id": "gid://gitlab/Project/123",
            "ciVariables": {
                "nodes": [
                    {"id": "gid://gitlab/Ci::Variable/111", "key": "TOKEN", "value": "abc", "environmentScope": "*", "protected": False}
                ]
            }
        },
        "group": {
            "id": "gid://gitlab/Group/456",
            "ciVariables": {
                "nodes": [
                    {"id": "gid://gitlab/Ci::GroupVariable/222", "key": "VAR", "value": "def", "environmentScope": "*", "protected": False}
                ]
            }
        }
    }
    return mock

@patch("codebase_suite.connectors.Gitlab.GitlabConnector.gitlab.GraphQL")
@patch("codebase_suite.connectors.Gitlab.GitlabConnector.gitlab.Gitlab")
@patch("codebase_suite.connectors.Gitlab.GitlabConnector.Config")
def test_init_success(mock_config_class, mock_gitlab_class, mock_graphql_class, mock_logger, mock_config, mock_gitlab_client, mock_graphql):
    mock_config_class.return_value = mock_config
    mock_gitlab_class.return_value = mock_gitlab_client
    mock_graphql_class.return_value = mock_graphql

    connector = GitlabConnector(logger=mock_logger)

    assert connector._GitlabConnector__client == mock_gitlab_client
    assert connector._GitlabConnector__graphql == mock_graphql
    mock_logger.debug.assert_called_with("✔️  Authorization in Gitlab GRAPHQL successful.")

@patch("codebase_suite.connectors.Gitlab.GitlabConnector.gitlab.GraphQL")
@patch("codebase_suite.connectors.Gitlab.GitlabConnector.gitlab.Gitlab")
@patch("codebase_suite.connectors.Gitlab.GitlabConnector.Config")
def test_init_auth_fail(mock_config_class, mock_gitlab_class, mock_graphql_class, mock_logger, mock_config):
    mock_config_class.return_value = mock_config
    mock_client = MagicMock()
    mock_client.auth.side_effect = gitlab.exceptions.GitlabAuthenticationError("Auth failed")
    mock_gitlab_class.return_value = mock_client
    mock_graphql_class.return_value = MagicMock()

    with pytest.raises(GitlabInstanceUnavailableException):
        GitlabConnector(logger=mock_logger)

@patch("codebase_suite.connectors.Gitlab.GitlabConnector.gitlab.GraphQL")
@patch("codebase_suite.connectors.Gitlab.GitlabConnector.gitlab.Gitlab")
@patch("codebase_suite.connectors.Gitlab.GitlabConnector.Config")
def test_init_graphql_fail(mock_config_class, mock_gitlab_class, mock_graphql_class, mock_logger, mock_config):
    mock_config_class.return_value = mock_config

    # Konfiguracja klienta Gitlab API działa
    mock_gitlab_client = MagicMock()
    mock_gitlab_client.auth.return_value = True
    mock_gitlab_class.return_value = mock_gitlab_client

    # GraphQL rzuca wyjątek
    mock_graphql_class.side_effect = Exception("GraphQL error")

    with pytest.raises(GitlabGraphQLUnavailableException) as exc_info:
        GitlabConnector(logger=mock_logger)

    assert "GraphQL error" in str(exc_info.value)
    mock_logger.error.assert_called_with("❌  Authorization Gitlab GRAPHQL failed. Please check your configuration.") 

@patch("codebase_suite.connectors.Gitlab.GitlabConnector.gitlab.GraphQL")
@patch("codebase_suite.connectors.Gitlab.GitlabConnector.gitlab.Gitlab")
@patch("codebase_suite.connectors.Gitlab.GitlabConnector.Config")
@patch("codebase_suite.connectors.Gitlab.GitlabConnector.Logger")
def test_init_default_logger_used(
    mock_logger_class,
    mock_config_class,
    mock_gitlab_class,
    mock_graphql_class,
    mock_config,
    mock_gitlab_client,
    mock_graphql
):
    # Przygotuj mocki
    mock_logger_instance = MagicMock()
    mock_logger_class.return_value = mock_logger_instance
    mock_config_class.return_value = mock_config
    mock_gitlab_class.return_value = mock_gitlab_client
    mock_graphql_class.return_value = mock_graphql

    # Uruchom konstruktor bez podania loggera
    connector = GitlabConnector()

    # Sprawdź, że Logger został utworzony
    mock_logger_class.assert_called_once()
    assert connector._GitlabConnector__logger == mock_logger_instance

