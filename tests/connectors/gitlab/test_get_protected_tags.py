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
def test_get_project_protected_tags(mock_config_class, mock_gitlab_class, mock_config, mock_logger):
    # Przygotowanie konfiguracji
    mock_config_class.return_value = mock_config
    mock_gitlab_client = MagicMock()
    mock_gitlab_class.return_value = mock_gitlab_client

    # Dane testowe
    expected_tags = [
        {
            'name': 'v1.*',
            'create_access_levels': [{'access_level': 40}]
        },
        {
            'name': 'release-*',
            'create_access_levels': [{'access_level': 30}]
        }
    ]

    # Tworzenie mocków dla tagów
    mock_tag1 = MagicMock()
    mock_tag1.attributes = expected_tags[0]
    mock_tag2 = MagicMock()
    mock_tag2.attributes = expected_tags[1]

    mock_protectedtags = MagicMock()
    mock_protectedtags.list.return_value = [mock_tag1, mock_tag2]

    mock_project = MagicMock()
    mock_project.protectedtags = mock_protectedtags
    mock_gitlab_client.projects.get.return_value = mock_project

    # Inicjalizacja testowanego obiektu
    connector = GitlabConnector(logger=mock_logger)

    # Ustawienie prywatnego klienta (jeśli nie chcesz zmieniać klasy produkcyjnej)
    connector._client = mock_gitlab_client

    # Wywołanie metody
    result = connector.get_project_protected_tags("mygroup/myproject")

    # Assercje
    assert result == expected_tags
    mock_gitlab_client.projects.get.assert_called_once_with("mygroup/myproject")
    mock_protectedtags.list.assert_called_once_with(all=True)