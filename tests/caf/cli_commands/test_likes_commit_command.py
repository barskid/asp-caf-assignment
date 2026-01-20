from collections.abc import Callable
from pathlib import Path

from libcaf.constants import DEFAULT_REPO_DIR, HEAD_FILE
from libcaf.repository import Repository
from pytest import CaptureFixture

from caf import cli_commands


def test_likes_commit_command(temp_repo: Repository, parse_commit_hash: Callable[[], str], capsys: CaptureFixture[str]) -> None:
    working_dir = temp_repo.working_dir
    temp_file = working_dir / 'likes_commit_test.txt'

    temp_file.write_text('First commit content')
    assert cli_commands.commit(working_dir_path=working_dir, author='LikeTester1', message='First commit') == 0
    commit_hash1 = parse_commit_hash()

    temp_file.write_text('Second commit content')
    assert cli_commands.commit(working_dir_path=working_dir, author='LikeTester2', message='Second commit') == 0

    assert cli_commands.like(working_dir_path=working_dir, commit_ref=commit_hash1, user='LikeTester1') == 0
    assert cli_commands.like(working_dir_path=working_dir, commit_ref=commit_hash1, user='LikeTester2') == 0

    assert cli_commands.likes_commit(working_dir_path=working_dir, commit=commit_hash1) == 0

    output = capsys.readouterr().out
    assert 'LikeTester1' in output
    assert 'LikeTester2' in output
    assert 'Like history for commit' in output


def test_likes_commit_no_repo(temp_repo_dir: Path, capsys: CaptureFixture[str]) -> None:
    assert cli_commands.likes_commit(working_dir_path=temp_repo_dir, commit='deadbeef') == -1
    assert 'No repository found' in capsys.readouterr().err


def test_likes_commit_no_likes(temp_repo: Repository, parse_commit_hash: Callable[[], str], capsys: CaptureFixture[str]) -> None:
    working_dir = temp_repo.working_dir
    temp_file = working_dir / 'likes_commit_empty.txt'

    temp_file.write_text('Commit with no likes')
    assert cli_commands.commit(working_dir_path=working_dir, author='LikeTester1', message='Lonely commit') == 0
    commit_hash = parse_commit_hash()

    assert cli_commands.likes_commit(working_dir_path=working_dir, commit=commit_hash) == 0
    assert 'No likes found for commit' in capsys.readouterr().out


def test_likes_commit_repo_error(temp_repo: Repository, capsys: CaptureFixture[str]) -> None:
    working_dir = temp_repo.working_dir
    (working_dir / DEFAULT_REPO_DIR / HEAD_FILE).unlink()

    assert cli_commands.likes_commit(working_dir_path=working_dir, commit='deadbeef') == -1
    assert 'Repository error' in capsys.readouterr().err
