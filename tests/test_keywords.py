"""Tests for Chinese → English keyword normalization in repo search."""
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from github.connector import GitHubConnector
from github.keywords import (
    build_search_query,
    ensure_star_filter,
    normalize_query,
)


# ── normalize_query ───────────────────────────────────────────────────

def test_normalize_passes_english_through():
    assert normalize_query("fastapi") == "fastapi"
    assert normalize_query("ecommerce react stars:>1000") == "ecommerce react stars:>1000"


def test_normalize_translates_chinese_term():
    assert normalize_query("电商网站 React") == "ecommerce React"


def test_normalize_translates_compound_terms():
    assert "mini program" in normalize_query("小程序 电商 后端")
    assert "llm" in normalize_query("大模型 微调 工具")
    assert "fine-tuning" in normalize_query("大模型 微调 工具")


def test_normalize_degrades_when_no_mapping():
    # 全表外词：降级返回原样，绝不静默丢查询
    assert normalize_query("微信") == "微信"


def test_normalize_removes_unmapped_chinese_around_mapped():
    assert normalize_query("python 爬虫 抖音") == "python crawler"


# ── ensure_star_filter ───────────────────────────────────────────────

def test_star_filter_appended_when_missing():
    assert ensure_star_filter("ecommerce react") == "ecommerce react stars:>50"


def test_star_filter_not_appended_when_present():
    assert ensure_star_filter("ecommerce react stars:>1000") == "ecommerce react stars:>1000"


# ── build_search_query ───────────────────────────────────────────────

def test_build_chinese_query_marks_translated():
    q, changed = build_search_query("电商网站 React")
    assert changed is True
    assert q == "ecommerce React stars:>50"


def test_build_english_query_untouched():
    q, changed = build_search_query("fastapi")
    assert changed is False
    assert q == "fastapi"


def test_build_unknown_chinese_untouched():
    q, changed = build_search_query("微信")
    assert changed is False
    assert q == "微信"


def test_build_is_idempotent():
    # 已规范化的结果再走一遍不应再变，避免双份 star 过滤
    q1, _ = build_search_query("电商网站 React")
    q2, _ = build_search_query(q1)
    assert q1 == q2


# ── connector integration ────────────────────────────────────────────

def test_search_repos_translates_chinese_in_url(monkeypatch):
    connector = GitHubConnector(github_token="test")
    captured = {}

    def fake_api_request(url):
        captured["url"] = url
        return {"items": [
            {"full_name": "medusajs/medusa", "html_url": "https://github.com/medusajs/medusa",
             "language": "TypeScript", "stargazers_count": 36000, "description": "commerce"},
        ]}

    monkeypatch.setattr(connector, "_api_request", fake_api_request)
    connector.search_repos("电商网站 React", limit=5)

    query = urllib.parse.parse_qs(urllib.parse.urlparse(captured["url"]).query)["q"][0]
    assert "ecommerce" in query
    assert "React" in query
    assert "stars:>50" in query
    assert "电商" not in query


def test_search_repos_keeps_english_query(monkeypatch):
    connector = GitHubConnector()
    captured = {}

    def fake_api_request(url):
        captured["url"] = url
        return {"items": []}

    monkeypatch.setattr(connector, "_api_request", fake_api_request)
    connector.search_repos("fastapi", limit=5)
    assert "fastapi" in captured["url"]
