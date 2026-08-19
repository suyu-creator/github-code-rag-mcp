<div align="center"><pre>
     ██████╗ ██╗████████╗██╗  ██╗██╗   ██╗██████╗      ██████╗ ██████╗ ██████╗ ███████╗
    ██╔════╝ ██║╚══██╔══╝██║  ██║██║   ██║██╔══██╗    ██╔════╝██╔═══██╗██╔══██╗██╔════╝
    ██║  ███╗██║   ██║   ███████║██║   ██║██████╔╝    ██║     ██║   ██║██║  ██║█████╗
    ██║   ██║██║   ██║   ██╔══██║██║   ██║██╔══██╗    ██║     ██║   ██║██║  ██║██╔══╝
    ╚██████╔╝██║   ██║   ██║  ██║╚██████╔╝██████╔╝    ╚██████╗╚██████╔╝██████╔╝███████╗
     ╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═════╝      ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝
       — Steal code from GitHub, ethically · Auto-indexed · Reuse-first —
</pre></div>

<p align="center">
  <a href="https://pypi.org/project/github-code-rag/"><img src="https://img.shields.io/pypi/v/github-code-rag?style=flat-square" alt="PyPI" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License" /></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-green?style=flat-square" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/MCP-v1.0-purple?style=flat-square" alt="MCP v1.0" />
  <img src="https://img.shields.io/badge/deps-1-orange?style=flat-square" alt="1 dependency" />
</p>

<p align="center">
  <strong>Still switching to your browser to search GitHub while coding?</strong><br/>
  Let your AI search 200M+ public repos directly, find the best implementation, and reuse it with source attribution.<br/>
  <br/>
  <em>No cloning, no plugins, no browser tabs — your AI searches GitHub while it codes.</em>
</p>

---

### In One Sentence

An MCP server that lets your AI **search and reuse code from GitHub in real time**.
Writing auth? Search first. Writing middleware? Search first. Writing payment integration? Search first.
Before AI writes any code, it finds the best implementation on GitHub — **no reinventing the wheel**.
Also includes a "requirements analysis Agent" methodology so AI researches before building, no guessing.

---

### The Problem

Does this sound familiar?

> "Needed an auth module, spent 30 mins Googling, found code of questionable quality."

> "There are great implementations on GitHub, but the AI never searches — it just writes from scratch."

> "Every new feature feels like reinventing the wheel when answers are everywhere."

**The problem is how AI codes today.**

```
Current: AI wants to write → guesses from memory → wrong → rewrite → still wrong

Better: AI wants to write → searches GitHub → finds the best → reuses → tweaks → done
```

**github-code-rag puts GitHub inside your AI's toolbox.** Search first, reuse second.

---

### Core Capabilities

#### 🔥 Real-time GitHub code search & reuse

Sorted by stars, finds the most mature projects first. Filter by language and star count.

```
User: Write a FastAPI database connection module
    ↓
AI: search_github("fastapi sqlalchemy database stars:>1000")
AI: read_github_file("tiangolo/fastapi", "docs_src/sql_app/main.py")
AI: search_code("create_engine sessionmaker")
    ↓
AI: I referenced the FastAPI official example, here you go:

# Source: tiangolo/fastapi/docs_src/sql_app/main.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
...
```

No browser switching, no cloning repos, no dozens of tabs.
Your AI **searches GitHub on the fly** while coding, finds the best implementation, reuses it.

#### 📚 Read code auto-indexes, gets better over time

All read repos go into a local FTS5 full-text index. Next time you search for related code, results come back in milliseconds.

```
→ search_code("jwt authentication middleware")
  Found 47 matches across 12 indexed repos:
  - fastapi/.../auth.py:35  JWT bearer middleware
  - django/.../auth.py:128  Token authentication
  - ...
```

The more you use it, the bigger your local code knowledge base gets, the faster AI codes.

#### 🔄 GitHub API + Bing dual fallback

- GitHub Search API: highest quality, sorted by stars (60 req/hr free, 5000 with Token)
- Bing search fallback: free unlimited quota, auto-degrade on rate limit
- Zero git clone: all via REST API, no local disk bloat

#### 🧠 Bonus: Requirements Analysis Agent

The system prompt hardcodes a workflow so AI doesn't jump straight into coding.
It searches similar projects first, asks clarifying questions based on real examples, and only starts building after confirmation.

```
User: I want to build a blog system
    ↓
AI: [searched 10 relevant projects]
    Do you want a standalone blog (like Hugo/Hexo) or a multi-user platform?
     - Standalone blog (simple, great SEO)
     - Multi-user platform (complex features, needs admin backend)
     - Recommend based on GitHub projects
```

Think of it as "a senior engineer's methodology — included for free."
You don't have to use it. The code search alone is worth it.

#### ⚡ Zero git clone · Zero vector DB · Only 1 dependency

- All via GitHub REST API — no repo cloning needed
- SQLite + FTS5 full-text index — no vector DB or embeddings
- Runtime depends only on `mcp>=1.0`, everything else is Python stdlib
- Startup < 1 second, memory < 50MB

---

### With vs Without

| | Without github-code-rag | With github-code-rag |
|---|---|---|
| Searching GitHub before coding | Manually in browser | AI does it automatically |
| Code source | From model memory | The best from 200M+ GitHub repos |
| Code quality | Depends on model ability | Standing on the shoulders of open source |
| Source attribution | No idea who wrote what | Auto-tagged `# Source: owner/repo/file.py` |
| Each new feature | Starts from scratch | Local knowledge base keeps growing |
| GitHub rate limiting | — | Bing auto-fallback, unlimited |

---

### Quick Start

#### 1. Install

```bash
# Recommended: pipx (isolated environment)
pipx install github-code-rag

# Or uv
uv tool install github-code-rag

# Or pip
pip install github-code-rag
```

#### 2. Configure Token (optional but recommended)

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

Works without a token — built-in Bing search fallback, free and unlimited.
With a token, GitHub API quota goes from 60 req/hr → 5000 req/hr.

#### 3. Configure your AI client

See the "Client Setup" section below.

#### 4. Try this

After installation, tell your AI:

> "Write a FastAPI JWT auth middleware. First search GitHub for the best implementation to reference."

Watch whether it searches GitHub before writing code.

---

### Client Setup

> All configurations use stdio mode. Restart your client after configuration.
> Not sure about the install path? Run `which github-code-rag` (macOS/Linux) or `where github-code-rag` (Windows).

#### Claude Code

Edit `~/.claude.json`, add:

```json
{
  "mcpServers": {
    "github-code-rag": {
      "command": "github-code-rag",
      "env": {
        "GITHUB_TOKEN": "ghp_your_token_here"
      }
    }
  }
}
```

#### Claude Desktop

Settings → Developer → Edit Config, add:

```json
{
  "mcpServers": {
    "github-code-rag": {
      "command": "github-code-rag"
    }
  }
}
```

- macOS config path: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows config path: `%APPDATA%\Claude\claude_desktop_config.json`

#### Cursor

Project-level (current project only): create `.cursor/mcp.json` in project root:

```json
{
  "mcpServers": {
    "github-code-rag": {
      "command": "github-code-rag"
    }
  }
}
```

Global: Settings → MCP → Add new server → Stdio → enter `github-code-rag`

#### Windsurf

Settings → MCP Servers → Add MCP Server, choose stdio mode, command:

```
github-code-rag
```

Config file locations:

- macOS: `~/.codeium/windsurf/mcp_config.json`
- Windows: `%APPDATA%\..\Roaming\Codeium\Windsurf\mcp_config.json`

#### Cline / Roo Code

Settings → MCP Servers → Add new MCP Server → Local executable, enter:

```
Command: github-code-rag
```

Or edit config files directly:

- Cline: `~/.cline/mcp.json`
- Roo Code: `~/.roo-code/mcp.json`

#### Codex CLI

Edit `~/.codex/config.toml`, add:

```toml
[mcp_servers.github-code-rag]
command = "github-code-rag"
```

#### OpenCode

Edit the mcp servers section in OpenCode config:

```json
{
  "mcpServers": {
    "github-code-rag": {
      "command": "github-code-rag"
    }
  }
}
```

> Any MCP-compatible client works. If your client isn't listed above, the setup is basically the same — point `command` to `github-code-rag`.

---

### Tool List

| Tool | Description |
|---|---|
| `search_github` | GitHub official API repo search, sorted by stars |
| `web_search_github` | Bing search fallback, free unlimited quota |
| `list_github_files` | Browse repo directory structure |
| `read_github_file` | Read file content, auto-index to local knowledge base |
| `search_code` | FTS5 full-text search across indexed code |
| `search_history` | Query search history for similar projects |
| `index_status` | View local index status |
| `db_inspect` | Inspect database schema and record counts |
| `db_cleanup` | Clean up historical data, free space |

---

### How It Works

```
┌───────────────────────────────────────────────────────────┐
│                    Your AI Client                         │
│  (Claude Code / Cursor / Codex / Claude Desktop / ...)   │
└───────────────────────────┬───────────────────────────────┘
                            │ MCP protocol (stdio)
┌───────────────────────────▼───────────────────────────────┐
│                                                           │
│  ┌─────────────────────────────────────────────────┐     │
│  │  System Prompt (Requirements Analysis Agent)    │     │
│  │    · Search first · Iterative narrowing         │     │
│  │    · Reuse-first · One question at a time       │     │
│  └───────────────────────┬─────────────────────────┘     │
│                          │ Guides AI tool usage           │
│  ┌───────────────────────▼─────────────────────────┐     │
│  │  9 MCP Tools                                     │     │
│  │  search / browse / read / code search / history │     │
│  └───────────┬───────────────────────────┬─────────┘     │
│              │                           │               │
│ ┌────────────▼───────────┐   ┌───────────▼──────────┐    │
│ │  GitHub REST API       │   │  SQLite + FTS5       │    │
│ │  + Bing fallback       │   │  Local code KB       │    │
│ │  Zero git clone        │   │  Trigram FTS         │    │
│ └────────────────────────┘   └──────────────────────┘    │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

#### Why FTS5, not vector databases?

| | FTS5 (what we use) | Vector search |
|---|---|---|
| Function/class/keyword search | Precise | Semantic drift |
| "How to implement auth" | No | Yes |
| Extra dependencies | Zero (SQLite built-in) | Vector DB + Embedding model |
| Download size | < 1MB | Tens ~ hundreds of MB |
| Search latency | < 10ms | Tens ~ hundreds of ms |

Our approach: **two-phase search**.
First use GitHub Search to find the right repos ("which project is worth referencing"), then use FTS5 to pinpoint code inside repos ("where's the implementation").

Vector search? For code reuse, it's often an oversold solution.
When you search code, you think "how to use sessionmaker" or "how to write JWT middleware" — not "things semantically similar to authentication."

---

### Comparison

| Feature | github-code-rag | codedb | codebase-rag | Official GitHub MCP |
|---|---|---|---|---|
| Search & reuse public GitHub code | ✅ | ❌ (local only) | ✅ (needs clone) | ✅ |
| Zero git clone | ✅ | N/A | ❌ | ✅ |
| Local code indexing (FTS5) | ✅ | ✅ (Zig custom) | ✅ (FTS5 + vector) | ❌ |
| Free search fallback (Bing) | ✅ | ❌ | ❌ | ❌ |
| Requirements analysis Agent | ✅ (bonus) | ❌ | ❌ | ❌ |
| Mandatory reuse methodology | ✅ (bonus) | ❌ | ❌ | ❌ |
| Search history / categories | ✅ | ❌ | ❌ | ❌ |
| External dependencies | 1 (mcp) | 0 (single binary) | Many (Bun + ONNX) | Many |
| Startup time | < 1s | Very fast | Slow | Fast |

In one sentence:

- codedb / codebase-rag = tools for searching local code
- Official GitHub MCP = Swiss Army knife for GitHub
- **github-code-rag = purpose-built for reusing GitHub code + bonus methodology Agent**

---

### Project Structure

```
├── server/
│   └── mcp_server.py          # MCP server + system prompt
├── github/
│   └── connector.py           # GitHub API wrapper (pure urllib, zero deps)
├── core/
│   ├── models.py              # Data models
│   └── retrieval_engine.py    # FTS5 search engine
├── storage/
│   └── sqlite_storage.py      # SQLite + FTS5 + WAL + trigger sync
├── tests/
│   ├── test_retrieval.py
│   └── test_storage.py
├── .well-known/mcp.json       # SSE mode config
├── pyproject.toml
└── run_server.py
```

---

### Development

```bash
# Clone
git clone https://github.com/suyu-creator/github-code-rag-mcp.git
cd github-code-rag-mcp

# Install dependencies
uv sync

# Run tests
uv run pytest

# Manual start (stdio mode)
uv run github-code-rag
```

**Environment variables:**

```
GITHUB_TOKEN=ghp_xxx           # GitHub API Token (recommended)
CODE_RAG_DATA_DIR=~/.code-rag  # Data storage directory
```

---

### FAQ

**Which MCP clients are supported?**

All MCP-compatible clients — Claude Code, Claude Desktop, Cursor, Windsurf, Cline, Codex, Gemini CLI, OpenCode… any client that can configure an MCP server works.

**Will my code be uploaded?**

No. All indexes are stored in local SQLite. The GitHub API only reads public repos. Your code never leaves your machine.

**Why not just use gh CLI?**

Because MCP tools should be transparent to the AI — it doesn't need to know what CLI you have installed, it just calls tools. Plus pure Python implementation, zero system dependencies.

**What if GitHub API is rate limited?**

Auto-degrades to Bing search. Free, unlimited quota, no extra config needed. Experience is slightly degraded, but it never stops working.

**Will you add vector search?**

Maybe, but it's not the current priority. Our focus is "quickly find the right code to reuse." The two-phase search (GitHub Search + FTS5) already covers 90% of use cases. The actual benefit of vector search for code reuse isn't as big as marketing claims suggest.

---

### Contributing

- Found a bug → open an Issue
- New idea → open an Issue to discuss first
- Code contribution → Fork + PR
- Find it useful → star it, help more people discover it

---

## 中文

<div align="center"><pre>
     ██████╗ ██╗████████╗██╗  ██╗██╗   ██╗██████╗      ██████╗ ██████╗ ██████╗ ███████╗
    ██╔════╝ ██║╚══██╔══╝██║  ██║██║   ██║██╔══██╗    ██╔════╝██╔═══██╗██╔══██╗██╔════╝
    ██║  ███╗██║   ██║   ███████║██║   ██║██████╔╝    ██║     ██║   ██║██║  ██║█████╗
    ██║   ██║██║   ██║   ██╔══██║██║   ██║██╔══██╗    ██║     ██║   ██║██║  ██║██╔══╝
    ╚██████╔╝██║   ██║   ██║  ██║╚██████╔╝██████╔╝    ╚██████╗╚██████╔╝██████╔╝███████╗
     ╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═════╝      ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝
        — 让 AI 直接从 GitHub 抄代码 · 读完自动索引 · 复用优先 —
</pre></div>

<p align="center">
  <a href="https://pypi.org/project/github-code-rag/"><img src="https://img.shields.io/pypi/v/github-code-rag?style=flat-square" alt="PyPI" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License" /></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-green?style=flat-square" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/MCP-v1.0-purple?style=flat-square" alt="MCP v1.0" />
  <img src="https://img.shields.io/badge/deps-1-orange?style=flat-square" alt="1 dependency" />
</p>

<p align="center">
  <strong>写代码还在切浏览器搜 GitHub？</strong><br/>
  让你的 AI 直接搜 2 亿+ 公开仓库，找到最相关的实现，抄过来还标来源。<br/>
  <br/>
  <em>不用 clone、不用装插件、不用打开浏览器 —— AI 写代码时顺手就把 GitHub 搜了。</em>
</p>

---

## 一句话介绍

一个让 AI **实时搜 GitHub 代码拿来复用**的 MCP 服务器。
写认证？搜一下。写中间件？搜一下。写支付？搜一下。
AI 写每一行代码之前，先去 GitHub 找最好的实现参考，**禁止从零造轮子**。
还内置了一套「需求分析 Agent」方法论，让 AI 先调研再动手，不瞎猜。

---

## 痛点

你是不是也这样？

> "写个用户认证模块，切浏览器搜了半小时，找到的代码质量参差不齐。"

> "明明 GitHub 上有最好的实现，AI 就是不知道去搜，非要自己从零瞎写。"

> "每次写新功能都像重新发明一遍轮子，明明到处都是参考答案。"

**问题出在 AI 写代码的姿势不对。**

```
现在的流程：AI 想写 → 凭记忆瞎写 → 不对 → 改 → 还不对

应该有的流程：AI 想写 → 搜 GitHub → 找到最好的实现 → 复用 → 微调 → 完成
```

**github-code-rag 把 GitHub 塞进了 AI 的工具箱里。** 想写什么，先搜，再抄。

---

## 核心能力

### 🔥 实时搜 GitHub，找到最相关的代码复用

按 star 排序，优先挑最成熟的项目。支持按语言、star 数筛选。

```
用户：帮我写个 FastAPI 的数据库连接模块
    ↓
AI：search_github("fastapi sqlalchemy database stars:>1000")
AI：read_github_file("tiangolo/fastapi", "docs_src/sql_app/main.py")
AI：search_code("create_engine sessionmaker")
    ↓
AI：我参考了 FastAPI 官方示例，给你写好了：

# Source: tiangolo/fastapi/docs_src/sql_app/main.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
...
```

不用切浏览器、不用 clone 仓库、不用在几十个标签页里翻。
AI 写代码时**顺手**就去 GitHub 搜了，找到最好的实现直接复用。

### 📚 读过的代码自动索引，越用越顺手

读过的仓库全部进本地 FTS5 全文索引，下次再搜相关代码毫秒级出结果。

```
→ search_code("jwt authentication middleware")
  在 12 个已读仓库中找到 47 个匹配片段：
  - fastapi/.../auth.py:35  JWT bearer middleware
  - django/.../auth.py:128  Token authentication
  - ...
```

用得越久，你的本地代码知识库越大，AI 写代码越快。

### 🔄 GitHub API + Bing 双路兜底，不怕限流

- GitHub Search API：质量最高，按 star 排序（60 次/时免费，配 Token 5000 次/时）
- Bing 搜索兜底：免费无限额度，限流自动降级
- 零 git clone：全部走 REST API，不占本地磁盘

### 🧠 附赠：需求分析 Agent —— 先调研再动手

系统提示词硬编码了工作流，AI 不会上来就瞎写。
它会先搜同类项目，基于真实项目反问你需求，确认清楚了才动手。

```
用户：我想做个博客系统
    ↓
AI：[搜了 10 个相关项目]
    你是要做独立博客（类似 Hugo/Hexo），还是多用户平台？
     - 独立博客（简单、SEO 好）
     - 多用户平台（功能复杂、需后台）
     - 我来根据 GitHub 项目给你推荐
```

可以理解为「附赠了一个高级工程师的工作方法论」。
不需要可以不用，代码搜索本身就值回票价。

### ⚡ 零 git clone · 零向量数据库 · 仅 1 个依赖

- 全部走 GitHub REST API，不需要 clone 仓库
- SQLite + FTS5 全文索引，不需要向量数据库和 embedding
- 运行时只依赖 `mcp>=1.0`，其他全是 Python 标准库
- 启动 < 1 秒，内存 < 50MB

---

## 装了 vs 没装

| | 没装 github-code-rag | 装了 github-code-rag |
|---|---|---|
| 写代码前搜 GitHub | 切浏览器手动搜 | AI 自动搜，直接复用 |
| 代码来源 | 凭模型记忆瞎写 | 从 2 亿+ GitHub 仓库挑最好的 |
| 代码质量 | 全靠模型水平 | 站在开源巨人肩膀上 |
| 来源标注 | 不知道抄的谁的 | 自动标注 `# Source: owner/repo/file.py` |
| 每次写新功能 | 从零开始 | 本地知识库越攒越多 |
| GitHub 限流 | — | Bing 自动兜底，无限额度 |

---

## 快速开始

### 1. 安装

```bash
# 推荐：pipx 一键安装（隔离环境）
pipx install github-code-rag

# 或者 uv
uv tool install github-code-rag

# 或者 pip
pip install github-code-rag
```

### 2. 配置 Token（可选但推荐）

```bash
export GITHUB_TOKEN=ghp_your_token_here
```

没有 Token 也能用 —— 内置 Bing 搜索兜底，免费无限额度。
有 Token 的话 GitHub API 额度从 60 次/时 → 5000 次/时。

### 3. 配置到你的 AI 客户端

见下面的「客户端配置」章节。

### 4. 试试这个

装好后跟你的 AI 说：

> "帮我写一个 FastAPI 的 JWT 认证中间件，先去 GitHub 搜一下最好的实现参考"

看看它会不会先搜 GitHub，再基于搜到的代码给你写。

---

## 客户端配置

> 以下配置均为 stdio 模式。配置完成后重启客户端即可使用。
> 不确定安装路径？运行 `which github-code-rag`（macOS/Linux）或 `where github-code-rag`（Windows）查看。

### Claude Code

编辑 `~/.claude.json`，添加：

```json
{
  "mcpServers": {
    "github-code-rag": {
      "command": "github-code-rag",
      "env": {
        "GITHUB_TOKEN": "ghp_your_token_here"
      }
    }
  }
}
```

### Claude Desktop

打开设置 → Developer → Edit Config，添加：

```json
{
  "mcpServers": {
    "github-code-rag": {
      "command": "github-code-rag"
    }
  }
}
```

- macOS 配置文件路径：`~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows 配置文件路径：`%APPDATA%\Claude\claude_desktop_config.json`

### Cursor

项目级配置（仅当前项目）：在项目根目录创建 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "github-code-rag": {
      "command": "github-code-rag"
    }
  }
}
```

全局配置：设置 → MCP → Add new server → Stdio → 填入 `github-code-rag`

### Windsurf

设置 → MCP Servers → Add MCP Server，选择 stdio 模式，命令填：

```
github-code-rag
```

配置文件通常位于：

- macOS：`~/.codeium/windsurf/mcp_config.json`
- Windows：`%APPDATA%\..\Roaming\Codeium\Windsurf\mcp_config.json`

### Cline / Roo Code

设置 → MCP Servers → Add new MCP Server → Local executable，填入：

```
Command: github-code-rag
```

或直接编辑配置文件：

- Cline：`~/.cline/mcp.json`
- Roo Code：`~/.roo-code/mcp.json`

### Codex CLI

编辑 `~/.codex/config.toml`，添加：

```toml
[mcp_servers.github-code-rag]
command = "github-code-rag"
```

### OpenCode

编辑 OpenCode 配置文件中的 mcp servers 部分：

```json
{
  "mcpServers": {
    "github-code-rag": {
      "command": "github-code-rag"
    }
  }
}
```

> 所有支持 MCP 协议的客户端都能用。如果你用的客户端不在上面列表里，配置方式基本一样 —— 把 command 指向 `github-code-rag` 即可。

---

## 工具列表

| 工具 | 说明 |
|---|---|
| `search_github` | GitHub 官方 API 搜索仓库，按 star 排序 |
| `web_search_github` | Bing 搜索兜底，免费无限额度 |
| `list_github_files` | 浏览仓库目录结构 |
| `read_github_file` | 读取文件内容，自动索引到本地知识库 |
| `search_code` | 在已读代码中做 FTS5 全文搜索 |
| `search_history` | 查询同类项目的搜索历史 |
| `index_status` | 查看本地索引状态 |
| `db_inspect` | 查看数据库表结构和记录数 |
| `db_cleanup` | 清理历史数据，释放空间 |

---

## 工作原理

```
┌───────────────────────────────────────────────────────────┐
│                    你的 AI 客户端                         │
│  (Claude Code / Cursor / Codex / Claude Desktop / ...)   │
└───────────────────────────┬───────────────────────────────┘
                            │ MCP protocol (stdio)
┌───────────────────────────▼───────────────────────────────┐
│                                                           │
│  ┌─────────────────────────────────────────────────┐     │
│  │  系统提示词（需求分析 Agent 方法论）             │     │
│  │    · 先搜再问 · 逐步收敛 · 复用优先              │     │
│  └───────────────────────┬─────────────────────────┘     │
│                          │ 指导 AI 怎么用工具             │
│  ┌───────────────────────▼─────────────────────────┐     │
│  │  9 个 MCP 工具                                   │     │
│  │  搜索 / 浏览 / 阅读 / 搜索代码 / 历史 / 管理     │     │
│  └───────────┬───────────────────────────┬─────────┘     │
│              │                           │               │
│ ┌────────────▼───────────┐   ┌───────────▼──────────┐    │
│ │  GitHub REST API       │   │  SQLite + FTS5       │    │
│ │  + Bing 搜索兜底       │   │  本地代码知识库       │    │
│ │  零 git clone          │   │  Trigram 全文搜索     │    │
│ └────────────────────────┘   └──────────────────────┘    │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

### 为什么是 FTS5，不是向量数据库？

| | FTS5（我们用的） | 向量搜索 |
|---|---|---|
| 搜函数名 / 类名 / 关键字 | 精确 | 语义漂移 |
| 搜 "认证怎么实现" | 不行 | 可以 |
| 额外依赖 | 零（SQLite 内置） | 向量数据库 + Embedding 模型 |
| 下载体积 | < 1MB | 几十 ~ 几百 MB |
| 搜索延迟 | < 10ms | 几十 ~ 几百 ms |

我们的解法：**两阶段搜索**。
先用 GitHub Search 找到对的仓库（解决"哪个项目值得参考"），再用 FTS5 在仓库内精确搜代码（解决"具体实现在哪"）。

向量搜索？对代码复用场景来说，很多时候是个被过度营销的方案。
你搜代码的时候脑子里想的是「sessionmaker 怎么用」「JWT 中间件怎么写」，不是「语义上接近认证的东西」。

---

## 同类项目对比

| 特性 | github-code-rag | codedb | codebase-rag | 官方 GitHub MCP |
|---|---|---|---|---|
| 搜 GitHub 公开代码拿来复用 | ✅ | ❌（仅本地） | ✅（需 clone） | ✅ |
| 零 git clone | ✅ | N/A | ❌ | ✅ |
| 本地代码索引（FTS5） | ✅ | ✅（Zig 自研） | ✅（FTS5 + 向量） | ❌ |
| 免费搜索兜底（Bing） | ✅ | ❌ | ❌ | ❌ |
| 需求分析 Agent 引导 | ✅（附赠） | ❌ | ❌ | ❌ |
| 强制代码复用方法论 | ✅（附赠） | ❌ | ❌ | ❌ |
| 搜索历史 / 分类积累 | ✅ | ❌ | ❌ | ❌ |
| 外部依赖数 | 1（mcp） | 0（单二进制） | 多（Bun + ONNX） | 多 |
| 启动时间 | < 1s | 极快 | 较慢 | 快 |

一句话总结差异：

- codedb / codebase-rag = 搜本地代码的工具
- 官方 GitHub MCP = GitHub 全能工具箱
- **github-code-rag = 专门用来抄 GitHub 代码的神器 + 附赠需求分析方法论**

---

## 项目结构

```
├── server/
│   └── mcp_server.py          # MCP 服务器 + 系统提示词
├── github/
│   └── connector.py           # GitHub API 封装（纯 urllib，零依赖）
├── core/
│   ├── models.py              # 数据模型
│   └── retrieval_engine.py    # FTS5 搜索引擎
├── storage/
│   └── sqlite_storage.py      # SQLite + FTS5 + WAL + 触发器同步
├── tests/
│   ├── test_retrieval.py
│   └── test_storage.py
├── .well-known/mcp.json       # SSE 模式配置
├── pyproject.toml
└── run_server.py
```

---

## 开发

```bash
# 克隆
git clone https://github.com/suyu-creator/github-code-rag-mcp.git
cd github-code-rag-mcp

# 安装依赖
uv sync

# 运行测试
uv run pytest

# 手动启动（stdio 模式）
uv run github-code-rag
```

**环境变量：**

```
GITHUB_TOKEN=ghp_xxx           # GitHub API Token（推荐）
CODE_RAG_DATA_DIR=~/.code-rag  # 数据存储目录
```

---

## FAQ

**支持哪些 MCP 客户端？**

所有支持 MCP 协议的 —— Claude Code、Claude Desktop、Cursor、Windsurf、Cline、Codex、Gemini CLI、OpenCode… 只要能配 MCP server 就能用。

**我的代码会上传吗？**

不会。所有索引存在本地 SQLite 里。GitHub API 只用来读公开仓库，你的代码不会发出去。

**为什么不直接用 gh CLI？**

因为 MCP 工具要对 AI 透明 —— AI 不需要知道你装了什么 CLI，它只需要调用工具就行。而且纯 Python 实现，零系统依赖。

**GitHub API 限流了怎么办？**

自动降级到 Bing 搜索，免费无限额度，不需要额外配置。体验差一点，但不会用不了。

**会加向量搜索吗？**

可能，但不是当前优先级。我们的定位是「快速找到对的代码来复用」，FTS5 + GitHub Search 的两阶段搜索已经能覆盖 90% 的场景。向量搜索在代码复用场景下的实际收益没有营销文案说的那么大。

---

## 参与贡献

- 发现 Bug → 提 Issue
- 有新想法 → 先开 Issue 讨论
- 代码贡献 → Fork + PR
- 觉得好用 → 点个 star，让更多人看到

---

