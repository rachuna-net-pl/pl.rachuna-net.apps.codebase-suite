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


@patch("codebase_suite.connectors.Gitlab.GitlabConnector.gitlab.GraphQL")
@patch("codebase_suite.connectors.Gitlab.GitlabConnector.gitlab.Gitlab")
@patch("codebase_suite.connectors.Gitlab.GitlabConnector.Config")
def test_get_project_inherited_variables(mock_config_class, mock_gitlab_class, mock_graphql_class, mock_logger, mock_config):
    mock_config_class.return_value = mock_config
    mock_gitlab_client = MagicMock()
    mock_gitlab_client.auth.return_value = True
    mock_gitlab_class.return_value = mock_gitlab_client

    mock_graphql_class.return_value = MagicMock()

    connector = GitlabConnector(logger=mock_logger)

    connector.graphql_get_group = MagicMock(return_value={
        "ciVariables": [
            {
                "id": "1",
                "key": "TOKEN",
                "value": "group-value",
                "environmentScope": "*",
                "protected": False
            }
        ]
    })

    connector.graphql_get_project = MagicMock(return_value={
        "ciVariables": [
            {
                "id": "2",
                "key": "TOKEN",
                "value": "project-value",
                "environmentScope": "*",
                "protected": False
            }
        ]
    })

    variables = connector.get_project_inherited_variables("mygroup/myproject")

    assert isinstance(variables, dict)
    assert any("TOKEN:*:False" in key for key in variables.keys())
    assert variables["TOKEN:*:False"]["value"] == "project-value"
