from pathlib import Path

from libcaf.repository import Repository
from pytest import CaptureFixture

from caf import cli_commands


def test_like_no_repo(temp_repo_dir: Path, capsys: CaptureFixture[str]) -> None:
    assert cli_commands.like(
        working_dir_path=temp_repo_dir,
        commit_ref='HEAD',
        user= 'John Doe'
    ) == -1

    assert 'No repository found' in capsys.readouterr().err

def test_like_missing_commit(
    temp_repo: Repository,
    capsys: CaptureFixture[str]
) -> None:
    assert cli_commands.like(
        working_dir_path=temp_repo.working_dir,
        commit_ref=None,
        user='John Doe'
    ) == -1

    err = capsys.readouterr().err
    assert 'Commit' in err or 'Invalid' in err


def test_like_missing_user(temp_repo: Repository, capsys: CaptureFixture[str]) -> None:
    temp_file = temp_repo.working_dir / 'file.txt'
    temp_file.write_text('content')

    cli_commands.commit(
        working_dir_path=temp_repo.working_dir,
        author='John Doe',
        message='first commit'
    )

    assert cli_commands.like(
        working_dir_path=temp_repo.working_dir,
        commit_ref='HEAD',
        user=None
    ) == -1

    assert 'User name is required' in capsys.readouterr().err

def test_like_no_existent_commit_hash(
        
    temp_repo: Repository,
    capsys: CaptureFixture[str]
    ) -> None:
    fake_commit_hash = 'a' * 40  

    assert cli_commands.like(
        working_dir_path=temp_repo.working_dir,
        commit_ref=fake_commit_hash,
        user='John Doe'
    ) == -1

    err = capsys.readouterr().err
    assert 'Invalid commit reference' in err or 'Repository error' in err

def test_like_invalid_commit_ref(
    temp_repo: Repository,
    capsys: CaptureFixture[str]
) -> None:
    assert cli_commands.like(
        working_dir_path=temp_repo.working_dir,
        commit_ref='not-a-commit',
        user='John Doe'
    ) == -1

    err = capsys.readouterr().err
    assert 'Invalid' in err or 'Repository error' in err


def test_like_head_success(temp_repo: Repository, capsys: CaptureFixture[str]) -> None:
    # create a commit first
    temp_file = temp_repo.working_dir / 'file.txt'
    temp_file.write_text('content')

    assert cli_commands.commit(
        working_dir_path=temp_repo.working_dir,
        author='John Doe',
        message='first commit'
    ) == 0

    # like HEAD
    assert cli_commands.like(
        working_dir_path=temp_repo.working_dir,
        commit_ref='HEAD',
        user='John Doe'
    ) == 0

    output = capsys.readouterr().out
    assert 'Like created successfully' in output
    assert 'Like hash:' in output
    assert 'User: John Doe' in output


def test_like_commit_hash_success(temp_repo: Repository, capsys: CaptureFixture[str]) -> None:
    temp_file = temp_repo.working_dir / 'file.txt'
    temp_file.write_text('content')

    # create commit
    cli_commands.commit(
        working_dir_path=temp_repo.working_dir,
        author='John Doe',
        message='first commit'
    )

    # get commit hash from log output
    log_output = capsys.readouterr().out
    commit_hash_line = next(line for line in log_output.splitlines() if 'Hash:' in line)
    commit_hash = commit_hash_line.split('Hash:')[1].strip()

    # like by commit hash
    assert cli_commands.like(
        working_dir_path=temp_repo.working_dir,
        commit_ref=commit_hash,
        user='John Doe'
    ) == 0

    output = capsys.readouterr().out
    assert 'Like created successfully' in output
    assert f'Commit: {commit_hash}' in output


def test_like_duplicate_same_user(temp_repo: Repository, capsys: CaptureFixture[str]) -> None:
    temp_file = temp_repo.working_dir / 'file.txt'
    temp_file.write_text('content')

    cli_commands.commit(
        working_dir_path=temp_repo.working_dir,
        author='John Doe',
        message='first commit'
    )

    cli_commands.like(
        working_dir_path=temp_repo.working_dir,
        commit_ref='HEAD',
        user='John Doe'
    )

    # duplicate like by same user
    assert cli_commands.like(
        working_dir_path=temp_repo.working_dir,
        commit_ref='HEAD',
        user='John Doe'
    ) == -1

    err = capsys.readouterr().err
    assert 'already liked' in err





