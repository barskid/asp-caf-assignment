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

@requires_repo
def create_like(self, commit_ref: HashRef | str, user: str) -> HashRef:
    if not user:
        raise ValueError("User is required")

    commit_hash = self.resolve_commit_ref(commit_ref)

    # Ensure likes refs directories exist
    self.likes_by_user_dir().mkdir(parents=True, exist_ok=True)
    self.likes_by_commit_dir().mkdir(parents=True, exist_ok=True)

    # Ensure user exists (logical creation via refs)
    self.add_user(user)

    # Get previous user like
    user_ref_path = self.user_likes_ref(user)
    prev_like_ref = read_ref(user_ref_path) if user_ref_path.exists() else None

    # Prevent duplicate like by walking the user's like chain
    current = self.resolve_ref(prev_like_ref) if prev_like_ref else None
    while current:
        like_obj = load_like(self.objects_dir(), current)
        if like_obj.commit_hash == commit_hash:
            raise RepositoryError(
                f"User '{user}' already liked commit '{commit_hash}'"
            )
        current = HashRef(like_obj.prev_like) if like_obj.prev_like else None

    # Create Like
    timestamp = int(datetime.now().timestamp())
    like = Like(commit_hash, user, timestamp, prev_like_ref)
    save_like(self.objects_dir(), like)
    like_hash = HashRef(hash_object(like))

    # Update refs
    write_ref(user_ref_path, like_hash)

    commit_user_ref = self.commit_likes_ref(commit_hash) / user
    commit_user_ref.parent.mkdir(parents=True, exist_ok=True)
    write_ref(commit_user_ref, like_hash)

    return like_hash


@requires_repo
def add_user(self, user: str) -> None:
    if not user:
        raise ValueError("User name is required")

    # Ensure likes-by-user directory exists
    self.likes_by_user_dir().mkdir(parents=True, exist_ok=True)

    user_ref_path = self.user_likes_ref(user)

    # User already exists → nothing to do
    if user_ref_path.exists():
        return

    # Logical creation of user
    user_ref_path.touch()

