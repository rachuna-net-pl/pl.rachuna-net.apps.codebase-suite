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
def test_get_group_badges(mock_config_class, mock_gitlab_class, mock_logger, mock_config):
    mock_config_class.return_value = mock_config
    mock_gitlab_client = MagicMock()
    mock_gitlab_class.return_value = mock_gitlab_client

    expected_badges = [
        {
            'group_id': '105046057',
            'name': 'pipeline',
            'link_url': 'https://gitlab.com/%{project_path}/-/commits/%{default_branch}',
            'image_url': 'https://gitlab.com/%{project_path}/badges/%{default_branch}/pipeline.svg',
            'rendered_link_url': 'https://gitlab.com/pl.rachuna-net/docs/-/commits/main',
            'rendered_image_url': 'https://gitlab.com/pl.rachuna-net/docs/badges/main/pipeline.svg',
            'id': 6062085,
            'kind': 'group',
        },
        {
            'group_id': '105046057',
            'name': 'release',
            'link_url': 'https://gitlab.com/%{project_path}/-/releases',
            'image_url': 'https://gitlab.com/%{project_path}/-/badges/release.svg',
            'rendered_link_url': 'https://gitlab.com/pl.rachuna-net/docs/-/releases',
            'rendered_image_url': 'https://gitlab.com/pl.rachuna-net/docs/-/badges/release.svg',
            'id': 6062086,
            'kind': 'group',
        },
    ]

    mock_badge1 = MagicMock()
    mock_badge1.attributes = expected_badges[0]
    mock_badge2 = MagicMock()
    mock_badge2.attributes = expected_badges[1]

    mock_badges = MagicMock()
    mock_badges.list.return_value = [mock_badge1, mock_badge2]

    mock_group = MagicMock()
    mock_group.badges = mock_badges
    mock_gitlab_client.groups.get.return_value = mock_group

    connector = GitlabConnector(logger=mock_logger)

    result = connector.get_group_badges("mygroup")

    assert result == expected_badges
    mock_gitlab_client.groups.get.assert_called_once_with("mygroup")
    mock_badges.list.assert_called_once_with(all=True)
