<div align="center"><pre>
     ██████╗ ██╗████████╗██╗  ██╗██╗   ██╗██████╗      ██████╗ ██████╗ ██████╗ ███████╗
    ██╔════╝ ██║╚══██╔══╝██║  ██║██║   ██║██╔══██╗    ██╔════╝██╔═══██╗██╔══██╗██╔════╝
    ██║  ███╗██║   ██║   ███████║██║   ██║██████╔╝    ██║     ██║   ██║██║  ██║█████╗
    ██║   ██║██║   ██║   ██╔══██║██║   ██║██╔══██╗    ██║     ██║   ██║██║  ██║██╔══╝
    ╚██████╔╝██║   ██║   ██║  ██║╚██████╔╝██████╔╝    ╚██████╗╚██████╔╝██████╔╝███████╗
     ╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═════╝      ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝
        — 先搜 GitHub 再写代码 · 禁止从零造轮子 · 像高级工程师一样思考 —
</pre></div>

<p align="center">
  <a href="https://pypi.org/project/github-code-rag/"><img src="https://img.shields.io/pypi/v/github-code-rag?style=flat-square" alt="PyPI" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License" /></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-green?style=flat-square" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/MCP-v1.0-purple?style=flat-square" alt="MCP v1.0" />
  <img src="https://img.shields.io/badge/deps-1-orange?style=flat-square" alt="1 dependency" />
</p>

<p align="center">
  <strong>你的 AI 写代码是不是在瞎猜？</strong><br/>
  「做个电商网站」→ 直接开写 → 不对 → 重写 → 还不对 → 精疲力尽<br/>
  <br/>
  <em>github-code-rag 让 AI 先调研、再提问、最后才动手 —— 像一个真正的高级工程师。</em>
</p>

---

## 一句话介绍

一个内置「需求分析 Agent」的 MCP 服务器。
装完之后，你的 Claude / Cursor / Codex 不会再上来就写代码 —— 它会先搜 GitHub
找同类项目，基于真实项目反问你需求，确认完了才动手，而且写的每一行代码都**必须从已读项目里复用**。

---

## 问题

你是不是也这样？

> "让 AI 写个后台管理系统，写了三版都不对，它根本不知道我想要啥。"

> "我花一下午改 AI 写的代码，还不如自己从头写快。"

> "每次都是从零开始，明明 GitHub 上有成熟方案，它就是不会去搜。"

**问题出在流程上。** 大多数 AI 写代码的流程是错的：

```
错误流程：用户说需求 → AI 直接写 → 不对 → 改 → 还不对 → 放弃

正确流程：需求 → 搜同类项目 → 分析方案 → 确认需求 → 复用代码 → 动手写
```

**github-code-rag 把「工程师思维」装进了 MCP。**

---

## 核心特性

### 强制「先搜再问」—— 不调研就不许写代码

系统提示词硬编码了工作流，AI 必须先搜 GitHub，再基于搜索结果提问。
想跳步？工具的设计就是让「跳过搜索直接写代码」变得比「先搜再写」更麻烦。

```
用户：我想做个博客系统
    ↓
AI 调用 search_history("博客系统") → 没记录
AI 调用 search_github("blog system python stars:>500")
    ↓
AI：找到了 10 个相关项目，从 500⭐ 到 50k⭐ 不等。
    你是要做独立博客（类似 Hugo/Hexo），还是多用户博客平台？
     - 独立博客（简单、SEO 好）
     - 多用户平台（功能复杂、需后台）
     - 我来根据 GitHub 项目给你推荐
```

### 强制代码复用 —— 禁止从零造轮子

读过的代码全部进本地知识库，写代码时随时搜。
**复用优先**是写在系统提示词里的铁律：

> "能找到现成实现就不要从零写。违反此规则 = 无效输出。"

复用的代码会自动标注来源：

```python
# Source: tiangolo/fastapi/docs_src/sql_app/main.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
```

### 越用越聪明 —— 你的私人项目知识库

每次搜索都会存到本地 SQLite。上次调研完「电商小程序」，这次再问同类问题，直接从历史记录里开始，不用重新搜。

```
→ search_history("电商小程序")
  类别 '电商小程序' 已读过的项目:
    - justjavac/wechat-app-eshop (JavaScript) @ 2026-03-15
    - xxx/shop-wxapp (TypeScript) @ 2026-03-14
  → 有记录，直接用 search_code 搜具体实现
```

### GitHub API + Bing 双路兜底

- GitHub Search API：质量高、按 star 排序（60 次/时免费，配 Token 后 5000 次/时）
- Bing 搜索兜底：免费、无限额度、不需要 API Key
- 限流自动降级，不用你操心

### 零 git clone · 零向量数据库 · 仅 1 个依赖

- 全部走 GitHub REST API，不需要 clone 仓库到本地
- SQLite + FTS5 全文索引，不需要向量数据库和 embedding 模型
- 运行时只依赖 `mcp>=1.0`，其他全是 Python 标准库
- 启动 < 1 秒，内存占用 < 50MB

---

## 装了 vs 没装

| | 没装 github-code-rag | 装了 github-code-rag |
|---|---|---|
| AI 上来就写代码 | 写得飞起 | 先搜 GitHub 再说 |
| 需求理解 | 靠猜 | 基于真实项目逐步确认 |
| 代码质量 | 从零开始瞎写 | 从 2000 万 GitHub 仓库里挑最好的复用 |
| 踩坑 | 每个坑都自己踩一遍 | 别人踩过的坑你跳过 |
| 每次从头来 | 每次都是新鲜的 | 越用积累越多 |
| 标来源 | 不知道抄的谁的 | 自动标注 `# Source: owner/repo/file.py` |

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
| `search_history` | 查询同类项目的搜索历史（每次需求第一步必调用） |
| `search_github` | GitHub 官方 API 搜索仓库，按 star 排序 |
| `web_search_github` | Bing 搜索兜底，免费无限额度 |
| `list_github_files` | 浏览仓库目录结构 |
| `read_github_file` | 读取文件内容，自动索引到本地知识库 |
| `search_code` | 在已读代码中做 FTS5 全文搜索 |
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
│  │    · 一次只问一个问题 · 来源标注                 │     │
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
| 搜函数名 / 类名 | 精确 | 语义漂移 |
| 搜 "认证怎么实现" | 不行 | 可以 |
| 额外依赖 | 零（SQLite 内置） | 向量数据库 + Embedding 模型 |
| 下载体积 | < 1MB | 几十 ~ 几百 MB |
| 搜索延迟 | < 10ms | 几十 ~ 几百 ms |

我们的解法：**两阶段搜索**。
先用 GitHub Search 找到对的仓库（解决"哪个项目值得参考"），再用 FTS5 在仓库内精确搜代码（解决"具体实现在哪"）。

向量搜索？对代码来说，很多时候是个被过度营销的方案。

---

## 同类项目对比

| 特性 | github-code-rag | codedb | codebase-rag | 官方 GitHub MCP |
|---|---|---|---|---|
| 需求分析 Agent 引导 | 是 | 否 | 否 | 否 |
| 强制代码复用方法论 | 是 | 否 | 否 | 否 |
| 搜索历史 / 分类积累 | 是 | 否 | 否 | 否 |
| 搜 GitHub 公开仓库 | 是 | 否（仅本地） | 是（需 clone） | 是 |
| 本地代码索引 | 是（FTS5） | 是（Zig 自研） | 是（FTS5 + 向量） | 否 |
| 零 git clone | 是 | N/A | 否 | 是 |
| 免费搜索兜底（Bing） | 是 | 否 | 否 | 否 |
| 外部依赖数 | 1（mcp） | 0（单二进制） | 多（Bun + ONNX） | 多 |
| 启动时间 | < 1s | 极快 | 较慢 | 快 |

一句话总结差异：

- codedb / codebase-rag = 更快更好的代码搜索工具
- github-code-rag = 带着方法论的需求分析 Agent + 代码搜索

工具谁都能做，但方法论 + 工具才是护城河。

---

## 项目结构

```
├── server/
│   └── mcp_server.py          # MCP 服务器 + 系统提示词（核心方法论）
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

**会加向量搜索吗？**

可能，但不是当前优先级。目前的经验是：先搜对仓库 > 在仓库里精确搜 > 语义搜。向量搜索在代码场景下的实际收益没有营销文案说的那么大。如果你有强烈需求，欢迎提 Issue。

---

## 参与贡献

- 发现 Bug → 提 Issue
- 有新想法 → 先开 Issue 讨论
- 代码贡献 → Fork + PR
- 觉得好用 → 点个 star，让更多人看到

---

---

## English

<div align="center"><pre>
     ██████╗ ██╗████████╗██╗  ██╗██╗   ██╗██████╗      ██████╗ ██████╗ ██████╗ ███████╗
    ██╔════╝ ██║╚══██╔══╝██║  ██║██║   ██║██╔══██╗    ██╔════╝██╔═══██╗██╔══██╗██╔════╝
    ██║  ███╗██║   ██║   ███████║██║   ██║██████╔╝    ██║     ██║   ██║██║  ██║█████╗
    ██║   ██║██║   ██║   ██╔══██║██║   ██║██╔══██╗    ██║     ██║   ██║██║  ██║██╔══╝
    ╚██████╔╝██║   ██║   ██║  ██║╚██████╔╝██████╔╝    ╚██████╗╚██████╔╝██████╔╝███████╗
     ╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═════╝      ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝
        — Search GitHub first, then write code · Stop reinventing wheels —
</pre></div>

<p align="center">
  <a href="https://pypi.org/project/github-code-rag/"><img src="https://img.shields.io/pypi/v/github-code-rag?style=flat-square" alt="PyPI" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License" /></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-green?style=flat-square" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/MCP-v1.0-purple?style=flat-square" alt="MCP v1.0" />
  <img src="https://img.shields.io/badge/deps-1-orange?style=flat-square" alt="1 dependency" />
</p>

<p align="center">
  <strong>Is your AI just guessing when it writes code?</strong><br/>
  "Build me an e-commerce site" → starts coding → wrong → rewrite → still wrong → exhausted<br/>
  <br/>
  <em>github-code-rag makes your AI research first, ask questions second, and only then build — like a real senior engineer.</em>
</p>

---

### In One Sentence

An MCP server with a built-in **requirements analysis Agent**.
Once installed, your Claude / Cursor / Codex won't jump straight into writing code. It searches GitHub for similar projects first, asks clarifying questions based on real-world examples, confirms requirements, and then — and only then — starts building, **reusing code from repos it has read**.

---

### The Problem

Does this sound familiar?

> "Asked AI to build an admin dashboard. Three rewrites later, it still doesn't get what I want."

> "I spent the whole afternoon fixing AI-generated code. Would've been faster to write it myself."

> "It always starts from scratch. There are proven solutions on GitHub, but it never searches."

**The problem is the workflow.** Most AI coding follows a broken process:

```
Broken: user describes → AI writes directly → wrong → rewrite → still wrong → give up

Better: requirements → search similar projects → analyze options → confirm → reuse → build
```

**github-code-rag puts "engineer thinking" inside your MCP.**

---

### Core Features

#### "Search First, Ask Later" — No writing without research

The system prompt hardcodes the workflow. The AI *must* search GitHub before asking questions. Skipping steps? The tool design makes "write first, search never" harder than doing it right.

```
User: I want to build a blog system
    ↓
AI calls search_history("blog system") → no records
AI calls search_github("blog system python stars:>500")
    ↓
AI: Found 10 relevant projects, from 500 stars to 50k stars.
    Do you want a standalone blog (like Hugo/Hexo) or a multi-user platform?
     - Standalone blog (simple, great SEO)
     - Multi-user platform (complex features, needs admin backend)
     - Recommend based on GitHub projects
```

#### Mandatory Code Reuse — Stop reinventing wheels

All read code goes into a local knowledge base, searchable at any time.
**Reuse-first** is an iron rule baked into the system prompt:

> "If you can find an existing implementation, don't write from scratch. Violating this rule = invalid output."

Reused code is automatically sourced:

```python
# Source: tiangolo/fastapi/docs_src/sql_app/main.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
```

#### Gets Smarter Over Time — Your personal project knowledge base

Every search is saved to local SQLite. Researched "e-commerce mini program" last time? Start from history this time, no need to search again.

```
→ search_history("e-commerce mini program")
  Category 'e-commerce mini program' previously read repos:
    - justjavac/wechat-app-eshop (JavaScript) @ 2026-03-15
    - xxx/shop-wxapp (TypeScript) @ 2026-03-14
  → Has records, use search_code for specific implementations
```

#### GitHub API + Bing Dual Fallback

- GitHub Search API: high quality, sorted by stars (60 req/hr free, 5000 with Token)
- Bing search fallback: free, unlimited quota, no API key needed
- Auto-degrade on rate limit — no manual intervention

#### Zero git clone · Zero vector DB · Only 1 dependency

- All via GitHub REST API — no need to clone repos locally
- SQLite + FTS5 full-text index — no vector database or embedding model needed
- Runtime depends only on `mcp>=1.0`, everything else is Python stdlib
- Startup < 1 second, memory footprint < 50MB

---

### With vs Without

| | Without github-code-rag | With github-code-rag |
|---|---|---|
| AI dives into code | Writes nonstop | Searches GitHub first |
| Requirement understanding | Guesses | Confirms iteratively based on real projects |
| Code quality | Writes from scratch | Reuses the best from 20M+ GitHub repos |
| Pitfalls | Steps in every one | Skips what others already learned |
| Each new project | Fresh start every time | Accumulates more over time |
| Source attribution | No idea who wrote what | Auto-tagged `# Source: owner/repo/file.py` |

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
| `search_history` | Query search history for similar projects (first step for every requirement) |
| `search_github` | GitHub official API repo search, sorted by stars |
| `web_search_github` | Bing search fallback, free unlimited quota |
| `list_github_files` | Browse repo directory structure |
| `read_github_file` | Read file content, auto-index to local knowledge base |
| `search_code` | FTS5 full-text search across indexed code |
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
| Function/class name search | Precise | Semantic drift |
| "How to implement auth" | No | Yes |
| Extra dependencies | Zero (SQLite built-in) | Vector DB + Embedding model |
| Download size | < 1MB | Tens ~ hundreds of MB |
| Search latency | < 10ms | Tens ~ hundreds of ms |

Our approach: **two-phase search**.
First use GitHub Search to find the right repos ("which project is worth referencing"), then use FTS5 to pinpoint code inside repos ("where's the implementation").

Vector search? For code, it's often an oversold solution.

---

### Comparison

| Feature | github-code-rag | codedb | codebase-rag | Official GitHub MCP |
|---|---|---|---|---|
| Requirements analysis Agent guidance | Yes | No | No | No |
| Mandatory code reuse methodology | Yes | No | No | No |
| Search history / category accumulation | Yes | No | No | No |
| Search public GitHub repos | Yes | No (local only) | Yes (needs clone) | Yes |
| Local code indexing | Yes (FTS5) | Yes (Zig custom) | Yes (FTS5 + vector) | No |
| Zero git clone | Yes | N/A | No | Yes |
| Free search fallback (Bing) | Yes | No | No | No |
| External dependencies | 1 (mcp) | 0 (single binary) | Many (Bun + ONNX) | Many |
| Startup time | < 1s | Very fast | Slow | Fast |

In one sentence:

- codedb / codebase-rag = faster, better code search tools
- github-code-rag = methodology-driven requirements analysis Agent + code search

Anyone can build tools. Methodology + tools is the moat.

---

### Project Structure

```
├── server/
│   └── mcp_server.py          # MCP server + system prompt (core methodology)
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

**Will you add vector search?**

Maybe, but it's not the current priority. Our experience so far: find the right repo first > precise search within repo > semantic search. The actual benefit of vector search for code isn't as big as marketing claims. If you have strong demand, feel free to open an Issue.

---

### Contributing

- Found a bug → open an Issue
- New idea → open an Issue to discuss first
- Code contribution → Fork + PR
- Find it useful → star it, help more people discover it
