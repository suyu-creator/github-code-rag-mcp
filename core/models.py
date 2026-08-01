"""Data models for the GitHub Code Search system."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SearchHistory:
    """Record of a search query and what repos were found for that category.

    Each time a user searches a category (e.g. "电商web"), the repos found
    and indexed are recorded here. Next time the same category is searched,
    only repos after the last indexed_at are fetched.
    """
    category: str          # User's search category: "电商web", "点餐小程序"
    repo_name: str         # "owner/repo"
    repo_url: str = ""
    language: str = ""
    indexed_at: str = ""   # ISO timestamp of when this was indexed


@dataclass
class SearchResult:
    """A search result from FTS5 code search."""
    repo: str
    file_path: str
    language: str
    snippet: str           # Matched content preview
    score: float = 0.0
    matched_by: str = "fts5"


@dataclass
class RepoInfo:
    """Information about an indexed repository."""
    name: str
    url: str = ""
    language: str = ""
    indexed_at: str = ""
    file_count: int = 0
    stars: int = 0
    description: str = ""