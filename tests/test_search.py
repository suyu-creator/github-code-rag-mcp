"""Tests for the search + read tools — connector parsing + MCP tool formatting."""
import base64
import os
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.models import RepoInfo
from github.connector import GitHubConnector, RateLimitError
from server import mcp_server


# ── GitHubConnector.search_repos ─────────────────────────────────────

def test_search_repos_parses_response(monkeypatch):
    connector = GitHubConnector(github_token="test")

    def fake_api_request(url):
        assert "sort=stars" in url
        assert "per_page=5" in url
        return {"items": [
            {"full_name": "tiangolo/fastapi", "html_url": "https://github.com/tiangolo/fastapi",
             "language": "Python", "stargazers_count": 80000, "description": "FastAPI framework"},
        ]}

    monkeypatch.setattr(connector, "_api_request", fake_api_request)

    repos = connector.search_repos("fastapi", limit=5)
    assert repos is not None
    assert len(repos) == 1
    assert repos[0].name == "tiangolo/fastapi"
    assert repos[0].stars == 80000
    assert repos[0].language == "Python"


def test_search_repos_network_unavailable(monkeypatch):
    connector = GitHubConnector()
    monkeypatch.setattr(connector, "_api_request", lambda url: None)
    assert connector.search_repos("x") is None


def test_search_repos_rate_limit_propagates(monkeypatch):
    connector = GitHubConnector()

    def raise_rate(url):
        raise RateLimitError("GitHub API rate limit exceeded")

    monkeypatch.setattr(connector, "_api_request", raise_rate)
    try:
        connector.search_repos("x")
        raise AssertionError("should have raised RateLimitError")
    except RateLimitError:
        pass


# ── search_github tool ───────────────────────────────────────────────

class FakeConnector:
    def __init__(self, repos):
        self._repos = repos

    def search_repos(self, query, limit=10):
        return self._repos


def test_search_github_formats_output(monkeypatch):
    repo = RepoInfo(name="tiangolo/fastapi", url="https://github.com/tiangolo/fastapi",
                    language="Python", stars=80000, description="FastAPI framework")
    monkeypatch.setattr(mcp_server, "_github", FakeConnector([repo]))

    out = mcp_server.search_github("fastapi", limit=5)
    assert "tiangolo/fastapi" in out
    assert "URL: https://github.com/tiangolo/fastapi" in out
    assert "Language: Python" in out
    assert "⭐ 80000 stars" in out
    assert "FastAPI framework" in out


def test_search_github_no_results(monkeypatch):
    monkeypatch.setattr(mcp_server, "_github", FakeConnector([]))
    assert "没有找到匹配" in mcp_server.search_github("zzz")


def test_search_github_rate_limit_message(monkeypatch):
    class RateLimited:
        def search_repos(self, query, limit=10):
            raise RateLimitError("limit")

    monkeypatch.setattr(mcp_server, "_github", RateLimited())
    out = mcp_server.search_github("fastapi")
    assert "web_search_github" in out
    assert "GITHUB_TOKEN" in out


# ── web_search_github tool ───────────────────────────────────────────

SAMPLE_PAGE = (
    '<div data-testid="results-list">'
    '<div class="Result-module__Result">'
    '<a href="/tiangolo/fastapi">'
    '<div class="search-title"><a href="/tiangolo/fastapi">fastapi</a></div>'
    '<div class="Content-module__Content"><p>FastAPI framework</p></div>'
    '<a href="/tiangolo/fastapi/stargazers" class="stargazersLink">80k</a>'
    '<span aria-label="Python language">Python</span>'
    '</div>'
    '</div>'
)


class FakeResp:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return SAMPLE_PAGE.encode("utf-8")


def test_web_search_github_parses_html(monkeypatch):
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=20: FakeResp())

    out = mcp_server.web_search_github("fastapi")
    assert "tiangolo/fastapi" in out
    assert "https://github.com/tiangolo/fastapi" in out
    assert "FastAPI framework" in out
    assert "Python" in out


def test_web_search_github_missing_marker(monkeypatch):
    class EmptyResp(FakeResp):
        def read(self):
            return b"<html>no results list</html>"

    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=20: EmptyResp())
    assert "无法解析" in mcp_server.web_search_github("fastapi")


def test_web_search_github_network_error(monkeypatch):
    def boom(req, timeout=20):
        raise OSError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    assert "不可达" in mcp_server.web_search_github("fastapi")


# ── GitHubConnector.read_file ────────────────────────────────────────

def test_connector_read_file_decodes_base64(monkeypatch):
    connector = GitHubConnector()
    raw = "def hello():\n    print('hi')\n"
    encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
    monkeypatch.setattr(connector, "_api_request", lambda url: {
        "content": encoded,
        "encoding": "base64",
    })

    assert connector.read_file("https://github.com/owner/repo", "main.py") == raw


def test_connector_read_file_missing(monkeypatch):
    connector = GitHubConnector()
    monkeypatch.setattr(connector, "_api_request", lambda url: None)
    assert connector.read_file("https://github.com/owner/repo", "nope.py") is None


def test_connector_parse_repo_name():
    assert GitHubConnector.parse_repo_name("https://github.com/tiangolo/fastapi") == "tiangolo/fastapi"


# ── read_github_file tool ────────────────────────────────────────────

def test_read_github_file_formats_output(monkeypatch):
    connector = GitHubConnector()
    encoded = base64.b64encode("print('hello')".encode("utf-8")).decode("ascii")
    monkeypatch.setattr(connector, "_api_request", lambda url: {
        "content": encoded,
        "encoding": "base64",
    })
    monkeypatch.setattr(mcp_server, "_github", connector)

    out = mcp_server.read_github_file("https://github.com/tiangolo/fastapi", "main.py")
    assert "Source: tiangolo/fastapi/main.py" in out
    assert "print('hello')" in out


def test_read_github_file_error(monkeypatch):
    connector = GitHubConnector()
    monkeypatch.setattr(connector, "_api_request", lambda url: None)
    monkeypatch.setattr(mcp_server, "_github", connector)

    assert "无法读取" in mcp_server.read_github_file("https://github.com/x/y", "nope.py")


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
