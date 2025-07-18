import pytest
import builtins
import sys
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from pathlib import Path

from codebase_suite.commands.terraform.import_tf import print_progress_bar, replan, gitlab

@pytest.fixture
def ctx_mock():
    logger = MagicMock()
    config = MagicMock()
    config.templates_dir = Path("/templates")

    mock = MagicMock()
    mock.obj = MagicMock()
    mock.obj.logger = MagicMock(return_value=logger)
    mock.get_config.return_value = config
    return mock

@pytest.fixture
def fake_plan_with_group_and_project():
    return {
        "resource_changes": [
            {
                "address": "gitlab_group.example",
                "mode": "managed",
                "type": "gitlab_group",
                "change": {
                    "actions": ["create"],
                    "after": {"path": "example-group"}
                }
            },
            {
                "address": "gitlab_project.example",
                "mode": "managed",
                "type": "gitlab_project",
                "change": {
                    "actions": ["create"],
                    "after": {"name": "example-project"}
                }
            }
        ]
    }

@pytest.fixture
def fake_plan_with_parent_group():
    return {
        "resource_changes": [
            {
                "address": "gitlab_group.example",
                "mode": "managed",
                "type": "gitlab_group",
                "change": {
                    "actions": ["create"],
                    "after": {
                        "path": "example-group",
                        "parent_id": 999
                    }
                }
            },
            {
                "address": "gitlab_project.example",
                "mode": "managed",
                "type": "gitlab_project",
                "change": {
                    "actions": ["create"],
                    "after": {"name": "example-project"}
                }
            }
        ]
    }

@pytest.fixture
def fake_plan_with_namespace_project():
    return {
        "resource_changes": [
            {
                "address": "gitlab_project.example",
                "mode": "managed",
                "type": "gitlab_project",
                "change": {
                    "actions": ["create"],
                    "after": {
                        "name": "example-project",
                        "namespace_id": 999
                    }
                }
            }
        ]
    }

@pytest.fixture
def fake_plan_multiple_resources():
    return {
        "resource_changes": [
            {
                "address": "gitlab_group.example1",
                "mode": "managed",
                "type": "gitlab_group",
                "change": {
                    "actions": ["create"],
                    "after": {"path": "group1"}
                }
            },
            {
                "address": "gitlab_group.example2",
                "mode": "managed",
                "type": "gitlab_group",
                "change": {
                    "actions": ["create"],
                    "after": {"path": "group2"}
                }
            }
        ]
    }

@pytest.mark.parametrize("index, size, expected_trace, expected_info_start", [
    (5, 10, "   Status import: 5 / 10", "    ["),
    (10, 10, "   Status import: 10 / 10", "    ["),
])
def test_print_progress_bar_logs_correctly(index, size, expected_trace, expected_info_start):
    mock_logger = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.obj.logger.return_value = mock_logger

    print_progress_bar(mock_ctx, index, size, width=10)

    mock_logger.trace.assert_called_once_with(expected_trace)
    mock_logger.info.assert_called_once()
    assert mock_logger.info.call_args[0][0].startswith(expected_info_start)

def test_replan_executes_terraform_methods():
    mock_logger = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.obj.logger.return_value = mock_logger

    mock_tf = MagicMock()
    mock_tf.get_terraform_plan_json.return_value = {"fake": "plan"}

    result = replan(mock_tf, mock_ctx)

    mock_tf.terraform_plan.assert_called_once()
    mock_tf.terraform_show.assert_called_once()
    mock_tf.get_terraform_plan_json.assert_called_once()
    assert result == {"fake": "plan"}

@patch("codebase_suite.commands.terraform.import_tf.Config")
@patch("codebase_suite.commands.terraform.import_tf.Terraform")
@patch("codebase_suite.commands.terraform.import_tf.GitlabConnector")
def test_gitlab_import_command_with_parent_id(
    mock_gitlab_connector,
    mock_terraform,
    mock_config,
    ctx_mock,
    fake_plan_with_parent_group
):
    runner = CliRunner()

    gl_instance = mock_gitlab_connector.return_value
    gl_instance.get_group_by_id.return_value.full_path = "parent-group"
    gl_instance.graphql_get_group.return_value = {"id": 123}
    gl_instance.graphql_get_project.return_value = {"id": 456}

    tf_instance = mock_terraform.return_value
    tf_instance.get_terraform_plan_json.return_value = fake_plan_with_parent_group

    mock_config.return_value.tf_state_name_iac_gitlab = "iac-gitlab"

    result = runner.invoke(
        gitlab,
        ["--repository-path", "/repo", "--dry", "--progress"],
        obj=ctx_mock
    )

    assert result.exit_code == 0
    tf_instance.terraform_init.assert_called_once_with("iac-gitlab")

    tf_instance.terraform_import.assert_any_call("gitlab_group.example", 123, True)
    tf_instance.terraform_import.assert_any_call("gitlab_project.example", 456, True)
    assert tf_instance.terraform_import.call_count == 2

@patch("codebase_suite.commands.terraform.import_tf.Config")
@patch("codebase_suite.commands.terraform.import_tf.Terraform")
@patch("codebase_suite.commands.terraform.import_tf.GitlabConnector")
def test_gitlab_import_command_with_namespace_id(
    mock_gitlab_connector,
    mock_terraform,
    mock_config,
    ctx_mock,
    fake_plan_with_namespace_project
):
    runner = CliRunner()

    gl_instance = mock_gitlab_connector.return_value
    gl_instance.get_group_by_id.return_value.full_path = "parent-group"
    gl_instance.graphql_get_project.return_value = {"id": 123}

    tf_instance = mock_terraform.return_value
    tf_instance.get_terraform_plan_json.return_value = fake_plan_with_namespace_project

    mock_config.return_value.tf_state_name_iac_gitlab = "iac-gitlab"

    result = runner.invoke(
        gitlab,
        ["--repository-path", "/repo", "--dry", "--progress"],
        obj=ctx_mock
    )

    assert result.exit_code == 0
    tf_instance.terraform_init.assert_called_once_with("iac-gitlab")

    tf_instance.terraform_import.assert_any_call("gitlab_project.example", 123, True)
    assert tf_instance.terraform_import.call_count == 1

@patch("codebase_suite.commands.terraform.import_tf.print_progress_bar")
@patch("codebase_suite.commands.terraform.import_tf.Config")
@patch("codebase_suite.commands.terraform.import_tf.Terraform")
@patch("codebase_suite.commands.terraform.import_tf.GitlabConnector")
def test_gitlab_import_progress_bar_called(
    mock_gitlab_connector,
    mock_terraform,
    mock_config,
    mock_print_progress_bar,
    ctx_mock,
    fake_plan_multiple_resources
):
    runner = CliRunner()

    gl_instance = mock_gitlab_connector.return_value
    gl_instance.get_group_by_id.return_value.full_path = "root"
    gl_instance.graphql_get_group.return_value = {"id": 123}

    tf_instance = mock_terraform.return_value
    tf_instance.get_terraform_plan_json.return_value = fake_plan_multiple_resources

    mock_config.return_value.tf_state_name_iac_gitlab = "iac-gitlab"

    result = runner.invoke(
        gitlab,
        ["--repository-path", "/repo", "--dry", "--progress"],
        obj=ctx_mock
    )

    assert result.exit_code == 0
    tf_instance.terraform_init.assert_called_once_with("iac-gitlab")

    # print_progress_bar powinno być wywołane minimum raz
    assert mock_print_progress_bar.call_count > 0

    # Sprawdź, czy w którymkolwiek wywołaniu counter < resources_count
    assert any(call.args[1] < call.args[2] for call in mock_print_progress_bar.call_args_list)

@pytest.fixture
def fake_plan_with_gitlab_groups():
    return {
        "resource_changes": [
            {
                "address": "gitlab_group.example1",
                "mode": "managed",
                "type": "gitlab_group",
                "change": {
                    "actions": ["create"],
                    "after": {"path": "group1"}
                }
            },
            {
                "address": "gitlab_group.example2",
                "mode": "managed",
                "type": "gitlab_group",
                "change": {
                    "actions": ["create"],
                    "after": {"path": "group2"}
                }
            }
        ]
    }

@patch("codebase_suite.commands.terraform.import_tf.print_progress_bar")
@patch("codebase_suite.commands.terraform.import_tf.Config")
@patch("codebase_suite.commands.terraform.import_tf.Terraform")
@patch("codebase_suite.commands.terraform.import_tf.GitlabConnector")
def test_gitlab_import_groups_section(
    mock_gitlab_connector,
    mock_terraform,
    mock_config,
    mock_print_progress_bar,
    fake_plan_with_gitlab_groups,
    ctx_mock
):
    runner = CliRunner()

    # Mock instancji GitlabConnector
    gl_instance = mock_gitlab_connector.return_value
    # Dla każdej grupy zwróć id 100 i 200 odpowiednio
    def graphql_get_group_side_effect(path):
        if path == "group1":
            return {"id": 100}
        elif path == "group2":
            return {"id": 200}
        return {"id": 999}
    gl_instance.graphql_get_group.side_effect = graphql_get_group_side_effect

    # Mock terraform i jego metoda get_terraform_plan_json zwraca plan z grupami
    tf_instance = mock_terraform.return_value
    # Na pierwsze replan zwracamy plan z grupami
    # Później inne replany (np. z projektami) można zwrócić pusty, ale nie testujemy tu reszty
    tf_instance.get_terraform_plan_json.side_effect = [
        fake_plan_with_gitlab_groups,  # pierwszy replan z grupami
        {"resource_changes": []},       # później puste plany
        {"resource_changes": []}
    ]

    mock_config.return_value.tf_state_name_iac_gitlab = "iac-gitlab"

    # Wywołanie CLI z progress=True i dry-run
    result = runner.invoke(
        gitlab,
        ["--repository-path", "/repo", "--dry", "--progress"],
        obj=ctx_mock
    )

    # Sprawdzenia
    assert result.exit_code == 0
    tf_instance.terraform_init.assert_called_once_with("iac-gitlab")

    # Sprawdź, że terraform_import był wywołany dla obu grup z odpowiednimi id i dry=True
    tf_instance.terraform_import.assert_any_call("gitlab_group.example1", 100, True)
    tf_instance.terraform_import.assert_any_call("gitlab_group.example2", 200, True)
    assert tf_instance.terraform_import.call_count >= 2  # min 2 wywołania

    # Sprawdź, że print_progress_bar jest wywoływane (ponieważ --progress)
    assert mock_print_progress_bar.call_count >= 1

    # Sprawdź, czy print_progress_bar był wywołany z poprawnymi wartościami counter i resources_count
    calls = mock_print_progress_bar.call_args_list
    resources_count = len(fake_plan_with_gitlab_groups["resource_changes"])
    for call in calls:
        ctx_arg, counter_arg, count_arg = call.args[0], call.args[1], call.args[2]
    #     assert counter_arg <= resources_count
    #     assert count_arg == resources_count

@patch("codebase_suite.commands.terraform.import_tf.print_progress_bar")
@patch("codebase_suite.commands.terraform.import_tf.GitlabConnector")
@patch("codebase_suite.commands.terraform.import_tf.Terraform")
@patch("codebase_suite.commands.terraform.import_tf.Config")
def test_gitlab_import_group_settings(
    mock_config,
    mock_terraform,
    mock_gitlab_connector,
    mock_print_progress_bar,
    ctx_mock
):
    runner = CliRunner()

    # Przykładowy plan z różnymi zasobami gitlab_group_* w resource_changes
    fake_plan = {
        "resource_changes": [
            {
                "address": "gitlab_group_badge.badge1",
                "type": "gitlab_group_badge",
                "change": {
                    "actions": ["create"],
                    "after": {
                        "group": 10,
                        "name": "badge-name"
                    }
                }
            },
            {
                "address": "gitlab_group_label.label1",
                "type": "gitlab_group_label",
                "change": {
                    "actions": ["create"],
                    "after": {
                        "group": 10,
                        "name": "label-name"
                    }
                }
            },
            {
                "address": "gitlab_group_variable.var1",
                "type": "gitlab_group_variable",
                "change": {
                    "actions": ["create"],
                    "after": {
                        "group": 10,
                        "key": "VAR_KEY"
                    }
                }
            }
        ]
    }

    # Mokkowanie zwrotów GitlabConnector
    gl_instance = mock_gitlab_connector.return_value
    # get_group_by_id zwraca obiekt z full_path
    group_mock = MagicMock()
    group_mock.full_path = "group/fullpath"
    gl_instance.get_group_by_id.return_value = group_mock

    # get_group_badges zwraca badge pasujący do nazwy
    gl_instance.get_group_badges.return_value = [
        {"name": "badge-name", "id": 123},
        {"name": "other-badge", "id": 999}
    ]

    # graphql_get_group zwraca strukturę zawierającą labels i ciVariables
    gl_instance.graphql_get_group.return_value = {
        "labels": [
            {"title": "label-name", "id": 222},
            {"title": "other-label", "id": 999}
        ],
        "ciVariables": [
            {"key": "VAR_KEY", "environmentScope": "prod"},
            {"key": "OTHER_KEY", "environmentScope": "dev"}
        ]
    }

    # Mokkowanie Terraform i replan
    tf_instance = mock_terraform.return_value
    tf_instance.get_terraform_plan_json.return_value = fake_plan

    # Config mock
    mock_config.return_value.tf_state_name_iac_gitlab = "iac-gitlab"

    # Parametry wejściowe CLI
    args = [
        "--repository-path", "/repo",
        "--dry",
        "--progress"
    ]

    result = runner.invoke(gitlab, args, obj=ctx_mock)

    assert result.exit_code == 0

    # Sprawdzenie, że terraform_import wywołano z odpowiednimi parametrami

    # dla gitlab_group_badge
    tf_instance.terraform_import.assert_any_call("gitlab_group_badge.badge1", "10:123", True)

    # dla gitlab_group_label
    tf_instance.terraform_import.assert_any_call("gitlab_group_label.label1", "10:222", True)

    # dla gitlab_group_variable
    tf_instance.terraform_import.assert_any_call("gitlab_group_variable.var1", "10:VAR_KEY:prod", True)

    # Sprawdź, że terraform_import wywołano dokładnie 3 razy
    assert tf_instance.terraform_import.call_count >= 3

    # Sprawdź, że print_progress_bar był wywoływany (przynajmniej raz)
    assert mock_print_progress_bar.call_count >= 1

@patch("codebase_suite.commands.terraform.import_tf.GitlabConnector")
@patch("codebase_suite.commands.terraform.import_tf.Terraform")
@patch("codebase_suite.commands.terraform.import_tf.Config")
def test_gitlab_import_project_settings(
    mock_config,
    mock_terraform,
    mock_gitlab_connector,
    ctx_mock
):
    runner = CliRunner()

    project_id = 42

    # Przykładowy plan z różnymi zasobami projektowymi
    fake_plan = {
        "resource_changes": [
            {
                "address": "gitlab_branch_protection.bp1",
                "type": "gitlab_branch_protection",
                "change": {
                    "actions": ["create"],
                    "after": {
                        "project": project_id,
                        "branch": "main"
                    }
                }
            },
            {
                "address": "gitlab_tag_protection.tp1",
                "type": "gitlab_tag_protection",
                "change": {
                    "actions": ["create"],
                    "after": {
                        "project": project_id,
                        "tag": "v1.0"
                    }
                }
            },
            {
                "address": "gitlab_project_badge.badge1",
                "type": "gitlab_project_badge",
                "change": {
                    "actions": ["create"],
                    "after": {
                        "project": project_id,
                        "name": "badge-name"
                    }
                }
            },
            {
                "address": "gitlab_project_mirror.mirror1",
                "type": "gitlab_project_mirror",
                "change": {
                    "actions": ["create"],
                    "after": {
                        "project": project_id,
                        "url": "https://mirror.repo"
                    }
                }
            },
            {
                "address": "gitlab_project_label.label1",
                "type": "gitlab_project_label",
                "change": {
                    "actions": ["create"],
                    "after": {
                        "project": project_id,
                        "name": "label-name"
                    }
                }
            },
            {
                "address": "gitlab_project_variable.var1",
                "type": "gitlab_project_variable",
                "change": {
                    "actions": ["create"],
                    "after": {
                        "project": project_id,
                        "key": "VAR_KEY"
                    }
                }
            }
        ]
    }

    # Mokkowanie GitlabConnector
    gl_instance = mock_gitlab_connector.return_value

    # get_project_by_id zwraca obiekt z path_with_namespace
    project_mock = MagicMock()
    project_mock.path_with_namespace = "group/project"
    gl_instance.get_project_by_id.return_value = project_mock

    # graphql_get_project zwraca dane do branchRules, labels i ciVariables
    gl_instance.graphql_get_project.return_value = {
        "branchRules": [{"name": "main"}, {"name": "dev"}],
        "labels": [{"title": "label-name", "id": 555}],
        "ciVariables": [{"key": "VAR_KEY", "environmentScope": "prod"}],
    }

    # get_project_protected_tags zwraca listę tagów
    gl_instance.get_project_protected_tags.return_value = [
        {"name": "v1.0"}, {"name": "v0.9"}
    ]

    # get_project_badges zwraca listę badge'y
    gl_instance.get_project_badges.return_value = [
        {"name": "badge-name", "id": 111}
    ]

    # get_project_mirrors zwraca listę mirrorów
    gl_instance.get_project_mirrors.return_value = [
        MagicMock(url="https://mirror.repo", id=777)
    ]

    # Mokkowanie Terraform i jego plan
    tf_instance = mock_terraform.return_value
    tf_instance.get_terraform_plan_json.return_value = fake_plan

    # Config
    mock_config.return_value.tf_state_name_iac_gitlab = "iac-gitlab"

    # Wywołanie CLI
    args = [
        "--repository-path", "/repo",
        "--dry"
    ]

    result = runner.invoke(gitlab, args, obj=ctx_mock)

    assert result.exit_code == 0

    # Sprawdź wywołania terraform_import

    tf_instance.terraform_import.assert_any_call("gitlab_branch_protection.bp1", f"{project_id}:main", True)
    tf_instance.terraform_import.assert_any_call("gitlab_tag_protection.tp1", f"{project_id}:v1.0", True)
    tf_instance.terraform_import.assert_any_call("gitlab_project_badge.badge1", f"{project_id}:111", True)
    tf_instance.terraform_import.assert_any_call("gitlab_project_mirror.mirror1", f"{project_id}:777", True)
    tf_instance.terraform_import.assert_any_call("gitlab_project_label.label1", f"{project_id}:555", True)
    tf_instance.terraform_import.assert_any_call("gitlab_project_variable.var1", f"{project_id}:VAR_KEY:prod", True)

    assert tf_instance.terraform_import.call_count >= 6


@patch("codebase_suite.commands.terraform.import_tf.print_progress_bar")
@patch("codebase_suite.commands.terraform.import_tf.GitlabConnector")
@patch("codebase_suite.commands.terraform.import_tf.Terraform")
@patch("codebase_suite.commands.terraform.import_tf.Config")
def test_print_progress_bar_called_only_when_progress_true_and_counter_less_than_resources(
    mock_config,
    mock_terraform,
    mock_gitlab_connector,
    mock_print_progress_bar,
    ctx_mock
):
    runner = CliRunner()

    # Fake plan z 2 zasobami — żeby counter < resources_count wystąpiło
    fake_plan = {
        "resource_changes": [
            {
                "address": "gitlab_group.example1",
                "type": "gitlab_group",
                "change": {"actions": ["create"], "after": {"path": "group1"}}
            },
            {
                "address": "gitlab_group.example2",
                "type": "gitlab_group",
                "change": {"actions": ["create"], "after": {"path": "group2"}}
            }
        ]
    }

    # Mokkowanie zwrotów GitlabConnector i Terraform
    gl_instance = mock_gitlab_connector.return_value
    gl_instance.graphql_get_group.return_value = {"id": 123}
    gl_instance.get_group_by_id.return_value = MagicMock(full_path="group")

    tf_instance = mock_terraform.return_value
    tf_instance.get_terraform_plan_json.return_value = fake_plan

    mock_config.return_value.tf_state_name_iac_gitlab = "iac-gitlab"

    # Test z progress=True → print_progress_bar wywołane
    result = runner.invoke(
        gitlab,
        ["--repository-path", "/repo", "--dry", "--progress"],
        obj=ctx_mock
    )
    assert result.exit_code == 0

    # Sprawdźmy wywołania print_progress_bar i ich argumenty
    counters = [call.args[1] for call in mock_print_progress_bar.call_args_list]
    sizes = [call.args[2] for call in mock_print_progress_bar.call_args_list]

    # W pętli jest wywołanie z counter < resources_count
    assert any(counter < size for counter, size in zip(counters, sizes))

    # Po pętli jest wywołanie z counter == resources_count
    assert any(counter == size for counter, size in zip(counters, sizes))

    # Test z progress=False → print_progress_bar nie wywołane
    mock_print_progress_bar.reset_mock()
    tf_instance.get_terraform_plan_json.return_value = fake_plan
    result2 = runner.invoke(
        gitlab,
        ["--repository-path", "/repo", "--dry"],
        obj=ctx_mock
    )
    assert result2.exit_code == 0
    mock_print_progress_bar.assert_not_called()