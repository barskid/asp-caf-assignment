"""Constants used throughout libcaf."""

from _libcaf import hash_length

DEFAULT_REPO_DIR = '.caf'
OBJECTS_SUBDIR = 'objects'
HEAD_FILE = 'HEAD'
DEFAULT_BRANCH = 'main'
REFS_DIR = 'refs'
HEADS_DIR = 'heads'
LIKES_DIR = "likes"
LIKES_BY_USER_DIR = "likes/by-user"
LIKES_BY_COMMIT_DIR = "likes/by-commit"
LIKES_PENDING_DIR = "likes/pending"

HASH_LENGTH = hash_length()
HASH_CHARSET = '0123456789abcdef'
