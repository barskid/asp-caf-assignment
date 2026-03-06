from pathlib import Path
from datetime import datetime

from .ref import HashRef, read_ref, write_ref
from .plumbing import load_like, save_like, hash_object
from . import Like

class LikeError(Exception):
    """Logical error related to likes."""
    pass


def user_likes_ref(likes_by_user_dir: Path, user: str) -> Path:
    """Get the ref path for a specific user's likes."""
    return likes_by_user_dir / user


def commit_like_ref(likes_by_commit_dir: Path,commit_hash: HashRef, user: str,) -> Path:
    """Get the ref path for likes of a specific commit."""
    return likes_by_commit_dir / str(commit_hash) / user


def likes_pending_ref(likes_pending_dir: Path) -> Path:
    """Get the ref that points to the current pending like."""
    return likes_pending_dir / "current"


def read_likes_pending(likes_pending_dir: Path) -> HashRef | None:
    """
    Read the current pending like operation, if exists.
    """
    ref = likes_pending_ref(likes_pending_dir)
    if not ref.exists():
        return None
    return read_ref(ref)


def write_likes_pending(likes_pending_dir: Path, like_hash: HashRef) -> None:
    """
    Persist a pending like operation and write its ref.
    """
    likes_pending_dir.mkdir(parents=True, exist_ok=True)
    write_ref(likes_pending_ref(likes_pending_dir), like_hash)


def clear_likes_pending(likes_pending_dir: Path) -> None:
    """
    Clear the pending like state.
    """
    ref = likes_pending_ref(likes_pending_dir)
    if ref.exists():
        ref.unlink(missing_ok=True)


def handle_pending(
    *,
    objects_dir: Path,
    likes_by_user_dir: Path,
    likes_by_commit_dir: Path,
    likes_pending_dir: Path,
) -> None:

    pending = read_likes_pending(likes_pending_dir)
    if not pending:
        return

    like = load_like(objects_dir, pending)

    user_ref = user_likes_ref(likes_by_user_dir, like.user)
    commit_ref = commit_like_ref(
        likes_by_commit_dir, HashRef(like.commit_hash), like.user
    )

    if not user_ref.exists():
        write_ref(user_ref, pending)

    if not commit_ref.exists():
        commit_ref.parent.mkdir(parents=True, exist_ok=True)
        write_ref(commit_ref, pending)

    clear_likes_pending(likes_pending_dir)




def create_like(*,objects_dir: Path,
    likes_by_user_dir: Path,
    likes_by_commit_dir: Path,
    likes_pending_dir: Path,
    commit_hash: HashRef,
    user: str,
    ) -> HashRef:
    
    if not user:
        raise ValueError("User is required")

    #recover from previous crash
    handle_pending(
        objects_dir=objects_dir,
        likes_by_user_dir=likes_by_user_dir,
        likes_by_commit_dir=likes_by_commit_dir,
        likes_pending_dir=likes_pending_dir,
    )


    # Ensure likes refs directories exist
    likes_by_user_dir.mkdir(parents=True, exist_ok=True)
    likes_by_commit_dir.mkdir(parents=True, exist_ok=True)

    # Ensure user exists
    add_user(likes_by_user_dir, user)

    user_ref_path = user_likes_ref(likes_by_user_dir, user)
    prev_like_ref = read_ref(user_ref_path) if user_ref_path.exists() else None

    # Prevent duplicate like
    current = prev_like_ref
    while current:
        like_obj = load_like(objects_dir, current)
        if like_obj.commit_hash == str(commit_hash):
            raise LikeError(
                f"User '{user}' already liked commit '{commit_hash}'"
            )
        current = HashRef(like_obj.prev_like) if like_obj.prev_like else None

    # Create Like object
    timestamp = int(datetime.now().timestamp())
    like = Like(str(commit_hash), user, timestamp, prev_like_ref)
    save_like(objects_dir, like)
    like_hash = HashRef(hash_object(like))

    # 2. mark pending BEFORE writing refs
    write_likes_pending(likes_pending_dir, like_hash)

    try:
        write_ref(user_ref_path, like_hash)

        commit_ref = commit_like_ref(
            likes_by_commit_dir, commit_hash, user
        )
        commit_ref.parent.mkdir(parents=True, exist_ok=True)
        write_ref(commit_ref, like_hash)

    except Exception:
        raise
    else:
        clear_likes_pending(likes_pending_dir)

    return like_hash


def add_user(likes_by_user_dir: Path, user: str) -> None:
    if not user:
        raise ValueError("User name is required")

    # Ensure likes-by-user directory exists
    likes_by_user_dir.mkdir(parents=True, exist_ok=True)

    (likes_by_user_dir / user).touch(exist_ok=True)
    
    

def delete_like(*, objects_dir: Path, likes_by_user_dir: Path, likes_by_commit_dir: Path, commit_hash: HashRef, user: str, ) -> None:

    if not user:
        raise ValueError("User is required")

    user_ref_path = user_likes_ref(likes_by_user_dir, user)
    if not user_ref_path.exists():
        raise LikeError(f"User '{user}' has no likes")

    # Read full chain from HEAD
    full_chain = []
    current = read_ref(user_ref_path)

    while current:
        like = load_like(objects_dir, current)
        full_chain.append(like)
        current = HashRef(like.prev_like) if like.prev_like else None

    # Ensure like exists
    if not any(l.commit_hash == str(commit_hash) for l in full_chain):
        raise LikeError( f"User '{user}' has no like on commit '{commit_hash}'")

    # Remove target like
    filtered_chain = [ l for l in full_chain if l.commit_hash != str(commit_hash)]

    # Rebuild chain from bottom
    new_prev = None

    for like in reversed(filtered_chain):
        prev_hash_str = str(new_prev) if new_prev else None

        new_like = Like(like.commit_hash, like.user, like.timestamp, prev_hash_str,)

        save_like(objects_dir, new_like)
        new_prev = HashRef(hash_object(new_like))

    # Update user HEAD
    if new_prev:
        write_ref(user_ref_path, new_prev)
    else:
        # No likes left
        user_ref_path.unlink()

    # Remove by-commit ref
    commit_user_ref = (likes_by_commit_dir/ str(commit_hash)/ user)

    if commit_user_ref.exists():
        commit_user_ref.unlink()

    # Clean empty commit directory
    commit_dir = commit_user_ref.parent
    if commit_dir.exists() and not any(commit_dir.iterdir()):
        commit_dir.rmdir()