"""MCP Server for GitHub Code Reading — browse & read files via API, no git clone.

Workflow:
1. search_github("电商") → find repos (GitHub API, 60次/时无token)
2. web_search_github("电商") → fallback 搜索 (GitHub 官方搜索页, 免费无限)
3. list_github_files(url) → browse repo structure
4. read_github_file(url, path) → read file content, LLM copies what it needs
5. search_code(query) → search across previously read files
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from mcp.server.fastmcp import FastMCP

from core.models import RepoInfo
from core.retrieval_engine import SearchEngine
from github.connector import GitHubConnector
from storage.sqlite_storage import Storage

logger = logging.getLogger("code_rag.server")

# ── Global State ────────────────────────────────────────────────────

_engine: Optional[SearchEngine] = None
_storage: Optional[Storage] = None
_github: Optional[GitHubConnector] = None

# ── MCP Server ──────────────────────────────────────────────────────

mcp = FastMCP(
    "github-code-rag",
    instructions="""# 需求分析 Agent - 先判断再搜或问

## 角色
你是一位资深需求分析师 + 代码研究员。用户提出想法后,**先判断需求清晰度**:明确就直接搜 GitHub,不明确就先问 1-2 个小问题澄清,再搜 GitHub。基于搜索结果向用户提问,逐步明确需求。

## 核心工作流

### Step 0: 需求清晰度判断(新增,必执行)

判断用户需求的明确程度:

- **明确**(用户说了具体功能 + 平台/规模/技术栈任一) -> 直接进 Step 1 搜索
  - 例:"做个小程序电商,日单 1k" -> 明确,直接搜
  - 例:"用 React 做个博客系统" -> 明确,直接搜
- **不明确**(只说"做个 XX",没说平台/规模/技术栈) -> 先问 1-2 个小问题,用户回答后再进 Step 1
  - 例:"做个电商" -> 不明确,问"Web/小程序/App?"
  - 例:"做个工具" -> 不明确,问"什么类型的工具?"

⚠️ 不明确时,只问 1-2 个**最关键的小问题**(平台/规模/类型),不要一次问 5 个。用户回答后立即进 Step 1 搜索。

### Step 1: 先搜再看(GitHub)

**Step 0 判断为"明确"或用户已回答澄清问题后,按以下顺序执行(不允许跳过):**

1. **必须先调 search_history("XX")** — 查之前有没有读过同类项目，**不允许跳过此步直接去搜**
2. 想查看数据库里有什么表和数据 → **db_inspect()** — 查看所有表结构、字段、记录数
3. 有记录 → **search_code("关键词")** — 搜已读代码
4. 没找到 → **search_github("XX")** — 在 GitHub 搜仓库（GitHub API，有限额）
5. 如果 search_github 限流 → **web_search_github("XX")** — 用 GitHub 官方搜索页（免费无限）
6. **list_github_files(url)** — 浏览仓库目录结构
7. **read_github_file(url, path)** — 读关键文件，了解实现思路

### Step 2: 基于搜索结果提问

#### 模式 A：用户已有明确需求
- 直接确认找到的项目是否匹配用户要求
- 不需要问基础问题，聚焦在"这个项目是否符合你的要求"

#### 模式 B：用户没有具体需求
- 先给概览："我找到了 X 个相关项目，分别用了不同的技术方案"
- 每次只问一个问题，每个问题带选项并附上括号简述优劣
- 每个选项列表最后加一个选项：我来根据 GitHub 项目给你推荐
- 用大白话，避免技术术语
- 如果用户回答后，之前找到的项目不符合新要求，重新去 GitHub 搜
- 用户没提项目规模（多少人用），搜的时候带上规模关键词

示例：
  "你要做 web 还是移动端？
   - Web（开发快、跨平台）
   - 移动端（原生体验好、需双端开发）
   - 我来根据 GitHub 项目给你推荐"

### Step 3: 需求验证
- 整理需求摘要（问题描述、范围、约束、假设）
- 简要告知用户找到了哪些可参考的项目（只说项目名和主要特点，不展示代码）
- 请用户确认或提出修改意见
- 用户确认后，进入 UI 确认

### Step 3.5: UI 设计确认
- 询问用户对 UI 有没有偏好，给选项并附上优劣简述
- 最后加一个选项：我来根据 GitHub 项目给你推荐

示例：
  "UI 风格有偏好吗？
   - 简洁现代（开发快、通用性强）
   - 玻璃拟态（视觉炫酷、动效多）
   - 极简/毛胚（加载快、内容优先）
   - 我来根据 GitHub 项目给你推荐"

- 用户选择后，去 GitHub 搜对应风格的 UI 项目/组件库
  - 先看 Step 1 找到的项目是否本身就符合该 UI 风格，符合就直接用
  - 不符合或不满意，就去 GitHub 专门搜该风格的 UI 参考
- 给用户简要反馈结果，不展示代码

### Step 4: 直接输出结果
- 问题描述
- 核心约束（预算、技术栈、平台、规模等）
- 功能需求列表
- 非功能需求列表
- 可参考的开源项目 / 代码资源
- 假设列表
- 风险评估

## 关键规则
1. **先判断清晰度,再搜或问** — 需求明确直接搜 GitHub;需求不明确先问 1-2 个小问题,再搜
2. **必须先调 search_history** — 进入 Step 1 搜索时,第一步必须是 search_history,不允许跳过
3. **一次只问一个问题** — 等用户回答后再问下一个
3. **复用优先** — 能找到现成实现就不要从零写
   错误做法：用户说"做个电商"，直接开始写代码
   正确做法：先搜 GitHub 找到同类项目，参考或复用
   违反此规则 = 无效输出
4. **标注来源** — 引用代码时标注 `# Source: owner/repo/file.py`
5. **用户确认后停止追问** — 用户说"是/可以"就结束验证
6. **默认可行** — 除非真的不可能，否则标记为可行
7. **用户最新说的为准** — 约束条件以用户最新修改为准
8. **UI 确认后必须去 GitHub 找参考** — 先看已有项目是否符合，不符合再搜
9. **用户补充新需求后，如果之前找到的项目不匹配，必须重新搜索**
10. **用户没提规模时，搜的时候带上不同规模的关键词去匹配**

## 禁止行为
- **不要跳过 search_history 直接搜 GitHub**
- 不要一次问多个问题
- 不要输出长篇技术解释（除非用户要求）
- 不要用 gh CLI 或 curl 代替 MCP 工具
- ⚠️ 需求不明确时不要硬猜,先问 1-2 个小问题
""",
)


def _init_engine(data_dir: str):
    """Initialize the engine with FTS5 storage."""
    global _engine, _storage, _github

    os.makedirs(data_dir, exist_ok=True)
    db_path = os.path.join(data_dir, "code_rag.db")

    _storage = Storage(db_path)
    _engine = SearchEngine(storage=_storage)
    _github = GitHubConnector()


# ── Tools ───────────────────────────────────────────────────────────

@mcp.tool()
def list_github_files(url: str, path: str = "") -> str:
    """浏览 GitHub 仓库的文件列表。

    找到仓库后，用本工具看目录结构。找到文件后再用 read_github_file 读内容。
    禁止用 gh CLI 或 curl 代替。

    Args:
        url: 仓库 URL (来自 search_github 的结果，如 https://github.com/owner/repo)
        path: 子目录路径（留空看根目录）
    """
    global _github

    if _github is None:
        _github = GitHubConnector()

    items = _github.list_files(url, path)
    if items is None:
        return "无法访问该仓库，请检查 URL 是否正确或网络是否可达。"

    if not items:
        return f"目录为空: {path or '/'}"

    output = [f"📁 {path or '/'}\n"]
    dirs = [i for i in items if i["type"] == "dir"]
    files = [i for i in items if i["type"] == "file"]

    for d in dirs:
        output.append(f"  📁 {d['name']}/\n")
    for f in files:
        output.append(f"  📄 {f['name']}\n")

    output.append(f"\n共 {len(dirs)} 个目录, {len(files)} 个文件")
    output.append("\n\n下一步：进入子目录继续浏览，或用 read_github_file(url, path) 读文件内容")

    return "".join(output)


@mcp.tool()
def read_github_file(url: str, path: str) -> str:
    """读取 GitHub 仓库中某个文件的内容。

    读到的代码可以直接复用，需要在代码中标注来源。
    文件内容会自动索引到本地，之后可用 search_code 搜索。

    Args:
        url: 仓库 URL (如 https://github.com/owner/repo)
        path: 文件路径 (如 "src/main.py")
    """
    global _engine, _storage, _github

    if _github is None:
        _github = GitHubConnector()
    if _engine is None:
        data_dir = os.environ.get("CODE_RAG_DATA_DIR", os.path.expanduser("~/.code-rag"))
        _init_engine(data_dir)

    content = _github.read_file(url, path)
    if content is None:
        return f"无法读取文件: {path}，请检查路径是否正确。"

    # Auto-index for search_code
    try:
        repo_name = _github.parse_repo_name(url)
        now = __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime())
        _storage.save_repo_info(RepoInfo(
            name=repo_name,
            url=url,
            language="",
            indexed_at=now,
            file_count=0,
        ))
        _storage.index_file(repo_name, path, content)
        _storage.update_file_count(repo_name)
    except Exception:
        pass  # Indexing is best-effort

    # Truncate if too long
    lines = content.split("\n")
    max_lines = 500
    if len(lines) > max_lines:
        content = "\n".join(lines[:max_lines])
        content += f"\n\n... (文件共 {len(lines)} 行，只显示前 {max_lines} 行)"

    return (
        f"# {path}\n"
        f"# Source: {_github.parse_repo_name(url)}/{path}\n"
        f"# 文件大小: {len(content)} 字符, {len(lines)} 行\n\n"
        f"{content}\n\n"
        f"---\n"
        f"下一步：继续用 read_github_file 读其他文件，或用 search_code 搜已读代码。"
    )


@mcp.tool()
def search_code(
    query: str,
    repo: Optional[str] = None,
    top_k: int = 5,
) -> str:
    """在已读过的代码中搜索关键词。

    写代码前先搜一下有没有现成的实现，有就直接复用，禁止从零编写。
    只能搜到之前用 read_github_file 读过的文件。

    Args:
        query: Search keywords
        repo: Optional filter by repository name
        top_k: Number of results (default: 5, max: 20)
    """
    global _engine

    if _engine is None:
        data_dir = os.environ.get("CODE_RAG_DATA_DIR", os.path.expanduser("~/.code-rag"))
        _init_engine(data_dir)

    top_k = min(top_k, 20)
    results = _engine.search_code(query, top_k=top_k, repo=repo)

    if not results:
        return "没有找到匹配的代码。先用 search_github(query) 搜仓库，然后 list_github_files + read_github_file 读代码。"

    output = [f"找到 {len(results)} 个匹配: {query}\n"]
    for i, result in enumerate(results, 1):
        output.append(
            f"{i}. [{result.repo}] {result.file_path} ({result.language})\n"
            f"   Score: {result.score:.3f}\n"
        )
        if result.snippet:
            output.append(f"   ```\n{result.snippet}\n   ```\n")
        output.append("\n")

    return "".join(output)


@mcp.tool()
def search_history(category: str) -> str:
    """查询某个类别之前读过什么项目。

    用户说"做个XX"时，第一步调本工具查历史记录。
    有记录 → search_code 搜代码，无记录 → search_github 搜新仓库。

    Args:
        category: Search category (e.g. "电商web", "点餐小程序")
    """
    global _engine

    if _engine is None:
        return "数据库未初始化，还没有读过任何代码。"

    records = _engine.get_search_history(category)

    if not records:
        return (
            f"类别 '{category}' 还没有读过的项目。\n\n"
            "下一步：调用 search_github(query) 在 GitHub 上搜索相关仓库\n"
            "例如：search_github(\"" + category + "\")"
        )

    output = [f"类别 '{category}' 已读过的项目:\n"]
    for r in records:
        output.append(
            f"  - {r.repo_name}"
            + (f" ({r.language})" if r.language else "")
            + (f" @ {r.indexed_at}" if r.indexed_at else "")
            + "\n"
        )

    return "".join(output)


@mcp.tool()
def search_github(query: str, limit: int = 10) -> str:
    """在 GitHub 搜索仓库，返回仓库 URL。

    这是搜索 GitHub 的唯一途径，禁止使用 gh CLI 或 curl。
    找到仓库后，用 list_github_files 浏览文件，read_github_file 读代码。

    Args:
        query: Search keywords (中文或英文均可)
        limit: Maximum results (default: 10, max: 30)
    """
    global _github, _engine

    if _github is None:
        _github = GitHubConnector()

    if _engine is None:
        data_dir = os.environ.get("CODE_RAG_DATA_DIR", os.path.expanduser("~/.code-rag"))
        _init_engine(data_dir)

    limit = min(limit, 30)

    try:
        repos = _github.search_repos(query, limit=limit)
    except Exception as e:
        if "RateLimitError" in type(e).__name__:
            return (
                "GitHub API 额度已用完，没有 token 的话每小时只能搜 60 次。\n\n"
                "请选择：\n"
                "1. 配置 GITHUB_TOKEN（推荐，5000次/时）— 去 https://github.com/settings/tokens 生成\n"
                "2. 用内置的 web_search_github 工具替代（免费，无需配置）"
            )
        return f"搜索出错: {e}"

    if repos is None:
        return "GitHub API 不可达（网络问题或代理未配置）。请检查网络连接后重试。"

    if not repos:
        return "没有找到匹配的仓库，试试其他关键词。"

    # Auto-record to search_history
    try:
        if _engine is None:
            data_dir = os.environ.get("CODE_RAG_DATA_DIR", os.path.expanduser("~/.code-rag"))
            _init_engine(data_dir)
        for repo in repos:
            _engine.record_search(query, repo)
    except Exception:
        pass  # Best-effort

    output = [f"GitHub 搜索结果: {query}\n"]
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

    output.append("下一步：选择一个仓库，用 list_github_files(url) 浏览目录，然后用 read_github_file(url, path) 读代码。")
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
    global _engine

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

    # Auto-record to search_history
    try:
        if _engine is None:
            data_dir = os.environ.get("CODE_RAG_DATA_DIR", os.path.expanduser("~/.code-rag"))
            _init_engine(data_dir)
        for r in results:
            name_parts = r["repo"].split("/")
            if len(name_parts) >= 2:
                _engine.record_search(query, RepoInfo(
                    name=r["repo"], url=r["url"], language=r["language"],
                    indexed_at="", description=r["description"][:200] or "",
                    stars=0, file_count=0,
                ))
    except Exception:
        pass  # Best-effort

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

    output.append("下一步：选择一个仓库，用 list_github_files(url) 浏览目录，然后用 read_github_file(url, path) 读代码。")
    return "".join(output)


@mcp.tool()
def index_status() -> str:
    """查看当前本地索引了哪些代码文件。"""
    global _engine, _storage

    if _engine is None:
        return "还没有读过任何代码。"

    stats = _storage.get_stats()
    repos = _engine.list_indexed_repos()
    categories = _storage.get_all_categories()

    output = [
        "索引状态:\n",
        f"仓库数: {stats['repos']}\n",
        f"文件数: {stats['files']}\n",
        f"搜索类别: {stats['categories']}\n",
        f"FTS5: {'已启用' if stats['has_fts'] else '不可用'}\n\n",
    ]

    if categories:
        output.append("类别:\n")
        for cat in categories:
            records = _engine.get_search_history(cat)
            output.append(f"  - {cat}: {len(records)} 个项目\n")
        output.append("\n")

    if repos:
        output.append("已读仓库:\n")
        for repo in repos:
            output.append(f"  - {repo.name}: {repo.file_count} 个文件\n")

    return "".join(output)


@mcp.tool()
def db_inspect() -> str:
    """查看数据库表结构和内容概况（所有表、字段、记录数、最近记录）。

    想看当前索引了哪些数据时用这个。比 index_status 更详细，展示完整表结构。
    """
    global _storage

    if _storage is None:
        return "数据库未初始化，还没有读过任何代码。"

    conn = _storage._get_conn()

    # 1. 获取所有表
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()

    output = ["📊 数据库表结构\n"]
    output.append("=" * 40 + "\n\n")

    for (table_name,) in tables:
        if table_name.startswith("sqlite_"):
            continue

        # 表信息
        output.append(f"📋 {table_name}\n")
        output.append("-" * 30 + "\n")

        # 字段信息
        columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        output.append("  字段:\n")
        for col in columns:
            cid, name, col_type, not_null, default, pk = col
            flags = []
            if pk:
                flags.append("PK")
            if not_null:
                flags.append("NOT NULL")
            if default is not None:
                flags.append(f"DEFAULT {default}")
            flag_str = f"  ({', '.join(flags)})" if flags else ""
            output.append(f"    - {name}  {col_type}{flag_str}\n")

        # 记录数
        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        output.append(f"  记录数: {count}\n")

        # 最近几条记录（只显示前 3 条）
        if count > 0:
            try:
                rows = conn.execute(
                    f"SELECT * FROM {table_name} ORDER BY rowid DESC LIMIT 3"
                ).fetchall()
                output.append("  最近记录:\n")
                for row in rows:
                    preview = " | ".join(str(c)[:50] for c in row[:4])
                    output.append(f"    - {preview}\n")
            except Exception:
                pass  # FTS5 虚拟表不支持直接查

        output.append("\n")

    return "".join(output)


@mcp.tool()
def db_cleanup(action: str = "", repo: str = "", category: str = "") -> str:
    """整理数据库表，清理不需要的历史数据。

    当 db_inspect 发现数据太多或过时了，用这个工具清理。

    Args:
        action: 操作类型
          - "stats" 查看各表数据量（默认）
          - "purge_category" 删除指定类别的搜索历史（需传 category）
          - "purge_repo" 删除指定仓库的所有数据（需传 repo，格式 owner/repo）
          - "purge_all" 清空所有数据（慎重！）
          - "vacuum" 压缩数据库，回收空间
        repo: 仓库名，格式 "owner/repo"，配合 action="purge_repo" 使用
        category: 类别名，配合 action="purge_category" 使用
    """
    global _storage

    if _storage is None:
        return "数据库未初始化。"

    conn = _storage._get_conn()

    if action == "stats" or not action:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' "
            "AND name NOT LIKE 'file_content_fts%'"
        ).fetchall()
        output = ["📊 数据量统计\n"]
        total = 0
        for (name,) in tables:
            count = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            total += count
            output.append(f"  {name}: {count} 条\n")
        output.append(f"  ───────────\n 总计: {total} 条\n")
        return "".join(output)

    elif action == "purge_category":
        if not category:
            return "请指定 category 参数"
        conn.execute("DELETE FROM search_history WHERE category = ?", (category,))
        conn.commit()
        return f"已删除类别 '{category}' 的搜索历史"

    elif action == "purge_repo":
        if not repo:
            return "请指定 repo 参数（格式: owner/repo）"
        conn.execute("DELETE FROM repos WHERE name = ?", (repo,))
        conn.execute("DELETE FROM search_history WHERE repo_name = ?", (repo,))
        conn.execute("DELETE FROM files WHERE repo = ?", (repo,))
        conn.commit()
        return f"已删除仓库 '{repo}' 的所有数据"

    elif action == "purge_all":
        conn.executescript("""
            DELETE FROM repos;
            DELETE FROM search_history;
            DELETE FROM files;
            DELETE FROM file_content_fts;
        """)
        conn.commit()
        return "已清空所有数据"

    elif action == "vacuum":
        conn.execute("VACUUM")
        conn.commit()
        return "数据库已压缩"

    return f"未知操作: {action}，支持: stats, purge_category, purge_repo, purge_all, vacuum"


# ── Main (for direct execution) ─────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="GitHub Code Reader MCP Server")
    parser.add_argument(
        "--data-dir",
        default=os.environ.get("CODE_RAG_DATA_DIR", os.path.expanduser("~/.code-rag")),
        help="Data directory for storing index data",
    )
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio")

    args = parser.parse_args()
    _init_engine(args.data_dir)
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()