"""GitHub repository connector — search repos and read files via REST API.

No git clone needed. Uses GitHub REST API directly.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, List, Optional, Tuple
from urllib.parse import urlparse

from core.models import RepoInfo

from github.keywords import build_search_query


class RateLimitError(Exception):
    """Raised when GitHub API rate limit is hit."""
    pass


class GitHubConnector:
    """Search GitHub repositories and read files via the REST API."""

    def __init__(self, github_token: str = ""):
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN", "")
        self._headers = {"Accept": "application/vnd.github.v3+json"}
        if self.github_token:
            self._headers["Authorization"] = f"Bearer {self.github_token}"

    # ── URL parsing ───────────────────────────────────────────────────

    @staticmethod
    def parse_repo_url(url: str) -> Tuple[str, str, str, str]:
        """Parse GitHub URL into (owner, repo, path, ref).

        Handles formats:
          https://github.com/owner/repo
          https://github.com/owner/repo/tree/main/src
          https://github.com/owner/repo/blob/main/file.py
        """
        path = urlparse(url).path.strip("/")
        parts = path.split("/")

        owner = parts[0] if len(parts) > 0 else ""
        repo = parts[1] if len(parts) > 1 else ""
        ref = ""
        file_path = ""

        if len(parts) > 2 and parts[2] in ("tree", "blob"):
            # /owner/repo/tree/main/path or /owner/repo/blob/main/path
            ref = parts[3] if len(parts) > 3 else ""
            file_path = "/".join(parts[4:]) if len(parts) > 4 else ""

        return owner, repo, ref, file_path

    @staticmethod
    def parse_repo_name(url: str) -> str:
        """Extract owner/repo name from GitHub URL."""
        path = urlparse(url).path.strip("/")
        parts = path.split("/")
        return f"{parts[0]}/{parts[1]}" if len(parts) >= 2 else path

    # ── API helpers ───────────────────────────────────────────────────

    def _api_request(self, url: str) -> Optional[Any]:
        """Make a GitHub API request with error handling."""
        req = urllib.request.Request(url, headers=self._headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 403:
                # 403 can mean rate-limit OR a blocked repo / abuse detection.
                # Only treat it as rate limiting when the header confirms the
                # quota is actually exhausted; otherwise surface as None.
                remaining = e.headers.get("X-RateLimit-Remaining", "")
                if remaining.isdigit() and int(remaining) == 0:
                    raise RateLimitError("GitHub API rate limit exceeded")
            return None
        except (urllib.error.URLError, TimeoutError, OSError):
            return None  # Network unavailable

    # ── File reading ──────────────────────────────────────────────────

    def read_file(self, url: str, path: str) -> Optional[str]:
        """Read a file's content from a GitHub repository.

        Args:
            url: GitHub repository URL (e.g. https://github.com/owner/repo)
            path: File path within the repo (e.g. "src/main.py")

        Returns:
            File content as string, or None on error
        """
        owner, repo, ref, _ = self.parse_repo_url(url)

        api_path = f"https://api.github.com/repos/{owner}/{repo}/contents/{path.strip('/')}"
        if ref:
            api_path += f"?ref={urllib.parse.quote(ref)}"
        result = self._api_request(api_path)

        if result is None or not isinstance(result, dict):
            return None

        content = result.get("content", "")
        encoding = result.get("encoding", "")

        if encoding == "base64" and content:
            try:
                decoded = base64.b64decode(content).decode("utf-8", errors="replace")
                return decoded
            except Exception:
                return None

        return None

    # ── Repo search ───────────────────────────────────────────────────

    def search_repos(
        self, query: str, limit: int = 10
    ) -> Optional[List[RepoInfo]]:
        """Search GitHub for repositories matching the query, sorted by stars.

        Args:
            query: Search query (Chinese terms are auto-translated to English)
            limit: Maximum results

        Returns:
            List of RepoInfo, or None if network unavailable
        """
        final_query, _ = build_search_query(query)
        url = (
            f"https://api.github.com/search/repositories"
            f"?q={urllib.parse.quote(final_query)}&sort=stars&per_page={limit}"
        )

        data = self._api_request(url)
        if data is None:
            return None  # 网络不可达

        repos = []
        for item in data.get("items", [])[:limit]:
            repos.append(RepoInfo(
                name=item["full_name"],
                url=item["html_url"],
                language=item.get("language") or "",
                stars=item.get("stargazers_count", 0),
                description=item.get("description") or "",
            ))
        return repos
