from pathlib import Path

from libcaf.constants import DEFAULT_REPO_DIR, REFS_DIR
from libcaf.repository import Repository
from pytest import CaptureFixture

from caf import cli_commands


def test_delete_like_command(temp_repo: Repository, parse_commit_hash, capsys: CaptureFixture[str]) -> None:
    working_dir = temp_repo.working_dir
    temp_file = working_dir / 'file.txt'
    temp_file.write_text('content')

    assert cli_commands.commit(working_dir_path=working_dir, author='user', message='msg') == 0
    commit_hash = parse_commit_hash()

    assert cli_commands.like(working_dir_path=working_dir, commit_ref=commit_hash, user='user') == 0
    assert cli_commands.delete_like(working_dir_path=working_dir, commit_ref=commit_hash, user='user') == 0

    like_ref_path = working_dir / DEFAULT_REPO_DIR / REFS_DIR / 'likes' / 'by-commit' / commit_hash / 'user'
    assert not like_ref_path.exists()

    assert 'Like by user' in capsys.readouterr().out


def test_delete_like_no_repo(temp_repo_dir: Path, capsys: CaptureFixture[str]) -> None:
    assert cli_commands.delete_like(working_dir_path=temp_repo_dir, commit_ref='HEAD', user='user') == -1
    assert 'No repository found' in capsys.readouterr().err


def test_delete_like_empty_commit(temp_repo: Repository, capsys: CaptureFixture[str]) -> None:
    assert cli_commands.delete_like(working_dir_path=temp_repo.working_dir, commit_ref='', user='user') == -1
    assert 'Commit reference is required' in capsys.readouterr().err


def test_delete_like_empty_user(temp_repo: Repository, capsys: CaptureFixture[str]) -> None:
    assert cli_commands.delete_like(working_dir_path=temp_repo.working_dir, commit_ref='HEAD', user='') == -1
    assert 'User name is required' in capsys.readouterr().err


def test_delete_like_does_not_exist(temp_repo: Repository, parse_commit_hash, capsys: CaptureFixture[str]) -> None:
    working_dir = temp_repo.working_dir
    temp_file = working_dir / 'file.txt'
    temp_file.write_text('content')

    assert cli_commands.commit(working_dir_path=working_dir, author='user', message='msg') == 0
    commit_hash = parse_commit_hash()

    assert cli_commands.delete_like(working_dir_path=working_dir, commit_ref=commit_hash, user='user') == -1
    assert 'has no like on commit' in capsys.readouterr().err

def test_delete_like_user_does_not_exist(temp_repo: Repository, parse_commit_hash, capsys: CaptureFixture[str]) -> None:
    working_dir = temp_repo.working_dir
    temp_file = working_dir / 'file.txt'
    temp_file.write_text('content')

    assert cli_commands.commit(working_dir_path=working_dir, author='user', message='msg') == 0
    commit_hash = parse_commit_hash()

    assert cli_commands.delete_like(working_dir_path=working_dir, commit_ref=commit_hash, user='user') == -1
    assert 'has no like on commit' in capsys.readouterr().err

def test_delete_like_from_middle(temp_repo: Repository, parse_commit_hash, capsys: CaptureFixture[str]) -> None:
    working_dir = temp_repo.working_dir
    temp_file = working_dir / 'file.txt'

    temp_file.write_text('v1')
    assert cli_commands.commit(working_dir_path=working_dir, author='user', message='msg') == 0
    commit1 = parse_commit_hash()

    temp_file.write_text('v2')
    assert cli_commands.commit(working_dir_path=working_dir, author='user', message='msg') == 0
    commit2 = parse_commit_hash()

    temp_file.write_text('v3')
    assert cli_commands.commit(working_dir_path=working_dir, author='user', message='msg') == 0
    commit3 = parse_commit_hash()

    assert cli_commands.like(working_dir_path=working_dir, commit_ref=commit1, user='user') == 0
    assert cli_commands.like(working_dir_path=working_dir, commit_ref=commit2, user='user') == 0
    assert cli_commands.like(working_dir_path=working_dir, commit_ref=commit3, user='user') == 0

    assert cli_commands.delete_like(working_dir_path=working_dir, commit_ref=commit2, user='user') == 0
    assert 'Like by user' in capsys.readouterr().out
