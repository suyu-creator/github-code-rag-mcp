<div align="center"><pre>
     ██████╗ ██╗████████╗██╗  ██╗██╗   ██╗██████╗      ██████╗ ██████╗ ██████╗ ███████╗
    ██╔════╝ ██║╚══██╔══╝██║  ██║██║   ██║██╔══██╗    ██╔════╝██╔═══██╗██╔══██╗██╔════╝
    ██║  ███╗██║   ██║   ███████║██║   ██║██████╔╝    ██║     ██║   ██║██║  ██║█████╗
    ██║   ██║██║   ██║   ██╔══██║██║   ██║██╔══██╗    ██║     ██║   ██║██║  ██║██╔══╝
    ╚██████╔╝██║   ██║   ██║  ██║╚██████╔╝██████╔╝    ╚██████╗╚██████╔╝██████╔╝███████╗
     ╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═════╝      ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝
        — 让 AI 直接搜 GitHub 仓库 · 按 star 排序 · 双通道兜底 —
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
  让你的 AI 直接搜 2 亿+ 公开仓库，按 star 排序找到最成熟的项目。<br/>
  <br/>
  <em>不用 clone、不用装插件、不用打开浏览器 —— AI 写代码时顺手就把 GitHub 搜了。</em>
</p>

---

## 一句话介绍

一个让 AI **实时搜 GitHub 仓库**的 MCP 服务器。
写认证？搜一下。写中间件？搜一下。写支付？搜一下。
AI 写每一行代码之前，先去 GitHub 找最好的项目参考，**禁止从零造轮子**。
还内置了一套「需求分析 Agent」方法论，让 AI 先调研再动手，不瞎猜。

---

## 核心能力

### 🔥 实时搜 GitHub 仓库 + 读代码

按 star 排序，优先挑最成熟的项目。支持按语言、star 数筛选（如 `python stars:>1000`）。
选定仓库后用 `read_github_file` 读关键文件，实现思路直接抄，来源自动标注。

```
用户：帮我找个 FastAPI 数据库连接的开源项目
    ↓
AI：search_github("fastapi sqlalchemy database stars:>1000")
    ↓
AI：我找到了这些高 star 项目：
  1. tiangolo/fastapi — Python | ⭐ 80000 | FastAPI framework
  2. sqlalchemy/sqlalchemy — Python | ⭐ 10000 | The Python SQL Toolkit
  ...
↓
AI：read_github_file("tiangolo/fastapi", "docs_src/sql_app/main.py")
    ↓
AI：我参考了 FastAPI 官方示例，给你写好了：

# Source: tiangolo/fastapi/docs_src/sql_app/main.py
from sqlalchemy import create_engine
...
```

### 🔄 GitHub API + 官方搜索页双路兜底，不怕限流

- GitHub Search API：质量最高，按 star 排序（60 次/时免费，配 Token 5000 次/时）
- GitHub 官方搜索页兜底：免费无限额度，限流自动降级
- 零 git clone：全部走 REST API，不占本地磁盘

### 🧠 附赠：需求分析 Agent —— 先调研再动手

系统提示词硬编码了工作流，AI 不会上来就瞎写。
它会先判断需求是否明确，搜同类项目，基于真实项目反问你需求，确认清楚了才给结论。

### ⚡ 零 git clone · 仅 1 个依赖

- 全部走 GitHub REST API，不需要 clone 仓库
- 运行时只依赖 `mcp>=1.0`，其他全是 Python 标准库
- 启动 < 1 秒，内存 < 50MB

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

没有 Token 也能用 —— 内置 GitHub 官方搜索页兜底，免费无限额度。
有 Token 的话 GitHub API 额度从 60 次/时 → 5000 次/时。

### 3. 配置到你的 AI 客户端

见下面的「客户端配置」章节。

### 4. 试试这个

装好后跟你的 AI 说：

> "帮我找个 React 管理后台的开源项目，先去 GitHub 搜一下"

看看它会不会先搜 GitHub，再基于搜到的项目给你推荐。

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

### Codex CLI

编辑 `~/.codex/config.toml`，添加：

```toml
[mcp_servers.github-code-rag]
command = "github-code-rag"
```

> 所有支持 MCP 协议的客户端都能用。如果你用的客户端不在上面列表里，配置方式基本一样 —— 把 command 指向 `github-code-rag` 即可。

---

## 工具列表

| 工具 | 说明 |
|---|---|
| `search_github` | GitHub 官方 API 搜索仓库，按 star 排序 |
| `web_search_github` | GitHub 官方搜索页兜底，免费无限额度 |
| `read_github_file` | 读取仓库文件内容，自动标注来源 |

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
│  │    · 先判断需求清晰度 · 先搜再问                 │     │
│  └───────────────────────┬─────────────────────────┘     │
│                          │ 指导 AI 怎么用工具             │
│  ┌───────────────────────▼─────────────────────────┐     │
│  │  3 个 MCP 工具                                   │     │
│  │  search_github / web_search_github / read_file  │     │
│  └───────────┬───────────────────────────┬─────────┘     │
│              │                           │               │
│ ┌────────────▼───────────┐   ┌───────────▼──────────┐    │
│ │  GitHub Search API     │   │  GitHub 官方搜索页    │    │
│ │  按 star 排序           │   │  免费无限兜底         │    │
│ │  零 git clone          │   │                      │    │
│ └────────────────────────┘   └──────────────────────┘    │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

---

## 项目结构

```
├── server/
│   ├── mcp_server.py          # MCP 服务器 + 系统提示词（3 个工具）
│   └── __main__.py
├── github/
│   └── connector.py           # GitHub API 封装（纯 urllib，零依赖）
├── core/
│   └── models.py              # 数据模型
├── tests/
│   └── test_search.py         # 两个搜索工具的测试
├── .well-known/mcp.json       # SSE 模式配置
└── pyproject.toml
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
uv run --with pytest pytest

# 手动启动（stdio 模式）
uv run github-code-rag
```

**环境变量：**

```
GITHUB_TOKEN=ghp_xxx           # GitHub API Token（推荐）
```

---

## FAQ

**支持哪些 MCP 客户端？**

所有支持 MCP 协议的 —— Claude Code、Claude Desktop、Cursor、Windsurf、Cline、Codex、Gemini CLI、OpenCode… 只要能配 MCP server 就能用。

**我的代码会上传吗？**

不会。本工具只做仓库搜索，GitHub API 只用来查询公开仓库元数据，你的代码不会发出去。

**为什么不直接用 gh CLI？**

因为 MCP 工具要对 AI 透明 —— AI 不需要知道你装了什么 CLI，它只需要调用工具就行。而且纯 Python 实现，零系统依赖。

**GitHub API 限流了怎么办？**

自动降级到 GitHub 官方搜索页，免费无限额度，不需要额外配置。

---

## English

<div align="center"><pre>
     ██████╗ ██╗████████╗██╗  ██╗██╗   ██╗██████╗      ██████╗ ██████╗ ██████╗ ███████╗
    ██╔════╝ ██║╚══██╔══╝██║  ██║██║   ██║██╔══██╗    ██╔════╝██╔═══██╗██╔══██╗██╔════╝
    ██║  ███╗██║   ██║   ███████║██║   ██║██████╔╝    ██║     ██║   ██║██║  ██║█████╗
    ██║   ██║██║   ██║   ██╔══██║██║   ██║██╔══██╗    ██║     ██║   ██║██║  ██║██╔══╝
    ╚██████╔╝██║   ██║   ██║  ██║╚██████╔╝██████╔╝    ╚██████╗╚██████╔╝██████╔╝███████╗
     ╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═════╝      ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝
       — Let AI search GitHub repos · Star-sorted · Dual-channel fallback —
</pre></div>

### In One Sentence

An MCP server that lets your AI **search GitHub repositories in real time**.
Writing auth? Search first. Writing middleware? Search first. Writing payment integration? Search first.
Before AI writes any code, it finds the best projects on GitHub — **no reinventing the wheel**.
Also includes a "requirements analysis Agent" methodology so AI researches before answering, no guessing.

### Core Capabilities

- **Real-time GitHub repo search** — sorted by stars, filterable by language and star count.
- **Read files from any repo** — `read_github_file` fetches file content with automatic source attribution.
- **Dual-channel fallback** — GitHub Search API first; auto-degrade to the official search page (free, unlimited) on rate limits.
- **Bonus: Requirements Analysis Agent** — the system prompt hardcodes a workflow so AI judges requirement clarity, searches first, and asks one question at a time before concluding.
- **Zero git clone · 1 dependency** — all via GitHub REST API; only `mcp>=1.0` at runtime; starts in < 1s.

### Tools

| Tool | Description |
|---|---|
| `search_github` | GitHub official API repo search, sorted by stars |
| `web_search_github` | GitHub official search page fallback, free unlimited quota |
| `read_github_file` | Read file content from a repo, with source attribution |

### Development

```bash
git clone https://github.com/suyu-creator/github-code-rag-mcp.git
cd github-code-rag-mcp
uv sync
uv run --with pytest pytest
uv run github-code-rag
```

**Environment variables:**

```
GITHUB_TOKEN=ghp_xxx           # GitHub API Token (recommended)
```

---

## 参与贡献

- 发现 Bug → 提 Issue
- 有新想法 → 先开 Issue 讨论
- 代码贡献 → Fork + PR
- 觉得好用 → 点个 star，让更多人看到
