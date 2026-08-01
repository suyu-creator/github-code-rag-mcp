"""Tests for the SearchEngine — FTS5 search + search history."""
import sys
import os
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.models import RepoInfo
from core.retrieval_engine import SearchEngine
from storage.sqlite_storage import Storage


def test_search_code():
    """Search indexed code via SearchEngine."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        storage = Storage(db_path)
        engine = SearchEngine(storage)

        storage.index_file("test/repo", "main.py",
                           "def hello(name):\n    print(f'Hello {name}')\n    return name")
        storage.index_file("test/repo", "utils.py",
                           "def parse_file(path):\n    with open(path) as f:\n        return f.read()")

        # Basic search
        results = engine.search_code("hello")
        assert len(results) >= 1
        assert results[0].file_path == "main.py"

        # Repo filter
        results = engine.search_code("hello", repo="test/repo")
        assert len(results) >= 1
        assert all(r.repo == "test/repo" for r in results)

        # Empty search
        results = engine.search_code("zzzzz")
        assert len(results) == 0

    finally:
        storage.close()
        os.unlink(db_path)


def test_search_history():
    """Search history via SearchEngine."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        storage = Storage(db_path)
        engine = SearchEngine(storage)

        # Record a search
        repo = RepoInfo(name="test/repo", url="https://github.com/test/repo",
                        language="python", indexed_at="2026-08-01T00:00:00Z")
        engine.record_search("电商web", repo)

        # Check history
        history = engine.get_search_history("电商web")
        assert len(history) == 1
        assert history[0].repo_name == "test/repo"

        # Check categories
        cats = engine.get_all_categories()
        assert "电商web" in cats

        # Latest index time
        latest = engine.get_latest_index_time("电商web")
        assert latest == "2026-08-01T00:00:00Z"

    finally:
        storage.close()
        os.unlink(db_path)


def test_get_stats():
    """Get engine stats."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        storage = Storage(db_path)
        engine = SearchEngine(storage)

        storage.index_file("test/repo", "main.py", "content")
        stats = engine.get_stats()
        assert stats["files"] == 1

    finally:
        storage.close()
        os.unlink(db_path)


if __name__ == "__main__":
    test_search_code()
    test_search_history()
    test_get_stats()
    print("All search engine tests passed!")