from pathlib import Path
from datetime import datetime

from .constants import HASH_LENGTH, HASH_CHARSET
from .ref import HashRef, read_ref, write_ref
from .plumbing import load_commit, load_like, save_like, hash_object
from .repository import RepositoryError
from . import Like

def likes_dir(repo) -> Path:
    """Get the path to the likes refs directory."""
    return repo.refs_dir() / "likes"


def likes_by_user_dir(repo) -> Path:
    """Get the path to the likes-by-user refs directory."""
    return likes_dir(repo) / "by-user"


def likes_by_commit_dir(repo) -> Path:
    """Get the path to the likes-by-commit refs directory."""
    return likes_dir(repo) / "by-commit"


def user_likes_ref(repo, user: str) -> Path:
    """Get the ref path for a specific user's likes."""
    return likes_by_user_dir(repo) / user


def commit_likes_ref(repo, commit_hash: str) -> Path:
    """Get the ref path for likes of a specific commit."""
    return likes_by_commit_dir(repo) / commit_hash

def likes_pending_dir(repo) -> Path:
    """Get the likes pending directory."""
    return likes_dir(repo) / "pending"


def likes_pending_ref(repo) -> Path:
    """Get the ref that points to the current pending like."""
    return likes_pending_dir(repo) / "current"


def commit_exists(repo, commit_hash: str) -> bool:
    try:
        load_commit(repo.objects_dir(), HashRef(commit_hash))
        return True
    except Exception:
        return False


def resolve_commit_ref(repo, commit_ref: HashRef | str) -> str:
    """
    Resolve a commit reference (hash or HEAD) to a commit hash string.
    """
    if commit_ref == "HEAD":
        resolved = repo.resolve_ref("HEAD")
        if resolved is None:
            raise RepositoryError("Invalid commit reference")
        commit_hash = str(resolved)

    elif isinstance(commit_ref, str) and len(commit_ref) == HASH_LENGTH \
            and all(c in HASH_CHARSET for c in commit_ref):
        commit_hash = commit_ref

    else:
        raise RepositoryError("Invalid commit reference")

    if not commit_exists(repo, commit_hash):
        raise RepositoryError(f"Commit '{commit_hash}' does not exist")

    return commit_hash


def read_likes_pending(repo) -> HashRef | None:
    """
    Read the current pending like operation, if exists.
    """
    ref = likes_pending_ref(repo)
    if not ref.exists():
        return None
    return read_ref(ref)



def write_likes_pending(repo, like_hash: HashRef) -> None:
    """
    Persist a pending like operation and write its ref.
    """
    likes_pending_dir(repo).mkdir(parents=True, exist_ok=True)
    write_ref(likes_pending_ref(repo), like_hash)


def clear_likes_pending(repo) -> None:
    """
    Clear the pending like state.
    """
    ref = likes_pending_ref(repo)
    if ref.exists():
        ref.unlink()

    dir_ = likes_pending_dir(repo)
    if dir_.exists() and not any(dir_.iterdir()):
        dir_.rmdir()

def like_ref_is_defined(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        read_ref(path)
        return True
    except Exception:
        return False

def add_like_to_user(repo, like: Like, like_hash: HashRef) -> None:
    user_ref = user_likes_ref(repo, like.user)
    write_ref(user_ref, like_hash)

def add_like_to_commit(repo, like: Like, like_hash: HashRef) -> None:
    commit_user_ref = commit_likes_ref(repo, like.commit_hash) / like.user
    commit_user_ref.parent.mkdir(parents=True, exist_ok=True)
    write_ref(commit_user_ref, like_hash)

def handle_pending_like(repo) -> None:
    like_hash = read_likes_pending(repo)
    if not like_hash:
        return

    like = load_like(repo.objects_dir(), like_hash)

    user_ref = user_likes_ref(repo, like.user)
    commit_user_ref = commit_likes_ref(repo, like.commit_hash) / like.user

    if not like_ref_is_defined(user_ref):
        add_like_to_user(repo, like, like_hash)

    if not like_ref_is_defined(commit_user_ref):
        add_like_to_commit(repo, like, like_hash)

    clear_likes_pending(repo)




def create_like(repo, commit_ref: HashRef | str, user: str) -> HashRef:
    if not user:
        raise ValueError("User is required")

    # 1. recover from previous crash
    handle_pending_like(repo)

    commit_hash = resolve_commit_ref(repo, commit_ref)

    # Ensure likes refs directories exist
    likes_by_user_dir(repo).mkdir(parents=True, exist_ok=True)
    likes_by_commit_dir(repo).mkdir(parents=True, exist_ok=True)

    # Ensure user exists
    add_user(repo, user)

    user_ref_path = user_likes_ref(repo, user)
    prev_like_ref = read_ref(user_ref_path) if user_ref_path.exists() else None

    # Prevent duplicate like
    current = repo.resolve_ref(prev_like_ref) if prev_like_ref else None
    while current:
        like_obj = load_like(repo.objects_dir(), current)
        if like_obj.commit_hash == commit_hash:
            raise RepositoryError(
                f"User '{user}' already liked commit '{commit_hash}'"
            )
        current = HashRef(like_obj.prev_like) if like_obj.prev_like else None

    # Create Like object
    timestamp = int(datetime.now().timestamp())
    like = Like(commit_hash, user, timestamp, prev_like_ref)
    save_like(repo.objects_dir(), like)
    like_hash = HashRef(hash_object(like))

    # 2. mark pending BEFORE writing refs
    write_likes_pending(repo, like_hash)

    try:
        add_like_to_user(repo, like, like_hash)
        add_like_to_commit(repo, like, like_hash)
    except Exception:
        # pending stays for recovery
        raise
    else:
        # 3. success → clear pending
        clear_likes_pending(repo)

    return like_hash


def add_user(repo, user: str) -> None:
    if not user:
        raise ValueError("User name is required")

    # Ensure likes-by-user directory exists
    likes_by_user_dir(repo).mkdir(parents=True, exist_ok=True)

    user_ref_path = user_likes_ref(repo, user)

    # User already exists → nothing to do
    if user_ref_path.exists():
        return

    # Logical creation of user
    user_ref_path.touch()

