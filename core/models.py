"""Data models for the GitHub Code Search system."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RepoInfo:
    """Information about a repository returned by GitHub search."""
    name: str          # "owner/repo"
    url: str = ""
    language: str = ""
    stars: int = 0
    description: str = ""
