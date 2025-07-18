import pytest
import json
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from codebase_suite.generators.terraform import GitlabGroup


@pytest.fixture
def sample_group():
    return {
        "name": "pl.rachuna-net",
        "fullPath": "pl.rachuna-net",
        "avatarUrl": "https://example.com/avatar.png"
    }

@pytest.fixture
def dummy_path(tmp_path):
    return tmp_path

@pytest.fixture
def logger_mock():
    return MagicMock()

@pytest.fixture
def config_mock():
    with patch("codebase_suite.generators.terraform.GitlabGroup.Config") as mock_config:
        mock_instance = MagicMock()
        mock_instance.tf_module_gitlab_group_source = "source_from_config"
        mock_config.return_value = mock_instance
        yield mock_config

@patch("codebase_suite.generators.terraform.GitlabGroup.Logger")
def test_logger_is_created_if_none_passed(mock_logger_class, sample_group, dummy_path, config_mock):
    # Act
    generator = GitlabGroup(
        template_path=dummy_path,
        group=sample_group,
        repository_path=dummy_path,
        logger=None  # <-- kluczowy przypadek
    )

    # Assert
    mock_logger_class.assert_called_once()  # Logger() został utworzony


@patch("codebase_suite.generators.terraform.GitlabGroup.Environment")
def test_generate_hcl_renders_template_and_saves_module(env_mock, sample_group, dummy_path, logger_mock, config_mock):
    fake_template = MagicMock()
    fake_template.render.return_value = 'rendered-content'
    
    env_instance = MagicMock()
    env_instance.get_template.return_value = fake_template
    env_mock.return_value = env_instance

    j2_file = dummy_path / "module.tf.j2"
    j2_file.write_text("dummy")

    generator = GitlabGroup(
        template_path=dummy_path,
        group=sample_group,
        repository_path=dummy_path,
        logger=logger_mock
    )

    with patch("builtins.open", mock_open()) as m_open, \
         patch("os.path.exists", return_value=False):
        generator.generate_hcl(force=True)

        m_open.assert_called_once()
        fake_template.render.assert_called_once()
        env_instance.get_template.assert_called_once_with(name="module.tf.j2")

@patch("codebase_suite.generators.terraform.GitlabGroup.Environment")
def test_generate_json_renders_template_and_saves_json(env_mock, sample_group, dummy_path, logger_mock, config_mock):
    fake_template = MagicMock()
    rendered_dict = {
        "resource": {
            "gitlab_group": {
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

    generator = GitlabGroup(
        template_path=dummy_path,
        group=sample_group,
        repository_path=dummy_path,
        logger=logger_mock
    )

    with patch("builtins.open", mock_open()) as m_open, \
         patch("os.path.exists", return_value=False):
        generator.generate_json(force=True)

        m_open.assert_called_once()
        fake_template.render.assert_called_once()
        env_instance.get_template.assert_called_once_with(name="module.tf.json.j2")

def test_avatar_is_none_if_blank(sample_group, dummy_path, logger_mock, config_mock):
    # Ustawiamy dokładnie b''
    sample_group["avatarUrl"] = "https://example.com/b''.png"

    generator = GitlabGroup(
        template_path=dummy_path,
        group=sample_group,
        repository_path=dummy_path,
        logger=logger_mock
    )

    assert generator._GitlabGroup__group["avatar"] is None

@patch("codebase_suite.generators.terraform.GitlabGroup.Logger")
def test_save_module_skips_when_tf_exists(mock_logger, sample_group, dummy_path, config_mock):
    logger = MagicMock()
    mock_logger.return_value = logger

    generator = GitlabGroup(
        template_path=dummy_path,
        group=sample_group,
        repository_path=dummy_path,
        logger=logger
    )

    # Symulujemy istnienie pliku .tf
    with patch("os.path.exists", side_effect=lambda path: str(path).endswith(".tf")), \
         patch("builtins.open", mock_open()) as m_open:
        generator._GitlabGroup__save_module(body="some-body", is_json=False)

        logger.warning.assert_called_once()
        logger.success.assert_not_called()
        m_open.assert_not_called()

@patch("codebase_suite.generators.terraform.GitlabGroup.Logger")
def test_save_module_skips_when_tf_json_exists(logger_mock_class, sample_group, dummy_path, config_mock):
    logger = MagicMock()
    logger_mock_class.return_value = logger

    generator = GitlabGroup(
        template_path=dummy_path,
        group=sample_group,
        repository_path=dummy_path,
        logger=logger
    )

    # Symulujemy istnienie pliku .tf.json
    with patch("os.path.exists", side_effect=lambda path: str(path).endswith(".tf.json")), \
         patch("builtins.open", mock_open()) as m_open:
        generator._GitlabGroup__save_module(body={"some": "json"}, is_json=True)

        logger.warning.assert_called_once()
        logger.success.assert_not_called()
        m_open.assert_not_called()

@patch("codebase_suite.generators.terraform.GitlabGroup.Logger")
def test_save_another_creates_directory(mock_logger_class, sample_group, dummy_path, config_mock):
    logger = MagicMock()
    mock_logger_class.return_value = logger

    generator = GitlabGroup(
        template_path=dummy_path,
        group=sample_group,
        repository_path=dummy_path,
        logger=None
    )

    dest = dummy_path / "nested/dir/file.tf"
    dest_dir = dest.parent

    with patch("os.path.isdir", return_value=False), \
         patch("os.makedirs") as mock_makedirs, \
         patch("os.path.exists", return_value=False), \
         patch("builtins.open", mock_open()):
        generator._GitlabGroup__save_another_files(dest=dest, body="content", is_json=False)

        mock_makedirs.assert_called_once_with(dest_dir)
        logger.success.assert_any_call(f"📁  Create directory: {dest_dir}")


@patch("codebase_suite.generators.terraform.GitlabGroup.Logger")
def test_save_another_skips_existing_tf(mock_logger_class, sample_group, dummy_path, config_mock):
    logger = MagicMock()
    mock_logger_class.return_value = logger

    generator = GitlabGroup(
        template_path=dummy_path,
        group=sample_group,
        repository_path=dummy_path,
        logger=None
    )

    dest = dummy_path / "group/file.tf"

    with patch("os.path.isdir", return_value=True), \
         patch("os.path.exists", side_effect=lambda p: str(p).endswith(".tf")), \
         patch("builtins.open", mock_open()) as m_open:
        generator._GitlabGroup__save_another_files(dest=dest, body="irrelevant", is_json=False)

        logger.warning.assert_called_once()
        m_open.assert_not_called()


@patch("codebase_suite.generators.terraform.GitlabGroup.Logger")
def test_save_another_skips_existing_tf_json(mock_logger_class, sample_group, dummy_path, config_mock):
    logger = MagicMock()
    mock_logger_class.return_value = logger

    generator = GitlabGroup(
        template_path=dummy_path,
        group=sample_group,
        repository_path=dummy_path,
        logger=None
    )

    dest = dummy_path / "group/file.json"

    with patch("os.path.isdir", return_value=True), \
         patch("os.path.exists", side_effect=lambda p: str(p).endswith(".json")), \
         patch("builtins.open", mock_open()) as m_open:
        generator._GitlabGroup__save_another_files(dest=dest, body="irrelevant", is_json=True)

        logger.warning.assert_called_once()
        m_open.assert_not_called()


@patch("codebase_suite.generators.terraform.GitlabGroup.Logger")
def test_save_another_writes_file_when_not_exists(mock_logger_class, sample_group, dummy_path, config_mock):
    logger = MagicMock()
    mock_logger_class.return_value = logger

    generator = GitlabGroup(
        template_path=dummy_path,
        group=sample_group,
        repository_path=dummy_path,
        logger=None
    )

    dest = dummy_path / "group/file.tf"

    with patch("os.path.isdir", return_value=True), \
         patch("os.path.exists", return_value=False), \
         patch("builtins.open", mock_open()) as m_open:
        generator._GitlabGroup__save_another_files(dest=dest, body="final-content", is_json=False)

        m_open.assert_called_once_with(dest, "w")
        logger.success.assert_any_call(f"📝  Generated: {dest} module definition.")

@patch("codebase_suite.generators.terraform.GitlabGroup.Logger")
def test_generate_hcl_handles_non_module_templates(mock_logger_class, sample_group, dummy_path, config_mock):
    logger = MagicMock()
    mock_logger_class.return_value = logger

    # Stwórz sztuczny szablon .tf.j2 poza module.tf.j2
    template_path = dummy_path / "templates"
    template_path.mkdir()
    (template_path / "outputs.tf.j2").write_text("output = {{ group.name }}")

    generator = GitlabGroup(
        template_path=template_path,
        group=sample_group,
        repository_path=dummy_path,
        logger=None
    )

    with patch.object(GitlabGroup, "_GitlabGroup__save_another_files") as mock_save:
        generator.generate_hcl(force=False)

        expected_dest = dummy_path / sample_group["fullPath"] / "outputs.tf"
        mock_save.assert_called_once()
        call_args = mock_save.call_args.kwargs
        assert call_args["dest"] == expected_dest
        assert "output = pl.rachuna-net" in call_args["body"]

@patch("codebase_suite.generators.terraform.GitlabGroup.Logger")
def test_generate_json_handles_non_module_templates(mock_logger_class, sample_group, dummy_path, config_mock):
    logger = MagicMock()
    mock_logger_class.return_value = logger

    # Stwórz sztuczny szablon .tf.json.j2 poza module.tf.json.j2
    template_path = dummy_path / "templates"
    template_path.mkdir()
    (template_path / "outputs.tf.json.j2").write_text('{"output": "{{ group.name }}"}')

    generator = GitlabGroup(
        template_path=template_path,
        group=sample_group,
        repository_path=dummy_path,
        logger=None
    )

    with patch.object(GitlabGroup, "_GitlabGroup__save_another_files") as mock_save:
        generator.generate_json(force=False)

        expected_dest = dummy_path / sample_group["fullPath"] / "outputs.tf.json"
        mock_save.assert_called_once()
        call_args = mock_save.call_args.kwargs
        assert call_args["dest"] == expected_dest
        assert call_args["body"] == {"output": "pl.rachuna-net"}