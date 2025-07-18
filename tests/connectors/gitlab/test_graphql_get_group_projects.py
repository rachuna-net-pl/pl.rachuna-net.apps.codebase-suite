import pytest
from unittest.mock import patch, MagicMock
from codebase_suite.connectors.Gitlab import GitlabConnector


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
def test_graphql_get_group_projects(mock_config_class, mock_gitlab_class, mock_graphql_class, mock_logger, mock_config):
    mock_config_class.return_value = mock_config
    mock_gitlab_client = MagicMock()
    mock_gitlab_class.return_value = mock_gitlab_client

    graphql_mock = MagicMock()
    mock_graphql_class.return_value = graphql_mock

    # Przygotowanie dwóch "stron" wyników (paginacja)
    graphql_mock.execute.side_effect = [
        {
            "group": {
                "projects": {
                    "nodes": [
                        {
                            "id": "gid://gitlab/Project/123",
                            "name": "project-a",
                            "archived": False,
                            "ciConfigPathOrDefault": ".gitlab-ci.yml",
                            "description": "First project",
                            "fullPath": "mygroup/project-a",
                            "visibility": "public",
                            "avatarUrl": None,
                            "topics": ["python"],
                            "branchRules": {
                                "nodes": [
                                    {
                                        "id": "gid://gitlab/Projects::BranchRule/1",
                                        "name": "main",
                                        "isDefault": True,
                                        "branchProtection": {
                                            "pushAccessLevels": {
                                                "nodes": [
                                                    {
                                                        "accessLevelDescription": "Maintainer"
                                                    }
                                                ]
                                            },
                                            "mergeAccessLevels": {
                                                "nodes": [
                                                    {
                                                        "accessLevelDescription": "Developer"
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                ]
                            },
                            "ciVariables": {
                                "nodes": [
                                    {
                                        "id": "gid://gitlab/Ci::Variable/111",
                                        "key": "VAR_A",
                                        "description": "desc A",
                                        "value": "valA",
                                        "protected": True,
                                        "masked": False,
                                        "environmentScope": "*"
                                    }
                                ]
                            },
                            "labels": {
                                "nodes": []
                            }
                        }
                    ],
                    "pageInfo": {
                        "endCursor": "cursor1",
                        "hasNextPage": True
                    }
                }
            }
        },
        {
            "group": {
                "projects": {
                    "nodes": [
                        {
                            "id": "gid://gitlab/Project/124",
                            "name": "project-b",
                            "archived": True,
                            "ciConfigPathOrDefault": ".gitlab-ci.yml",
                            "description": "Second project",
                            "fullPath": "mygroup/project-b",
                            "visibility": "private",
                            "avatarUrl": None,
                            "topics": ["devops"],
                            "branchRules": {
                                "nodes": []
                            },
                            "ciVariables": {
                                "nodes": []
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
                    ],
                    "pageInfo": {
                        "endCursor": None,
                        "hasNextPage": False
                    }
                }
            }
        }
    ]

    connector = GitlabConnector(logger=mock_logger)
    projects = connector.graphql_get_group_projects("mygroup")

    assert len(projects) == 2

    p1 = next(p for p in projects if p["name"] == "project-a")
    assert p1["id"] == "123"
    assert p1["ciVariables"][0]["id"] == "111"
    assert p1["ciVariables"][0]["key"] == "VAR_A"
    assert p1["branchRules"][0]["id"] == "1"
    assert p1["branchRules"][0]["branchProtection"]["pushAccessLevels"][0]["accessLevelDescription"] == "Maintainer"
    assert p1["branchRules"][0]["branchProtection"]["mergeAccessLevels"][0]["accessLevelDescription"] == "Developer"

    p2 = next(p for p in projects if p["name"] == "project-b")
    assert p2["id"] == "124"
    assert p2["ciVariables"] == []
    assert p2["labels"][0]["id"] == "777"
    assert p2["labels"][0]["title"] == "Label1"

    # Sprawdzenie, czy zapytanie było wykonane dwukrotnie (paginacja)
    assert graphql_mock.execute.call_count == 2