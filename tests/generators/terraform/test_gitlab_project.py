import pytest
import json
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from codebase_suite.generators.terraform import GitlabProject


@pytest.fixture
def sample_project():
    return {
        "name": "pl.rachuna-net",
        "fullPath": "pl.rachuna-net",
        "avatarUrl": "https://example.com/avatar.png",
        "description": "Test project",
        "visibility": "public",
        "archived": False
    }


@pytest.fixture
def dummy_path(tmp_path):
    return tmp_path


@pytest.fixture
def logger_mock():
    return MagicMock()


@pytest.fixture
def config_mock():
    with patch("codebase_suite.generators.terraform.GitlabProject.Config") as mock_config:
        mock_instance = MagicMock()
        mock_instance.tf_module_gitlab_project_source = "source_from_config"
        mock_config.return_value = mock_instance
        yield mock_config


@patch("codebase_suite.generators.terraform.GitlabProject.Logger")
def test_logger_is_created_if_none_passed(mock_logger_class, sample_project, dummy_path, config_mock):
    GitlabProject(
        template_path=dummy_path,
        project=sample_project,
        repository_path=dummy_path,
        logger=None
    )
    mock_logger_class.assert_called_once()


@patch("codebase_suite.generators.terraform.GitlabProject.Environment")
def test_generate_hcl_renders_template_and_saves_module(env_mock, sample_project, dummy_path, logger_mock, config_mock):
    fake_template = MagicMock()
    fake_template.render.return_value = 'rendered-content'
    env_instance = MagicMock()
    env_instance.get_template.return_value = fake_template
    env_mock.return_value = env_instance

    j2_file = dummy_path / "module.tf.j2"
    j2_file.write_text("dummy")

    generator = GitlabProject(
        template_path=dummy_path,
        project=sample_project,
        repository_path=dummy_path,
        logger=logger_mock
    )

    with patch("builtins.open", mock_open()) as m_open, \
         patch("os.path.exists", return_value=False):
        generator.generate_hcl(force=True)

        m_open.assert_called_once()
        fake_template.render.assert_called_once()


@patch("codebase_suite.generators.terraform.GitlabProject.Environment")
def test_generate_json_renders_template_and_saves_json(env_mock, sample_project, dummy_path, logger_mock, config_mock):
    fake_template = MagicMock()
    rendered_dict = {
        "resource": {
            "gitlab_project": {
                "example": {
                    "name": "pl.rachuna-net"
                }
            }
        }
    }
    fake_template.render.return_value = json.dumps(rendered_dict)

    env_instance = MagicMock()
    env_instance.get_template.return_value = fake_template
    env_mock.return_value = env_instance

    j2_file = dummy_path / "module.tf.json.j2"
    j2_file.write_text("dummy")

    generator = GitlabProject(
        template_path=dummy_path,
        project=sample_project,
        repository_path=dummy_path,
        logger=logger_mock
    )

    with patch("builtins.open", mock_open()) as m_open, \
         patch("os.path.exists", return_value=False):
        generator.generate_json(force=True)

        m_open.assert_called_once()
        fake_template.render.assert_called_once()


def test_avatar_is_none_if_blank(sample_project, dummy_path, logger_mock, config_mock):
    sample_project["avatarUrl"] = "https://example.com/b''.png"
    generator = GitlabProject(
        template_path=dummy_path,
        project=sample_project,
        repository_path=dummy_path,
        logger=logger_mock
    )
    assert generator._GitlabProject__project["avatar"] is None


@patch("codebase_suite.generators.terraform.GitlabProject.Logger")
def test_save_module_skips_when_tf_exists(mock_logger_class, sample_project, dummy_path, config_mock):
    logger = MagicMock()
    mock_logger_class.return_value = logger
    generator = GitlabProject(dummy_path, sample_project, dummy_path, logger)

    with patch("os.path.exists", side_effect=lambda p: str(p).endswith(".tf")), \
         patch("builtins.open", mock_open()) as m_open:
        generator._GitlabProject__save_module(body="body", is_json=False)

        logger.warning.assert_called_once()
        m_open.assert_not_called()


@patch("codebase_suite.generators.terraform.GitlabProject.Logger")
def test_save_module_skips_when_tf_json_exists(mock_logger_class, sample_project, dummy_path, config_mock):
    logger = MagicMock()
    mock_logger_class.return_value = logger
    generator = GitlabProject(dummy_path, sample_project, dummy_path, logger)

    with patch("os.path.exists", side_effect=lambda p: str(p).endswith(".tf.json")), \
         patch("builtins.open", mock_open()) as m_open:
        generator._GitlabProject__save_module(body={}, is_json=True)

        logger.warning.assert_called_once()
        m_open.assert_not_called()


@patch("codebase_suite.generators.terraform.GitlabProject.Logger")
def test_save_another_writes_when_not_exists(mock_logger_class, sample_project, dummy_path, config_mock):
    logger = MagicMock()
    mock_logger_class.return_value = logger
    generator = GitlabProject(dummy_path, sample_project, dummy_path, logger)
    dest = dummy_path / "subdir/file.tf"

    with patch("os.path.isdir", return_value=False), \
         patch("os.makedirs") as m_makedirs, \
         patch("os.path.exists", return_value=False), \
         patch("builtins.open", mock_open()) as m_open:
        generator._GitlabProject__save_another_files(dest=dest, body="abc", is_json=False)

        m_makedirs.assert_called_once_with(dest.parent)
        m_open.assert_called_once_with(dest, "w")
        logger.success.assert_any_call(f"📝  Generated: {dest} module definition.")

@patch("codebase_suite.generators.terraform.GitlabProject.Logger")
def test_save_another_skips_existing_tf(mock_logger_class, sample_project, dummy_path, config_mock):
    logger = MagicMock()
    mock_logger_class.return_value = logger

    generator = GitlabProject(
        template_path=dummy_path,
        project=sample_project,
        repository_path=dummy_path,
        logger=logger
    )

    dest = dummy_path / "some/path/file.tf"

    with patch("os.path.isdir", return_value=True), \
         patch("os.path.exists", side_effect=lambda path: str(path).endswith(".tf")), \
         patch("builtins.open", mock_open()) as m_open:
        generator._GitlabProject__save_another_files(dest=dest, body="irrelevant", is_json=False)

        logger.warning.assert_called_once_with(f"⛔  File {dest} already exists, skipping. Use --force to overwrite.")
        m_open.assert_not_called()

@patch("codebase_suite.generators.terraform.GitlabProject.Logger")
def test_save_another_skips_existing_tf_json(mock_logger_class, sample_project, dummy_path, config_mock):
    logger = MagicMock()
    mock_logger_class.return_value = logger

    generator = GitlabProject(
        template_path=dummy_path,
        project=sample_project,
        repository_path=dummy_path,
        logger=logger
    )

    dest = dummy_path / "some/path/file.json"

    with patch("os.path.isdir", return_value=True), \
         patch("os.path.exists", side_effect=lambda path: str(path).endswith(".json")), \
         patch("builtins.open", mock_open()) as m_open:
        generator._GitlabProject__save_another_files(dest=dest, body="irrelevant", is_json=True)

        logger.warning.assert_called_once_with(f"⛔  File {dest} already exists, skipping. Use --force to overwrite.")
        m_open.assert_not_called()

@patch("codebase_suite.generators.terraform.GitlabProject.Logger")
def test_generate_hcl_handles_non_module_templates(mock_logger_class, sample_project, dummy_path, config_mock):
    logger = MagicMock()
    mock_logger_class.return_value = logger

    template_path = dummy_path / "templates"
    template_path.mkdir()
    (template_path / "variables.tf.j2").write_text("variable = {{ project.name }}")

    generator = GitlabProject(
        template_path=template_path,
        project=sample_project,
        repository_path=dummy_path,
        logger=logger
    )

    with patch.object(GitlabProject, "_GitlabProject__save_another_files") as mock_save:
        generator.generate_hcl(force=True)

        expected_dest = dummy_path / sample_project["fullPath"] / "variables.tf"
        mock_save.assert_called_once()
        call_args = mock_save.call_args.kwargs
        assert call_args["dest"] == expected_dest
        assert "pl.rachuna-net" in call_args["body"]

@patch("codebase_suite.generators.terraform.GitlabProject.Logger")
def test_generate_json_handles_non_module_templates(mock_logger_class, sample_project, dummy_path, config_mock):
    logger = MagicMock()
    mock_logger_class.return_value = logger

    template_path = dummy_path / "templates"
    template_path.mkdir()
    (template_path / "outputs.tf.json.j2").write_text('{ "output": "{{ project.name }}" }')

    generator = GitlabProject(
        template_path=template_path,
        project=sample_project,
        repository_path=dummy_path,
        logger=logger
    )

    with patch.object(GitlabProject, "_GitlabProject__save_another_files") as mock_save:
        generator.generate_json(force=True)

        expected_dest = dummy_path / sample_project["fullPath"] / "outputs.tf.json"
        mock_save.assert_called_once()
        call_args = mock_save.call_args.kwargs
        assert call_args["dest"] == expected_dest
        assert call_args["body"] == {"output": "pl.rachuna-net"}