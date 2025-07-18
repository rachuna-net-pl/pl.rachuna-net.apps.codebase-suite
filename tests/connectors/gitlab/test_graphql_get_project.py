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
def test_graphql_get_project(mock_config_class, mock_gitlab_class, mock_graphql_class, mock_logger, mock_config):
    mock_config_class.return_value = mock_config
    mock_gitlab_client = MagicMock()
    mock_gitlab_client.auth.return_value = True
    mock_gitlab_class.return_value = mock_gitlab_client

    graphql_mock = MagicMock()
    graphql_mock.execute.return_value = {
        "project": {
            "id": "gid://gitlab/Project/321",
            "name": "myproject",
            "archived": False,
            "ciConfigPathOrDefault": ".gitlab-ci.yml",
            "description": "Example project",
            "fullPath": "mygroup/myproject",
            "visibility": "private",
            "avatarUrl": "http://example.com/avatar.png",
            "topics": ["ci", "automation", "infra"],
            "branchRules": {
                "nodes": [
                    {
                        "id": "gid://gitlab/Projects::BranchRule/111",
                        "name": "main",
                        "isDefault": True,
                        "branchProtection": {
                            "allowForcePush": True,
                            "pushAccessLevels": {
                                "nodes": [
                                    {"accessLevel": 40, "accessLevelDescription": "Maintainer"}
                                ]
                            },
                            "mergeAccessLevels": {
                                "nodes": [
                                    {"accessLevel": 30, "accessLevelDescription": "Developer"}
                                ]
                            }
                        }
                    }
                ]
            },
            "ciVariables": {
                "nodes": [
                    {
                        "id": "gid://gitlab/Ci::Variable/999",
                        "key": "FOO",
                        "description": "test var",
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
                        "id": "gid://gitlab/GroupLabel/777",
                        "color": "#FFFFFF",
                        "description": "Test label",
                        "title": "Label1"
                    }
                ]
            }
        }
    }
    mock_graphql_class.return_value = graphql_mock

    connector = GitlabConnector(logger=mock_logger)

    project_data = connector.graphql_get_project("mygroup/myproject")

    assert project_data['id'] == "321"
    assert project_data['name'] == "myproject"
    assert project_data['archived'] is False
    assert project_data['ciConfigPathOrDefault'] == ".gitlab-ci.yml"
    assert project_data['description'] == "Example project"
    assert project_data['fullPath'] == "mygroup/myproject"
    assert project_data['visibility'] == "private"
    assert project_data['avatarUrl'] == "http://example.com/avatar.png"
    assert "infra" in project_data['topics']

    # branchRules
    assert len(project_data['branchRules']) == 1
    rule = project_data['branchRules'][0]
    assert rule['id'] == "111"
    assert rule['name'] == "main"
    assert rule['isDefault'] is True

    # branchProtection
    protection = rule['branchProtection']
    assert protection is not None
    assert protection['allowForcePush'] is True
    assert protection['pushAccessLevels'][0]['accessLevel'] == 40
    assert protection['pushAccessLevels'][0]['accessLevelDescription'] == "Maintainer"
    assert protection['mergeAccessLevels'][0]['accessLevel'] == 30
    assert protection['mergeAccessLevels'][0]['accessLevelDescription'] == "Developer"

    # ciVariables
    ci_var = project_data['ciVariables'][0]
    assert ci_var['id'] == "999"
    assert ci_var['key'] == "FOO"
    assert ci_var['value'] == "bar"
    assert ci_var['description'] == "test var"
    assert ci_var['protected'] is False
    assert ci_var['masked'] is True
    assert ci_var['environmentScope'] == "*"

    # labels
    label = project_data['labels'][0]
    assert label['id'] == "777"
    assert label['color'] == "#FFFFFF"
    assert label['description'] == "Test label"
    assert label['title'] == "Label1"

    graphql_mock.execute.assert_called_once()