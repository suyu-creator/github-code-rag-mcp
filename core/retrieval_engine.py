"""Simple FTS5 search engine — no knowledge graph, no vectors.

Just FTS5 full-text search on indexed file content.
Reference: dinosn/claude-recall — zero-dep FTS5 + RRF pattern
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from core.models import RepoInfo, SearchHistory, SearchResult

if TYPE_CHECKING:
    from storage.sqlite_storage import Storage


class SearchEngine:
    """FTS5-based search engine for indexed code."""

    def __init__(self, storage: Storage):
        self.storage = storage

    # ── Code search ─────────────────────────────────────────────────

    def search_code(
        self, query: str, top_k: int = 10, repo: Optional[str] = None
    ) -> List[SearchResult]:
        """Search indexed code using FTS5.

        Args:
            query: Search keywords
            top_k: Number of results
            repo: Optional repo filter

        Returns:
            List of SearchResult
        """
        return self.storage.search_code(query, top_k=top_k, repo=repo)

    # ── Search history ───────────────────────────────────────────────

    def get_search_history(self, category: str) -> List[SearchHistory]:
        """Get all repos indexed for a category."""
        return self.storage.get_search_history(category)

    def get_all_categories(self) -> List[str]:
        """Get all search categories."""
        return self.storage.get_all_categories()

    def get_latest_index_time(self, category: str) -> Optional[str]:
        """Get the most recent index time for a category."""
        return self.storage.get_latest_index_time(category)

    def record_search(self, category: str, repo: RepoInfo) -> None:
        """Record a repo indexed for a category."""
        self.storage.record_search(category, repo)

    # ── Repo management ──────────────────────────────────────────────

    def list_indexed_repos(self) -> List[RepoInfo]:
        return self.storage.list_indexed_repos()

    def get_stats(self) -> dict:
        return self.storage.get_stats()