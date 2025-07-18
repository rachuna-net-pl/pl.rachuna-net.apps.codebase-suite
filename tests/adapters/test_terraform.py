import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
from codebase_suite.adapters.Terraform.Terraform import Terraform


@pytest.fixture
def fake_path():
    return Path("/fake/path")


@pytest.fixture
def mock_logger():
    logger = MagicMock()
    logger.debug = MagicMock()
    logger.trace = MagicMock()
    logger.info = MagicMock()
    logger.success = MagicMock()
    logger.error = MagicMock()
    return logger


@pytest.fixture
def mock_gitlab_project():
    return {"id": "123456"}


@patch("codebase_suite.adapters.Terraform.Terraform.os.path.exists", return_value=True)
@patch("codebase_suite.adapters.Terraform.Terraform.Git")
@patch("codebase_suite.adapters.Terraform.Terraform.GitlabConnector")
def test_constructor_success(mock_gitlab_connector, mock_git, mock_exists, mock_logger, fake_path, mock_gitlab_project):
    mock_git.return_value.get_remote_url.return_value = "group/project"
    mock_gitlab_connector.return_value.graphql_get_project.return_value = mock_gitlab_project

    tf = Terraform(mock_logger, fake_path)

    mock_logger.debug.assert_called()
    mock_logger.trace.assert_called()
    mock_logger.info.assert_any_call("    Enable gitlab state: True")
    assert tf._Terraform__project_iac_id == "123456"

@patch("codebase_suite.adapters.Terraform.Terraform.os.path.exists", return_value=False)
@patch("codebase_suite.adapters.Terraform.Terraform.Logger")  # żeby nie próbował pisać do stderr
def test_constructor_raises_file_not_found(mock_logger_class, mock_exists, fake_path):
    mock_logger = MagicMock()
    mock_logger_class.return_value = mock_logger

    with pytest.raises(FileNotFoundError) as excinfo:
        Terraform(None, fake_path)

    assert str(excinfo.value) == f"Repository path '{fake_path}' does not exist."
@patch("codebase_suite.adapters.Terraform.Terraform.os.path.exists", return_value=True)
@patch("codebase_suite.adapters.Terraform.Terraform.Logger")
@patch("codebase_suite.adapters.Terraform.Terraform.Git")
@patch("codebase_suite.adapters.Terraform.Terraform.GitlabConnector")
def test_constructor_creates_default_logger(mock_gitlab_connector, mock_git, mock_logger_class, mock_exists, fake_path, mock_gitlab_project):
    # Arrange
    mock_logger_instance = MagicMock()
    mock_logger_class.return_value = mock_logger_instance

    mock_git.return_value.get_remote_url.return_value = "group/project"
    mock_gitlab_connector.return_value.graphql_get_project.return_value = mock_gitlab_project

    # Act
    tf = Terraform(None, fake_path)

    # Assert
    mock_logger_class.assert_called_once()  # sprawdzamy, że Logger() został utworzony
    assert tf._Terraform__logger == mock_logger_instance
    
@patch("codebase_suite.adapters.Terraform.Terraform.subprocess.run")
@patch("codebase_suite.adapters.Terraform.Terraform.Config")
@patch("codebase_suite.adapters.Terraform.Terraform.os.path.exists", return_value=True)
@patch("codebase_suite.adapters.Terraform.Terraform.Git")
@patch("codebase_suite.adapters.Terraform.Terraform.GitlabConnector")
def test_terraform_init_gitlab_state(
    mock_gitlab, mock_git, mock_exists, mock_config, mock_subproc, mock_logger, fake_path, mock_gitlab_project
):
    mock_git.return_value.get_remote_url.return_value = "group/project"
    mock_gitlab.return_value.graphql_get_project.return_value = mock_gitlab_project
    mock_config.return_value.gitlab_url = "https://gitlab.example.com"
    mock_config.return_value.gitlab_username = "ci-user"
    mock_config.return_value.gitlab_token.get_secret_value.return_value = "SECRET"
    mock_subproc.return_value.returncode = 0

    tf = Terraform(mock_logger, fake_path)
    tf.terraform_init("test-state")

    mock_subproc.assert_called()
    mock_logger.success.assert_called()


@patch("codebase_suite.adapters.Terraform.Terraform.subprocess.run")
@patch("codebase_suite.adapters.Terraform.Terraform.Config")
@patch("codebase_suite.adapters.Terraform.Terraform.os.path.exists", return_value=True)
@patch("codebase_suite.adapters.Terraform.Terraform.Git")
@patch("codebase_suite.adapters.Terraform.Terraform.GitlabConnector")
def test_terraform_init_with_gitlab_state_disabled(
    mock_gitlab_connector,
    mock_git,
    mock_exists,
    mock_config,
    mock_subproc,
    mock_logger,
    fake_path,
    mock_gitlab_project
):
    # Arrange
    mock_git.return_value.get_remote_url.return_value = "group/project"
    mock_gitlab_connector.return_value.graphql_get_project.return_value = mock_gitlab_project

    # Konfiguracja enable_gitlab_state = False
    tf = Terraform(mock_logger, fake_path, enable_gitlab_state=False)

    mock_config.return_value.tf_init_args = "-input=false -upgrade"
    mock_subproc.return_value.returncode = 0

    # Act
    tf.terraform_init("my-tf-state")

    # Assert
    # Komenda powinna zawierać tf_init_args z Config, a nie backend-config
    expected_cmd_part = f"terraform init {mock_config.return_value.tf_init_args}"
    called_cmd = mock_subproc.call_args[0][0]  # pierwszy argument wywołania subprocess.run (cmd)
    assert expected_cmd_part in called_cmd

    mock_logger.success.assert_called()


@patch("codebase_suite.adapters.Terraform.Terraform.subprocess.run")
@patch("codebase_suite.adapters.Terraform.Terraform.Config")
@patch("codebase_suite.adapters.Terraform.Terraform.os.path.exists", return_value=True)
@patch("codebase_suite.adapters.Terraform.Terraform.Git")
@patch("codebase_suite.adapters.Terraform.Terraform.GitlabConnector")
def test_terraform_init_subprocess_failure(
    mock_gitlab_connector,
    mock_git,
    mock_exists,
    mock_config,
    mock_subproc,
    mock_logger,
    fake_path,
    mock_gitlab_project
):
    # Arrange
    mock_git.return_value.get_remote_url.return_value = "group/project"
    mock_gitlab_connector.return_value.graphql_get_project.return_value = mock_gitlab_project

    mock_subproc.return_value.returncode = 1  # symulacja błędu
    mock_subproc.return_value.stdout = "fake stdout"
    mock_subproc.return_value.stderr = "fake stderr"

    tf = Terraform(mock_logger, fake_path, enable_gitlab_state=False)
    mock_config.return_value.tf_init_args = "-input=false"

    # Act + Assert
    with pytest.raises(SystemExit) as excinfo:
        tf.terraform_init("my-tf-state")

    # Sprawdzenie, że exit(1) został wywołany
    assert excinfo.value.code == 1

    # Sprawdzenie, że logger.error został wywołany
    mock_logger.error.assert_called_with("❌   Terraform init failed!")

    # Dodatkowo można sprawdzić, że stdout i stderr były wypisane (np. patch print)


@patch("codebase_suite.adapters.Terraform.Terraform.subprocess.run")
@patch("codebase_suite.adapters.Terraform.Terraform.os.remove")
@patch("codebase_suite.adapters.Terraform.Terraform.os.path.exists")
def test_terraform_plan_success(mock_exists, mock_remove, mock_subproc, mock_logger, fake_path):
    tf = Terraform.__new__(Terraform)
    tf._Terraform__cwd = fake_path
    tf._Terraform__logger = mock_logger
    tf._Terraform__cmd = "terraform"
    tf._Terraform__tfplan = ".terraform/.tfplan"

    mock_exists.return_value = True
    mock_subproc.return_value.returncode = 0

    tf.terraform_plan()

    mock_remove.assert_called()
    mock_logger.success.assert_called()


@patch("codebase_suite.adapters.Terraform.Terraform.os.remove")
@patch("codebase_suite.adapters.Terraform.Terraform.os.path.exists", return_value=True)
@patch("codebase_suite.adapters.Terraform.Terraform.subprocess.run")
@patch("builtins.print")
@patch("codebase_suite.adapters.Git.Git.os.path.isdir", return_value=True)  # <-- TU patchujemy isdir dla Git
@patch("codebase_suite.adapters.Terraform.Terraform.Git")
@patch("codebase_suite.adapters.Terraform.Terraform.GitlabConnector")
def test_terraform_plan_failure(
    mock_gitlab_connector,
    mock_git,
    mock_isdir,
    mock_print,
    mock_subproc,
    mock_exists,
    mock_remove,
):
    mock_logger = MagicMock()

    fake_path = Path("/fake/dir")

    mock_git.return_value.get_remote_url.return_value = "group/project"
    mock_gitlab_connector.return_value.graphql_get_project.return_value = {"id": "123"}

    mock_subproc.return_value.returncode = 1
    mock_subproc.return_value.stdout = "fake stdout"
    mock_subproc.return_value.stderr = "fake stderr"

    tf = Terraform(mock_logger, fake_path)

    with pytest.raises(SystemExit) as exc:
        tf.terraform_plan()

    assert exc.value.code == 1
    mock_remove.assert_called_once()
    mock_logger.error.assert_called_with("❌   Terraform plan failed!")

    printed = [call.args[0] for call in mock_print.call_args_list]
    assert any("terraform plan" in s for s in printed)
    assert "fake stdout" in printed
    assert "fake stderr" in printed

@patch("codebase_suite.adapters.Terraform.Terraform.subprocess.run")
@patch("codebase_suite.adapters.Terraform.Terraform.os.remove")
@patch("codebase_suite.adapters.Terraform.Terraform.os.path.exists")
def test_terraform_show_success(mock_exists, mock_remove, mock_subproc, mock_logger, fake_path):
    tf = Terraform.__new__(Terraform)
    tf._Terraform__cwd = fake_path
    tf._Terraform__logger = mock_logger
    tf._Terraform__cmd = "terraform"
    tf._Terraform__tfplan = ".terraform/.tfplan"
    tf._Terraform__tfplanjson = ".tfplan.json"

    mock_exists.return_value = True
    mock_subproc.return_value.returncode = 0

    tf.terraform_show()

    mock_remove.assert_called()
    mock_logger.success.assert_called()


@patch("codebase_suite.adapters.Terraform.Terraform.os.remove")
@patch("codebase_suite.adapters.Terraform.Terraform.os.path.exists", return_value=True)
@patch("codebase_suite.adapters.Terraform.Terraform.subprocess.run")
@patch("builtins.print")
@patch("codebase_suite.adapters.Git.Git.os.path.isdir", return_value=True)
@patch("codebase_suite.adapters.Terraform.Terraform.Git")
@patch("codebase_suite.adapters.Terraform.Terraform.GitlabConnector")
def test_terraform_show_failure(
    mock_gitlab_connector,
    mock_git,
    mock_isdir,
    mock_print,
    mock_subproc,
    mock_exists,
    mock_remove,
):
    mock_logger = MagicMock()
    fake_path = Path("/fake/dir")

    mock_git.return_value.get_remote_url.return_value = "group/project"
    mock_gitlab_connector.return_value.graphql_get_project.return_value = {"id": "123"}

    mock_subproc.return_value.returncode = 1
    mock_subproc.return_value.stdout = "fake stdout"
    mock_subproc.return_value.stderr = "fake stderr"

    tf = Terraform(mock_logger, fake_path)

    with pytest.raises(SystemExit) as exc:
        tf.terraform_show()

    assert exc.value.code == 1
    mock_remove.assert_called_once()
    mock_logger.error.assert_called_with("❌   Terraform show failed!")

    printed = [call.args[0] for call in mock_print.call_args_list]
    assert any("terraform show" in s for s in printed)
    assert "fake stdout" in printed
    assert "fake stderr" in printed

@patch("codebase_suite.adapters.Terraform.Terraform.subprocess.run")
@patch("codebase_suite.adapters.Terraform.Terraform.Config")
@patch("codebase_suite.adapters.Terraform.Terraform.os.path.exists", return_value=True)
@patch("codebase_suite.adapters.Terraform.Terraform.Git")
@patch("codebase_suite.adapters.Terraform.Terraform.GitlabConnector")
def test_terraform_init_subprocess_failure(
    mock_gitlab_connector,
    mock_git,
    mock_exists,
    mock_config,
    mock_subproc,
    mock_logger,
    fake_path,
    mock_gitlab_project
):
    # Arrange
    mock_git.return_value.get_remote_url.return_value = "group/project"
    mock_gitlab_connector.return_value.graphql_get_project.return_value = mock_gitlab_project

    mock_subproc.return_value.returncode = 1  # symulacja błędu
    mock_subproc.return_value.stdout = "fake stdout"
    mock_subproc.return_value.stderr = "fake stderr"

    tf = Terraform(mock_logger, fake_path, enable_gitlab_state=False)
    mock_config.return_value.tf_init_args = "-input=false"

    # Act + Assert
    with pytest.raises(SystemExit) as excinfo:
        tf.terraform_init("my-tf-state")

    # Sprawdzenie, że exit(1) został wywołany
    assert excinfo.value.code == 1

    # Sprawdzenie, że logger.error został wywołany
    mock_logger.error.assert_called_with("❌   Terraform init failed!")

    # Dodatkowo można sprawdzić, że stdout i stderr były wypisane (np. patch print)


@patch("codebase_suite.adapters.Terraform.Terraform.subprocess.run")
def test_terraform_import_executes(mock_subproc, mock_logger, fake_path):
    tf = Terraform.__new__(Terraform)
    tf._Terraform__cwd = fake_path
    tf._Terraform__logger = mock_logger
    tf._Terraform__cmd = "terraform"

    mock_subproc.return_value.returncode = 0

    tf.terraform_import("aws_s3_bucket.mybucket", "bucket-123")

    mock_logger.debug.assert_called()
    mock_logger.success.assert_called()


@patch("codebase_suite.adapters.Terraform.Terraform.subprocess.run")
@patch("builtins.print")
@patch("codebase_suite.adapters.Git.Git.os.path.isdir", return_value=True)
@patch("codebase_suite.adapters.Terraform.Terraform.os.path.exists", return_value=True)
@patch("codebase_suite.adapters.Terraform.Terraform.Git")
@patch("codebase_suite.adapters.Terraform.Terraform.GitlabConnector")
def test_terraform_import_failure(
    mock_gitlab_connector,
    mock_git,
    mock_exists,
    mock_isdir,
    mock_print,
    mock_subproc,
):
    mock_logger = MagicMock()
    fake_path = Path("/fake/dir")

    mock_git.return_value.get_remote_url.return_value = "group/project"
    mock_gitlab_connector.return_value.graphql_get_project.return_value = {"id": "123"}

    mock_subproc.return_value.returncode = 1
    mock_subproc.return_value.stdout = "stdout error"
    mock_subproc.return_value.stderr = "stderr error"

    tf = Terraform(mock_logger, fake_path)

    with pytest.raises(SystemExit) as exc:
        tf.terraform_import(to="resource.to_import", id="resource-id", dry=False)

    assert exc.value.code == 1

    mock_print.assert_any_call("terraform import 'resource.to_import' 'resource-id'")
    mock_print.assert_any_call("stdout error")
    mock_print.assert_any_call("stderr error")
    mock_logger.error.assert_called_with("❌   Terraform import failed!")


@patch("codebase_suite.adapters.Terraform.Terraform.subprocess.run")
@patch("codebase_suite.adapters.Git.Git.os.path.isdir", return_value=True)
@patch("codebase_suite.adapters.Terraform.Terraform.os.path.exists", return_value=True)
@patch("codebase_suite.adapters.Terraform.Terraform.Git")
@patch("codebase_suite.adapters.Terraform.Terraform.GitlabConnector")
def test_terraform_import_dry_run(
    mock_gitlab_connector,
    mock_git,
    mock_exists,
    mock_isdir,
    mock_subproc,
):
    mock_logger = MagicMock()
    fake_path = Path("/fake/dir")

    mock_git.return_value.get_remote_url.return_value = "group/project"
    mock_gitlab_connector.return_value.graphql_get_project.return_value = {"id": "123"}

    tf = Terraform(mock_logger, fake_path)

    tf.terraform_import(to="resource.to_import", id="resource-id", dry=True)

    # subprocess.run NIE powinno być wywołane w trybie dry
    mock_subproc.assert_not_called()
    

@patch("codebase_suite.adapters.Terraform.Terraform.os.path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data='{"resource_changes": []}')
def test_get_terraform_plan_json_success(mock_open_file, mock_exists, mock_logger, fake_path):
    tf = Terraform.__new__(Terraform)
    tf._Terraform__cwd = fake_path
    tf._Terraform__logger = mock_logger
    tf._Terraform__tfplanjson = ".tfplan.json"

    data = tf.get_terraform_plan_json()

    assert data == {"resource_changes": []}
    mock_open_file.assert_called()


@patch("codebase_suite.adapters.Terraform.Terraform.os.path.exists", return_value=False)
def test_get_terraform_plan_json_file_not_found(mock_exists, mock_logger, fake_path):
    tf = Terraform.__new__(Terraform)
    tf._Terraform__cwd = fake_path
    tf._Terraform__logger = mock_logger
    tf._Terraform__tfplanjson = ".tfplan.json"

    with pytest.raises(SystemExit):
        tf.get_terraform_plan_json()
    mock_logger.error.assert_called()
