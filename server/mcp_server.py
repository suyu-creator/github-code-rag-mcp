"""MCP Server for GitHub repository search + file reading — no git clone.

Workflow:
1. search_github("电商") → find repos (GitHub API, 60次/时无token)
2. web_search_github("电商") → fallback 搜索 (GitHub 官方搜索页, 免费无限)
3. read_github_file(url, path) → read file content, LLM copies what it needs
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from mcp.server.fastmcp import FastMCP

from github.connector import GitHubConnector, RateLimitError
from github.keywords import build_search_query

logger = logging.getLogger("code_rag.server")

# ── Global State ────────────────────────────────────────────────────

_github: Optional[GitHubConnector] = None

# ── MCP Server ──────────────────────────────────────────────────────

# Resolve FastMCP's internal Settings forward refs so pydantic-settings
# does not print an IncompleteFieldDefinitionWarning to stderr at startup.
# On CJK Windows that stderr is GBK-encoded (non-UTF-8) and makes the MCP
# client abort the stdio handshake, so keep stderr clean.
from mcp.server.fastmcp.server import Settings

Settings.model_rebuild()
logging.getLogger("mcp").setLevel(logging.WARNING)

mcp = FastMCP(
    "github-code-rag",
    instructions="""# 需求分析 Agent - 先判断再搜

## 角色
你是一位资深需求分析师。用户提出想法后,先判断需求清晰度:明确就直接搜 GitHub,不明确就先问 1-2 个小问题澄清,再搜 GitHub。基于搜索结果向用户提问,逐步明确需求。

## 核心工作流

### Step 0: 需求清晰度判断(必执行)

判断用户需求的明确程度:

- **明确**(用户说了具体功能 + 平台/规模/技术栈任一) -> 直接进 Step 1 搜索
  - 例:"做个小程序电商,日单 1k" -> 明确,直接搜
  - 例:"用 React 做个博客系统" -> 明确,直接搜
- **不明确**(只说"做个 XX",没说平台/规模/技术栈) -> 先问 1-2 个小问题,用户回答后再进 Step 1
  - 例:"做个电商" -> 不明确,问"Web/小程序/App?"
  - 例:"做个工具" -> 不明确,问"什么类型的工具?"

⚠️ 不明确时,只问 1-2 个**最关键的小问题**(平台/规模/类型),不要一次问 5 个。用户回答后立即进 Step 1 搜索。

### Step 1: 搜 GitHub

1. **search_github(query)** — 在 GitHub 搜仓库(GitHub API,按 star 排序,质量最高)
2. 如果 search_github 限流或搜不到 -> **web_search_github(query)** — 用 GitHub 官方搜索页(免费无限额度)
3. 结果不理想就换关键词重搜,必要时带上语言/规模关键词,如 "python"、"stars:>1000"
4. 用户想看某个仓库的具体实现 -> **read_github_file(url, path)** — 读仓库中某个文件的内容(自动标注来源,可直接复用)

### Step 2: 基于搜索结果提问

#### 模式 A:用户已有明确需求
- 直接确认找到的项目是否匹配用户要求
- 聚焦在"这个项目是否符合你的要求"

#### 模式 B:用户没有具体需求
- 先给概览:"我找到了 X 个相关项目,分别用了不同的技术方案"
- 每次只问一个问题,每个问题带选项并附上括号简述优劣
- 每个选项列表最后加一个选项:我来根据 GitHub 项目给你推荐
- 用大白话,避免技术术语
- 用户没提项目规模(多少人用)时,搜的时候带上规模关键词
- 用户回答后,如果之前找到的项目不符合新要求,重新搜索

### Step 3: 需求验证
- 整理需求摘要(问题描述、范围、约束、假设)
- 简要告知用户找到了哪些可参考的项目(只说项目名和主要特点)
- 请用户确认或提出修改意见,用户确认后停止追问

## 关键规则
1. **先判断清晰度,再搜** — 需求明确直接搜 GitHub;需求不明确先问 1-2 个小问题,再搜
2. **一次只问一个问题** — 等用户回答后再问下一个
3. **复用优先** — 能找到现成实现就不要从零写;给用户推荐最相关的开源项目
   错误做法:用户说"做个电商",直接开始写代码
   正确做法:先搜 GitHub 找到同类项目,给用户推荐参考
4. **用户最新说的为准** — 约束条件以用户最新修改为准
5. **用户没提规模时,搜的时候带上不同规模的关键词去匹配**
6. **只汇报工具实际返回的内容** — 不要编造不存在的仓库、star 数或描述
7. **强烈优先用 MCP 自带工具**（search_github / web_search_github / read_github_file）— 质量高、免手动解析;不强制禁用 gh CLI / curl,但 MCP 不可用时才用它们兜底

## 禁止行为
- 不要一次问多个问题
- 不要输出长篇技术解释(除非用户要求)
- ⚠️ 需求不明确时不要硬猜,先问 1-2 个小问题
""",
)


# ── Tools ───────────────────────────────────────────────────────────

@mcp.tool()
def search_github(query: str, limit: int = 10) -> str:
    """在 GitHub 搜索仓库，返回仓库 URL。

    这是搜索 GitHub 的首选途径，强烈优先使用本工具;不强制禁用 gh CLI / curl,
    但 MCP 工具不可用时才用它们兜底。按 star 排序，优先找到最成熟的项目。

    中文关键词会自动翻译成英文技术关键词并追加 star 过滤（如 "电商网站" →
    "ecommerce stars:>50"），因为 GitHub 对中文相关性排序不可靠。

    Args:
        query: Search keywords (中文或英文均可，可带筛选如 "python stars:>1000")
        limit: Maximum results (default: 10, max: 30)
    """
    global _github

    if _github is None:
        _github = GitHubConnector()

    limit = min(limit, 30)

    final_query, was_translated = build_search_query(query)

    try:
        repos = _github.search_repos(final_query, limit=limit)
    except RateLimitError:
        return (
            "GitHub API 额度已用完，没有 token 的话每小时只能搜 60 次。\n\n"
            "请选择：\n"
            "1. 配置 GITHUB_TOKEN（推荐，5000次/时）— 去 https://github.com/settings/tokens 生成\n"
            "2. 用内置的 web_search_github 工具替代（免费，无需配置）"
        )
    except Exception as e:
        return f"搜索出错: {e}"

    if repos is None:
        return "GitHub API 不可达（网络问题或代理未配置）。请检查网络连接后重试。"

    if not repos:
        return "没有找到匹配的仓库，试试其他关键词。"

    header = f"GitHub 搜索结果: {final_query}\n"
    if was_translated:
        header += f"   (中文关键词 \"{query}\" 已自动转为英文关键词 + star 过滤)\n"
    output = [header]
    for i, repo in enumerate(repos, 1):
        output.append(
            f"{i}. {repo.name}\n"
            f"   URL: {repo.url}\n"
        )
        if repo.language:
            output.append(f"   Language: {repo.language}\n")
        parts = []
        if repo.stars:
            parts.append(f"⭐ {repo.stars} stars")
        if repo.description:
            parts.append(repo.description[:300])
        if parts:
            output.append(f"   {' | '.join(parts)}\n")
        output.append("\n")

    output.append("下一步：选定仓库后可用 read_github_file(url, path) 读代码；结果不理想就换关键词重搜。")
    return "".join(output)


@mcp.tool()
def web_search_github(query: str, limit: int = 10) -> str:
    """通过 GitHub 官方搜索页搜索开源项目（免费，无需 API Key，无限额度）。

    当 search_github 限流时用这个替代。搜索 GitHub 上的仓库。
    解析 github.com/search 的 HTML 结果页，不依赖第三方搜索引擎。

    Args:
        query: 搜索关键词 (如 "电商网站 React")
        limit: 返回结果数 (default: 10, max: 20)
    """
    import html
    import re
    import urllib.parse
    import urllib.request

    def _clean(t: str) -> str:
        t = re.sub(r"<[^>]+>", "", t)
        return html.unescape(t).strip()

    limit = min(limit, 20)
    url = f"https://github.com/search?q={urllib.parse.quote(query)}&type=repositories"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            page = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"GitHub 搜索页不可达: {type(e).__name__}: {e}"

    marker = 'data-testid="results-list"'
    if marker not in page:
        return f"无法解析 GitHub 搜索结果: {query}（页面结构可能已变化）"

    results = []
    blocks = re.split(r'<div class="Result-module__Result', page.split(marker, 1)[1])
    for block in blocks[1:limit + 1]:
        href_match = re.search(r'<a[^>]*href="/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"', block)
        if not href_match:
            continue
        repo = href_match.group(1)
        title_match = re.search(r'search-title[^>]*>\s*<a[^>]*>(.*?)</a>', block, re.DOTALL)
        desc_match = re.search(r'Content-module__Content[^>]*>(.*?)</div>', block, re.DOTALL)
        star_match = re.search(r'stargazersLink[^>]*>(.*?)</a>', block, re.DOTALL)
        lang_match = re.search(r'aria-label="([^"]*language[^"]*)"', block)
        results.append({
            "repo": repo,
            "url": f"https://github.com/{repo}",
            "title": _clean(title_match.group(1)) if title_match else repo,
            "description": _clean(desc_match.group(1)) if desc_match else "",
            "stars": _clean(star_match.group(1)) if star_match else "",
            "language": _clean(lang_match.group(1).replace("language", "")) if lang_match else "",
        })

    if not results:
        return f"GitHub 上没有找到匹配的仓库: {query}"

    output = [f"GitHub 网页搜索结果: {query}\n"]
    for i, r in enumerate(results, 1):
        output.append(f"{i}. {r['title']}\n")
        output.append(f"   URL: {r['url']}\n")
        if r["language"]:
            output.append(f"   Language: {r['language']}\n")
        parts = []
        if r["stars"]:
            parts.append(f"⭐ {r['stars']} stars")
        if r["description"]:
            parts.append(r["description"][:300])
        if parts:
            output.append(f"   {' | '.join(parts)}\n")
        output.append("\n")

    output.append("下一步：选定仓库后可用 read_github_file(url, path) 读代码；结果不理想就换关键词重搜。")
    return "".join(output)


@mcp.tool()
def read_github_file(url: str, path: str) -> str:
    """读取 GitHub 仓库中某个文件的内容。

    搜到仓库后，用本工具读关键文件了解实现思路。
    读到的代码可以直接复用，需要在代码中标注来源。

    Args:
        url: 仓库 URL (如 https://github.com/owner/repo)
        path: 文件路径 (如 "src/main.py")
    """
    global _github

    if _github is None:
        _github = GitHubConnector()

    content = _github.read_file(url, path)
    if content is None:
        return f"无法读取文件: {path}，请检查路径是否正确。"

    lines = content.split("\n")
    max_lines = 500
    truncated = len(lines) > max_lines
    shown = "\n".join(lines[:max_lines])
    if truncated:
        shown += f"\n\n... (文件共 {len(lines)} 行，只显示前 {max_lines} 行)"

    return (
        f"# {path}\n"
        f"# Source: {_github.parse_repo_name(url)}/{path}\n"
        f"# 文件大小: {len(content)} 字符, {len(lines)} 行\n\n"
        f"{shown}\n\n"
        f"---\n"
        f"下一步：继续用 read_github_file 读其他文件，或用 search_github 搜其他仓库。"
    )


# ── Main (for direct execution) ─────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="GitHub Repo Search MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio")

    args = parser.parse_args()
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
