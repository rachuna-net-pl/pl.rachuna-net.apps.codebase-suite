import pytest
import os
import subprocess

from path import Path
from unittest.mock import patch, MagicMock

from codebase_suite.adapters.Git import Git
from codebase_suite.core.Logger import Logger


@patch("codebase_suite.adapters.Git.Git.os.path.isdir", return_value=True)
def test_git_init_success(mock_isdir):
    repo_path = "/exist/path"
    Git._instance = None
    cl = Git(logger=Logger().get_logger(), src_path=repo_path)

    assert cl._Git__cwd == repo_path   

@patch("codebase_suite.adapters.Git.Git.os.path.isdir", return_value=False)
def test_git_init_failed(mock_isdir):
    Git._instance = None
    logger = Logger().get_logger()
    repo_path = "/invalid/path"
    
    with pytest.raises(FileNotFoundError):
        Git(logger=logger, src_path=repo_path)


@patch("codebase_suite.adapters.Git.Git.os.path.isdir", return_value=True)
@patch("codebase_suite.adapters.Git.Git.Logger", autospec=True)
def test_git_init_with_default_logger(mock_isdir, mock_logger):
    Git._instance = None
    repo_path = "/exist/path"

    cl = Git(logger=None, src_path=repo_path)

    assert cl._Git__cwd == repo_path

@patch("codebase_suite.adapters.Git.Git.os.path.isdir", return_value=True)
@patch("codebase_suite.adapters.Git.Git.subprocess.run")
def test_get_remote_url_ssh(mock_run, mock_isdir):
    Git._instance = None
    logger = Logger().get_logger()
    repo_path = "/exist/path"

    # SSH URL format
    mock_run.return_value = subprocess.CompletedProcess(
        args=["git remote get-url origin"],
        returncode=0,
        stdout="git@github.com:org/repo.git",
        stderr=""
    )

    git = Git(logger=logger, src_path=Path(repo_path))
    url = git.get_remote_url()

    assert url == "org/repo"
    assert git.full_path == "org/repo"


def test_get_remote_url_https():
    Git._instance = None
    logger = Logger().get_logger()
    repo_path = "/exist/path"

    with patch("codebase_suite.adapters.Git.Git.os.path.isdir", return_value=True):
        git = Git(logger=logger, src_path=Path(repo_path))

    with patch("codebase_suite.adapters.Git.Git.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["git remote get-url origin"],
            returncode=0,
            stdout="https://gitlab.com/org/repo.git",
            stderr=""
        )

        url = git.get_remote_url()

    assert url == "org/repo"
    assert git.full_path == "org/repo"

def test_get_remote_url_failure_returncode(capsys):
    Git._instance = None
    logger = Logger().get_logger()
    repo_path = "/invalid/path"

    with patch("codebase_suite.adapters.Git.Git.os.path.isdir", return_value=True):
        git = Git(logger=logger, src_path=Path(repo_path))

    with patch("codebase_suite.adapters.Git.Git.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["git remote get-url origin"],
            returncode=1,
            stdout="fatal: no such remote",
            stderr="error"
        )
    
        with pytest.raises(SystemExit):
            git.get_remote_url()

        captured = capsys.readouterr()
        assert "fatal: no such remote" in captured.out

@patch("codebase_suite.adapters.Git.Git.os.path.isdir", return_value=True)
@patch("codebase_suite.adapters.Git.Git.subprocess.run")
def test_get_remote_url_unknown_format(mock_run, mock_isdir):
    Git._instance = None
    logger = Logger().get_logger()
    repo_path = "/exist/path"

    mock_run.return_value = subprocess.CompletedProcess(
        args=["git remote get-url origin"],
        returncode=0,
        stdout="some-strange-format",
        stderr=""
    )

    git = Git(logger=logger, src_path=Path(repo_path))

    with pytest.raises(SystemExit):
        git.get_remote_url()