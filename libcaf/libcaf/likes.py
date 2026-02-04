from pathlib import Path
from .plumbing import load_commit
from .ref import HashRef


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
