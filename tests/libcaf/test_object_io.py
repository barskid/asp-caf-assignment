from pathlib import Path

from libcaf.plumbing import hash_object, load_commit, load_tree, save_commit, save_tree, save_like, load_like

from libcaf import Commit, Tree, TreeRecord, TreeRecordType, Like



def test_save_load_commit(temp_repo_dir: Path) -> None:
    commit = Commit('tree_hash123', 'Author', 'Commit message', 1234567890, 'commithash123parent')
    commit_hash = hash_object(commit)

    save_commit(temp_repo_dir, commit)
    loaded_commit = load_commit(temp_repo_dir, commit_hash)

    assert loaded_commit.tree_hash == commit.tree_hash
    assert loaded_commit.author == commit.author
    assert loaded_commit.message == commit.message
    assert loaded_commit.timestamp == commit.timestamp
    assert loaded_commit.parent == commit.parent


def test_save_load_commit_without_parent(temp_repo_dir: Path) -> None:
    commit_none_parent = Commit('commithash456', 'Author', 'Commit message', 1234567890, None)
    commit_none_parent_hash = hash_object(commit_none_parent)

    save_commit(temp_repo_dir, commit_none_parent)
    loaded_commit_none_parent = load_commit(temp_repo_dir, commit_none_parent_hash)

    assert loaded_commit_none_parent.tree_hash == commit_none_parent.tree_hash
    assert loaded_commit_none_parent.author == commit_none_parent.author
    assert loaded_commit_none_parent.message == commit_none_parent.message
    assert loaded_commit_none_parent.timestamp == commit_none_parent.timestamp
    assert loaded_commit_none_parent.parent == commit_none_parent.parent


def test_save_load_tree(temp_repo_dir: Path) -> None:
    records = {
        'omer': TreeRecord(TreeRecordType.BLOB, 'omer123', 'omer'),
        'bar': TreeRecord(TreeRecordType.BLOB, 'bar123', 'bar'),
        'meshi': TreeRecord(TreeRecordType.BLOB, 'meshi123', 'meshi'),
    }
    tree = Tree(records)
    tree_hash = hash_object(tree)

    save_tree(temp_repo_dir, tree)
    loaded_tree = load_tree(temp_repo_dir, tree_hash)

    assert loaded_tree.records.keys() == records.keys()
    assert loaded_tree.records == records

def test_save_load_like(temp_repo_dir: Path) -> None:
 
    like = Like('commit123', 'user', 1234567890, 'prevlikehash123')
    like_hash = hash_object(like)

    save_like(temp_repo_dir, like)
    loaded_like = load_like(temp_repo_dir, like_hash)

    assert loaded_like.commit_hash == like.commit_hash
    assert loaded_like.user == like.user
    assert loaded_like.timestamp == like.timestamp
    assert loaded_like.prev_like == like.prev_like


def test_save_load_like_without_prev_like(temp_repo_dir: Path) -> None:
    like_no_prev = Like('commit456', 'user', 987654321, None)
    like_no_prev_hash = hash_object(like_no_prev)

    save_like(temp_repo_dir, like_no_prev)
    loaded_like_no_prev = load_like(temp_repo_dir, like_no_prev_hash)

    assert loaded_like_no_prev.commit_hash == like_no_prev.commit_hash
    assert loaded_like_no_prev.user == like_no_prev.user
    assert loaded_like_no_prev.timestamp == like_no_prev.timestamp
    assert loaded_like_no_prev.prev_like == like_no_prev.prev_like