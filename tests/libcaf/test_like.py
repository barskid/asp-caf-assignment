from pytest import raises

from libcaf.repository import Repository, RepositoryError
from libcaf.plumbing import load_like
from libcaf.ref import read_ref
from libcaf.constants import LIKES_BY_USER_DIR, LIKES_BY_COMMIT_DIR

def test_like_create(temp_repo: Repository) -> None:
    commit_ref = temp_repo.commit_working_dir('author', 'message')

    like_ref = temp_repo.create_like(commit_ref, user='user')
    like = load_like(temp_repo.objects_dir(), like_ref)

    assert like.user == 'user'
    assert like.commit_hash == str(commit_ref)
    assert like.prev_like is None

def test_like_user_head_updated(temp_repo: Repository) -> None:
    commit_ref = temp_repo.commit_working_dir('author', 'message')

    like_ref = temp_repo.create_like(commit_ref, user='user')

    user_head = read_ref(
        temp_repo.refs_dir() / LIKES_BY_USER_DIR / 'user'
    )

    assert user_head == like_ref

def test_like_chain_for_same_user(temp_repo: Repository) -> None:
    commit_ref_1 = temp_repo.commit_working_dir('author', 'commit 1')
    commit_ref_2 = temp_repo.commit_working_dir('author', 'commit 2')

    first_like = temp_repo.create_like(commit_ref_1, user='user')
    second_like = temp_repo.create_like(commit_ref_2, user='user')

    second_like_obj = load_like(temp_repo.objects_dir(), second_like)

    assert second_like_obj.prev_like == first_like

def test_like_written_under_commit_ref(temp_repo: Repository) -> None:
    commit_ref = temp_repo.commit_working_dir('author', 'message')

    like_ref = temp_repo.create_like(commit_ref, user='user')

    commit_like_ref = (
        temp_repo.refs_dir()
        / LIKES_BY_COMMIT_DIR
        / str(commit_ref)
        / 'user'
    )

    assert commit_like_ref.exists()
    assert read_ref(commit_like_ref) == like_ref

def test_like_5_duplicate_same_user_same_commit_raises_error(temp_repo: Repository,) -> None:
    commit_ref = temp_repo.commit_working_dir('author', 'message')

    temp_repo.create_like(commit_ref, user='user')

    with raises(RepositoryError):
        temp_repo.create_like(commit_ref, user='user')

