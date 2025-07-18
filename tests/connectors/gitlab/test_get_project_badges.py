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
def test_get_project_badges(mock_config_class, mock_gitlab_class, mock_logger, mock_config):
    mock_config_class.return_value = mock_config
    mock_gitlab_client = MagicMock()
    mock_gitlab_class.return_value = mock_gitlab_client

    expected_badges = [
        {
            'project_id': '12345',
            'name': 'coverage',
            'link_url': 'https://gitlab.com/%{project_path}/-/pipelines',
            'image_url': 'https://gitlab.com/%{project_path}/badges/coverage.svg',
            'rendered_link_url': 'https://gitlab.com/mygroup/myproject/-/pipelines',
            'rendered_image_url': 'https://gitlab.com/mygroup/myproject/badges/coverage.svg',
            'id': 1234567,
            'kind': 'project',
        },
        {
            'project_id': '12345',
            'name': 'build',
            'link_url': 'https://gitlab.com/%{project_path}/-/jobs',
            'image_url': 'https://gitlab.com/%{project_path}/badges/build.svg',
            'rendered_link_url': 'https://gitlab.com/mygroup/myproject/-/jobs',
            'rendered_image_url': 'https://gitlab.com/mygroup/myproject/badges/build.svg',
            'id': 1234568,
            'kind': 'project',
        },
    ]

    mock_badge1 = MagicMock()
    mock_badge1.attributes = expected_badges[0]
    mock_badge2 = MagicMock()
    mock_badge2.attributes = expected_badges[1]

    mock_badges = MagicMock()
    mock_badges.list.return_value = [mock_badge1, mock_badge2]

    mock_project = MagicMock()
    mock_project.badges = mock_badges
    mock_gitlab_client.projects.get.return_value = mock_project

    connector = GitlabConnector(logger=mock_logger)

    result = connector.get_project_badges("mygroup/myproject")

    assert result == expected_badges
    mock_gitlab_client.projects.get.assert_called_once_with("mygroup/myproject")
    mock_badges.list.assert_called_once_with(all=True)