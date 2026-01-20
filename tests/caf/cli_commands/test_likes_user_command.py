from collections.abc import Callable
from pathlib import Path

from libcaf.constants import DEFAULT_REPO_DIR, HEAD_FILE
from libcaf.repository import Repository
from pytest import CaptureFixture

from caf import cli_commands


def test_likes_user_command(temp_repo: Repository, parse_commit_hash: Callable[[], str], capsys: CaptureFixture[str]) -> None:
    working_dir = temp_repo.working_dir
    temp_file = working_dir / 'likes_user_test.txt'

    temp_file.write_text('First commit content')
    assert cli_commands.commit(working_dir_path=working_dir, author='LikeTester1', message='First commit') == 0
    commit_hash1 = parse_commit_hash()

    temp_file.write_text('Second commit content')
    assert cli_commands.commit(working_dir_path=working_dir, author='LikeTester2', message='Second commit') == 0
    commit_hash2 = parse_commit_hash()

    assert cli_commands.like(working_dir_path=working_dir, commit_ref=commit_hash1, user='LikeTester1') == 0
    assert cli_commands.like(working_dir_path=working_dir, commit_ref=commit_hash2, user='LikeTester1') == 0

    assert cli_commands.likes_user(working_dir_path=working_dir, user='LikeTester1') == 0

    output = capsys.readouterr().out
    assert commit_hash1 in output
    assert commit_hash2 in output
    assert 'Like history for user' in output


def test_likes_user_no_repo(temp_repo_dir: Path, capsys: CaptureFixture[str]) -> None:
    assert cli_commands.likes_user(working_dir_path=temp_repo_dir, user='LikeTester1') == -1
    assert 'No repository found' in capsys.readouterr().err


def test_likes_user_no_likes(temp_repo: Repository, capsys: CaptureFixture[str]) -> None:
    assert cli_commands.likes_user(working_dir_path=temp_repo.working_dir, user='LikeTester1') == 0
    assert 'No likes found for user' in capsys.readouterr().out


