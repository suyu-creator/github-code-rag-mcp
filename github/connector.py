"""GitHub repository connector for browsing and reading files via API.

No git clone needed. Uses GitHub REST API directly.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from core.models import RepoInfo


class RateLimitError(Exception):
    """Raised when GitHub API rate limit is hit."""
    pass


class GitHubConnector:
    """Browse GitHub repos and read files via REST API."""

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
            if e.code == 404:
                return None
            if e.code == 403:
                # 403 can mean rate-limit OR a blocked repo / abuse detection.
                # Only treat it as rate limiting when the header confirms the
                # quota is actually exhausted; otherwise surface as None.
                remaining = e.headers.get("X-RateLimit-Remaining", "")
                if remaining.isdigit() and int(remaining) == 0:
                    raise RateLimitError("GitHub API rate limit exceeded")
                return None
            return None
        except (urllib.error.URLError, TimeoutError, OSError):
            return None  # Network unavailable

    def _get_default_branch(self, owner: str, repo: str) -> str:
        """Get the default branch for a repo."""
        data = self._api_request(
            f"https://api.github.com/repos/{owner}/{repo}"
        )
        if data:
            return data.get("default_branch", "main")
        return "main"

    # ── File browsing ─────────────────────────────────────────────────

    def list_files(self, url: str, path: str = "") -> Optional[List[Dict[str, Any]]]:
        """List files and directories in a GitHub repository path.

        Args:
            url: GitHub repository URL (e.g. https://github.com/owner/repo)
            path: Subdirectory path (empty for root)

        Returns:
            List of {name, type, path} dicts, or None on error
        """
        owner, repo, ref, extracted_path = self.parse_repo_url(url)
        if not path:
            path = extracted_path

        api_path = path.strip("/")
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{api_path}" if api_path else f"https://api.github.com/repos/{owner}/{repo}/contents"
        if ref:
            api_url += f"?ref={urllib.parse.quote(ref)}"

        result = self._api_request(api_url)
        if result is None:
            return None

        items = []
        for item in result if isinstance(result, list) else [result]:
            name = item.get("name", "")
            item_type = item.get("type", "")
            item_path = item.get("path", "")
            items.append({
                "name": name,
                "type": item_type,  # "file" or "dir"
                "path": item_path,
            })

        return items

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
        """Search GitHub for repositories matching the query.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of RepoInfo, or None if network unavailable
        """
        url = (
            f"https://api.github.com/search/repositories"
            f"?q={urllib.parse.quote(query)}&sort=stars&per_page={limit}"
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
                file_count=0,
            ))
        return repos