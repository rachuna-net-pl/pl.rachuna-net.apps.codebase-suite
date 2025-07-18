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
def test_graphql_get_descendant_groups(mock_config_class, mock_gitlab_class, mock_graphql_class, mock_logger, mock_config):
    mock_config_class.return_value = mock_config
    mock_gitlab_client = MagicMock()
    mock_gitlab_class.return_value = mock_gitlab_client

    graphql_mock = MagicMock()
    mock_graphql_class.return_value = graphql_mock

    graphql_mock.execute.side_effect = [
        {
            "group": {
                "descendantGroups": {
                    "nodes": [
                        {
                            "id": "gid://gitlab/Group/101",
                            "name": "child-group-a",
                            "fullPath": "mygroup/child-a",
                            "description": "Child A",
                            "visibility": "private",
                            "avatarUrl": None,
                            "labels": {
                                "nodes": [
                                    {
                                        "id": "gid://gitlab/GroupLabel/201",
                                        "color": "#ffffff",
                                        "description": "Test label",
                                        "title": "Label A"
                                    }
                                ]
                            },
                            "ciVariables": {
                                "nodes": [
                                    {
                                        "id": "gid://gitlab/Ci::GroupVariable/301",
                                        "key": "GROUP_VAR",
                                        "description": "Group variable",
                                        "value": "value",
                                        "protected": False,
                                        "masked": True,
                                        "environmentScope": "*"
                                    }
                                ]
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
                "descendantGroups": {
                    "nodes": [
                        {
                            "id": "gid://gitlab/Group/102",
                            "name": "child-group-b",
                            "fullPath": "mygroup/child-b",
                            "description": "Child B",
                            "visibility": "internal",
                            "avatarUrl": None,
                            "labels": {
                                "nodes": []
                            },
                            "ciVariables": {
                                "nodes": []
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
    groups = connector.graphql_get_descendantGroups("mygroup")

    assert len(groups) == 2

    g1 = next(g for g in groups if g["name"] == "child-group-a")
    assert g1["id"] == "101"
    assert g1["ciVariables"][0]["id"] == "301"
    assert g1["labels"][0]["id"] == "201"
    assert g1["fullPath"] == "mygroup/child-a"

    g2 = next(g for g in groups if g["name"] == "child-group-b")
    assert g2["id"] == "102"
    assert g2["ciVariables"] == []
    assert g2["labels"] == []

    assert graphql_mock.execute.call_count == 2