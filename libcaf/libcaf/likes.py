from pathlib import Path
from .plumbing import load_commit
from .ref import HashRef
from .constants import HASH_LENGTH, HASH_CHARSET
from .repository import RepositoryError


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