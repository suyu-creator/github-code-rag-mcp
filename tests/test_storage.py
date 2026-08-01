"""Tests for the storage module — FTS5 search + search history."""
import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.models import RepoInfo, SearchHistory
from storage.sqlite_storage import Storage


def test_index_and_search():
    """Index files and search via FTS5."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        storage = Storage(db_path)

        # Index a file
        storage.index_file("test/repo", "main.py", "def hello(name):\n    print(f'Hello {name}')\n    return name")
        storage.index_file("test/repo", "utils.py", "def parse_file(path):\n    with open(path) as f:\n        return f.read()")

        # Search by keyword
        results = storage.search_code("hello")
        assert len(results) >= 1
        assert results[0].file_path == "main.py"

        # Search by content
        results = storage.search_code("parse_file")
        assert len(results) >= 1
        assert results[0].file_path == "utils.py"

        # Search with repo filter
        results = storage.search_code("hello", repo="test/repo")
        assert len(results) >= 1
        assert all(r.repo == "test/repo" for r in results)

        # Empty search
        results = storage.search_code("zzzzznotfound")
        assert len(results) == 0

        # Short query (less than 2 chars)
        results = storage.search_code("a")
        assert len(results) == 0

    finally:
        storage.close()
        os.unlink(db_path)


def test_index_repo_files():
    """Index all files in a directory."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        storage = Storage(db_path)

        # Create a temp repo structure
        with tempfile.TemporaryDirectory() as repo_dir:
            # Create some source files
            with open(os.path.join(repo_dir, "app.py"), "w") as f:
                f.write("def main():\n    print('hello')\n")
            with open(os.path.join(repo_dir, "utils.py"), "w") as f:
                f.write("def helper():\n    return 42\n")
            # Create a non-source file (should be skipped)
            with open(os.path.join(repo_dir, "image.jpg"), "w") as f:
                f.write("binary data\n")
            # Create a file in __pycache__ (should be skipped)
            os.makedirs(os.path.join(repo_dir, "__pycache__"))
            with open(os.path.join(repo_dir, "__pycache__", "cache.py"), "w") as f:
                f.write("cached = True\n")

            count = storage.index_repo_files("test/repo", repo_dir)
            assert count == 2  # Only app.py and utils.py

        # Search should find content
        results = storage.search_code("main")
        assert len(results) >= 1
        assert results[0].repo == "test/repo"

    finally:
        storage.close()
        os.unlink(db_path)


def test_search_history():
    """Record and retrieve search history by category."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        storage = Storage(db_path)

        # Record searches
        storage.record_search("电商web", RepoInfo(
            name="owner/ecommerce", url="https://github.com/owner/ecommerce",
            language="python", indexed_at="2026-08-01T00:00:00Z",
        ))
        storage.record_search("电商web", RepoInfo(
            name="owner/shop", url="https://github.com/owner/shop",
            language="javascript", indexed_at="2026-08-02T00:00:00Z",
        ))
        storage.record_search("点餐小程序", RepoInfo(
            name="owner/ordering", url="https://github.com/owner/ordering",
            language="python", indexed_at="2026-08-03T00:00:00Z",
        ))

        # Query by category
        results = storage.get_search_history("电商web")
        assert len(results) == 2
        assert results[0].repo_name == "owner/shop"  # Most recent first

        results = storage.get_search_history("点餐小程序")
        assert len(results) == 1
        assert results[0].repo_name == "owner/ordering"

        # Empty category
        results = storage.get_search_history("notexist")
        assert len(results) == 0

        # All categories
        cats = storage.get_all_categories()
        assert len(cats) == 2
        assert "电商web" in cats
        assert "点餐小程序" in cats

        # Latest index time
        latest = storage.get_latest_index_time("电商web")
        assert latest == "2026-08-02T00:00:00Z"

    finally:
        storage.close()
        os.unlink(db_path)


def test_repo_info():
    """Save and list repo info."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        storage = Storage(db_path)
        repo = RepoInfo(name="test/repo", url="https://github.com/test/repo",
                        language="python", file_count=5)
        storage.save_repo_info(repo)

        repos = storage.list_indexed_repos()
        assert len(repos) == 1
        assert repos[0].name == "test/repo"
        assert repos[0].file_count == 5
    finally:
        storage.close()
        os.unlink(db_path)


def test_delete_repo():
    """Delete all data for a repo."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        storage = Storage(db_path)
        storage.save_repo_info(RepoInfo(name="test/repo", file_count=1))
        storage.record_search("test", RepoInfo(name="test/repo", indexed_at="2026-01-01"))
        storage.index_file("test/repo", "main.py", "content")

        storage.delete_repo_data("test/repo")

        repos = storage.list_indexed_repos()
        assert len(repos) == 0
        assert len(storage.get_search_history("test")) == 0
        assert len(storage.search_code("content")) == 0
    finally:
        storage.close()
        os.unlink(db_path)


def test_get_stats():
    """Get storage statistics."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        storage = Storage(db_path)
        storage.index_file("test/repo", "main.py", "content")
        storage.record_search("test", RepoInfo(name="test/repo", indexed_at="2026-01-01"))
        storage.save_repo_info(RepoInfo(name="test/repo", file_count=1))

        stats = storage.get_stats()
        assert stats["repos"] == 1
        assert stats["files"] == 1
        assert stats["categories"] == 1
        assert stats["has_fts"] is True
    finally:
        storage.close()
        os.unlink(db_path)


if __name__ == "__main__":
    test_index_and_search()
    test_index_repo_files()
    test_search_history()
    test_repo_info()
    test_delete_repo()
    test_get_stats()
    print("All storage tests passed!")