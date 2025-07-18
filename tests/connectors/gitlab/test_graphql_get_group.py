import pytest
from unittest.mock import patch, MagicMock
from codebase_suite.connectors.Gitlab import GitlabConnector
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

@patch("codebase_suite.connectors.Gitlab.GitlabConnector.gitlab.GraphQL")
@patch("codebase_suite.connectors.Gitlab.GitlabConnector.gitlab.Gitlab")
@patch("codebase_suite.connectors.Gitlab.GitlabConnector.Config")
def test_graphql_get_group_full_response(mock_config_class, mock_gitlab_class, mock_graphql_class, mock_logger, mock_config):
    mock_config_class.return_value = mock_config
    mock_gitlab_client = MagicMock()
    mock_gitlab_client.auth.return_value = True
    mock_gitlab_class.return_value = mock_gitlab_client

    graphql_mock = MagicMock()
    graphql_mock.execute.return_value = {
        "group": {
            "id": "gid://gitlab/Group/456",
            "name": "mygroup",
            "fullPath": "mygroup",
            "description": "Test group description",
            "visibility": "private",
            "avatarUrl": "http://example.com/avatar.png",
            "ciVariables": {
                "nodes": [
                    {
                        "id": "gid://gitlab/Ci::GroupVariable/999",
                        "key": "FOO",
                        "description": "Test variable",
                        "value": "bar",
                        "protected": False,
                        "masked": True,
                        "environmentScope": "*"
                    }
                ]
            },
            "labels": {
                "nodes": [
                    {
                        "id": "gid://gitlab/GroupLabel/321",
                        "color": "#FF0000",
                        "description": "Important label",
                        "title": "critical"
                    },
                    {
                        "id": "gid://gitlab/GroupLabel/322",
                        "color": "#00FF00",
                        "description": "Minor issue",
                        "title": "minor"
                    }
                ]
            }
        }
    }
    mock_graphql_class.return_value = graphql_mock

    connector = GitlabConnector(logger=mock_logger)
    group_data = connector.graphql_get_group("mygroup")

    assert group_data['id'] == "456"
    assert group_data['name'] == "mygroup"
    assert group_data['fullPath'] == "mygroup"
    assert group_data['description'] == "Test group description"
    assert group_data['visibility'] == "private"
    assert group_data['avatarUrl'] == "http://example.com/avatar.png"

    # Check CI Variables
    ci_var = group_data['ciVariables'][0]
    assert ci_var['id'] == "999"
    assert ci_var['key'] == "FOO"
    assert ci_var['value'] == "bar"
    assert ci_var['description'] == "Test variable"
    assert ci_var['protected'] is False
    assert ci_var['masked'] is True
    assert ci_var['environmentScope'] == "*"

    # Check Labels
    assert len(group_data['labels']) == 2

    label1 = group_data['labels'][0]
    assert label1['id'] == "321"
    assert label1['title'] == "critical"
    assert label1['color'] == "#FF0000"
    assert label1['description'] == "Important label"

    label2 = group_data['labels'][1]
    assert label2['id'] == "322"
    assert label2['title'] == "minor"
    assert label2['color'] == "#00FF00"
    assert label2['description'] == "Minor issue"

    graphql_mock.execute.assert_called_once()