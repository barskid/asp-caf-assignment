from pytest import raises

from libcaf.repository import Repository, RepositoryError
from libcaf.plumbing import load_like
from libcaf.ref import read_ref, HashRef
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


def test_like_delete(temp_repo: Repository) -> None:
    commit_ref = temp_repo.commit_working_dir('author', 'message')

    like_ref = temp_repo.create_like(commit_ref, user='user')

    temp_repo.delete_like(commit_ref, user='user')

    user_ref = (temp_repo.refs_dir() / LIKES_BY_USER_DIR / 'user')
    commit_ref_dir = (temp_repo.refs_dir()/ LIKES_BY_COMMIT_DIR/ str(commit_ref))

    assert not user_ref.exists()
    assert not commit_ref_dir.exists()

def test_like_delete_head_updates_user_head(temp_repo: Repository) -> None:
    commit_ref_1 = temp_repo.commit_working_dir('author', 'commit 1')
    commit_ref_2 = temp_repo.commit_working_dir('author', 'commit 2')

    first_like = temp_repo.create_like(commit_ref_1, user='user')
    second_like = temp_repo.create_like(commit_ref_2, user='user')

    # delete head (second like)
    temp_repo.delete_like(commit_ref_2, user='user')

    user_head = read_ref(temp_repo.refs_dir() / LIKES_BY_USER_DIR / 'user')

    assert user_head == first_like


def test_like_delete_middle_of_chain(temp_repo: Repository) -> None:
    commit_ref_1 = temp_repo.commit_working_dir('author', 'commit 1')
    commit_ref_2 = temp_repo.commit_working_dir('author', 'commit 2')
    commit_ref_3 = temp_repo.commit_working_dir('author', 'commit 3')

    like1 = temp_repo.create_like(commit_ref_1, user='user')
    like2 = temp_repo.create_like(commit_ref_2, user='user')
    like3 = temp_repo.create_like(commit_ref_3, user='user')

    # delete middle 
    temp_repo.delete_like(commit_ref_2, user='user')

    # head should still be the last like
    user_head = read_ref(temp_repo.refs_dir() / LIKES_BY_USER_DIR / 'user')
    assert user_head != like3

    head_like = load_like(temp_repo.objects_dir(), user_head)

    assert head_like.commit_hash == str(commit_ref_3)

    # deleted like should not exist under commit refs
    commit_like_ref = ( temp_repo.refs_dir()/ LIKES_BY_COMMIT_DIR/ str(commit_ref_2)/ 'user')
    assert not commit_like_ref.exists()


def test_like_delete_removes_commit_ref(temp_repo: Repository) -> None:
    commit_ref = temp_repo.commit_working_dir('author', 'message')

    temp_repo.create_like(commit_ref, user='user')
    temp_repo.delete_like(commit_ref, user='user')

    commit_like_ref = (temp_repo.refs_dir()/ LIKES_BY_COMMIT_DIR/ str(commit_ref)/ 'user')

    assert not commit_like_ref.exists()

def test_like_delete_cleans_empty_commit_dir(temp_repo: Repository) -> None:
    commit_ref = temp_repo.commit_working_dir('author', 'message')

    temp_repo.create_like(commit_ref, user='user')
    temp_repo.delete_like(commit_ref, user='user')

    commit_dir = (temp_repo.refs_dir()/ LIKES_BY_COMMIT_DIR/ str(commit_ref))

    assert not commit_dir.exists()



def test_like_delete_middle_of_chain_rewrites_chain(temp_repo: Repository,) -> None:
    commit_ref_1 = temp_repo.commit_working_dir('author', 'commit 1')
    commit_ref_2 = temp_repo.commit_working_dir('author', 'commit 2')
    commit_ref_3 = temp_repo.commit_working_dir('author', 'commit 3')

    like1 = temp_repo.create_like(commit_ref_1, user='user')
    like2 = temp_repo.create_like(commit_ref_2, user='user')
    like3 = temp_repo.create_like(commit_ref_3, user='user')

    temp_repo.delete_like(commit_ref_2, user='user')

    # HEAD should NOT equal old like3 (because rewrite happened)
    new_head = read_ref(temp_repo.refs_dir() / LIKES_BY_USER_DIR / 'user')

    assert new_head != like3

    # Load new head
    new_head_obj = load_like(temp_repo.objects_dir(), new_head)

    # It should point directly to like1
    assert new_head_obj.prev_like == like1


def test_like_deleted_object_not_in_chain(temp_repo: Repository,) -> None:
    commit_ref_1 = temp_repo.commit_working_dir('author', 'commit 1')
    commit_ref_2 = temp_repo.commit_working_dir('author', 'commit 2')
    commit_ref_3 = temp_repo.commit_working_dir('author', 'commit 3')

    temp_repo.create_like(commit_ref_1, user='user')
    temp_repo.create_like(commit_ref_2, user='user')
    temp_repo.create_like(commit_ref_3, user='user')

    temp_repo.delete_like(commit_ref_2, user='user')

    # Traverse chain and ensure commit_ref_2 not present
    current = read_ref(temp_repo.refs_dir() / LIKES_BY_USER_DIR / 'user')

    while current:
        like = load_like(temp_repo.objects_dir(), current)
        assert like.commit_hash != str(commit_ref_2)
        current = (HashRef(like.prev_like) if like.prev_like else None)


def test_like_delete_non_existing_like_raises_error(temp_repo: Repository,) -> None:
    commit_ref_1 = temp_repo.commit_working_dir('author', 'commit 1')
    commit_ref_2 = temp_repo.commit_working_dir('author', 'commit 2')

    temp_repo.create_like(commit_ref_1, user='user')

    with raises(RepositoryError):
        temp_repo.delete_like(commit_ref_2, user='user')


def test_likes_log_by_user_order(temp_repo: Repository) -> None:
    c1 = temp_repo.commit_working_dir("Author", "First commit")
    c2 = temp_repo.commit_working_dir("Author", "Second commit")

    like1 = temp_repo.create_like(c1, user="user")
    like2 = temp_repo.create_like(c2, user="user")

    assert [
        _.commit_hash
        for _ in temp_repo.likes_log_by_user("user")
    ] == [str(c2), str(c1)]


def test_likes_log_by_user_after_delete(temp_repo: Repository) -> None:
    c1 = temp_repo.commit_working_dir("Author", "c1")
    c2 = temp_repo.commit_working_dir("Author", "c2")
    c3 = temp_repo.commit_working_dir("Author", "c3")

    temp_repo.create_like(c1, user="user")
    temp_repo.create_like(c2, user="user")
    temp_repo.create_like(c3, user="user")

    temp_repo.delete_like(c2, user="user")

    assert [
        _.commit_hash
        for _ in temp_repo.likes_log_by_user("user")
    ] == [str(c3), str(c1)]


def test_likes_log_by_user_empty(temp_repo: Repository) -> None:
    assert list(temp_repo.likes_log_by_user("user")) == []

