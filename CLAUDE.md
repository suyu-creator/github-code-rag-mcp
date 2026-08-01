# github-code-rag-mcp

基于 MCP 协议的 GitHub Code RAG 工具。通过系统提示词优化 AI 提问流程（先搜再问、逐步确认需求），SQLite + FTS5 存储代码索引与搜索历史，实现从 GitHub 检索到代码复用的完整链路。零外部依赖。

## 项目结构

```
├── server/
│   └── mcp_server.py          # MCP 服务器入口，定义所有工具
├── github/
│   └── connector.py           # GitHub REST API 封装（纯 urllib）
├── core/
│   ├── models.py              # 数据模型（dataclass）
│   └── retrieval_engine.py    # FTS5 搜索引擎
├── storage/
│   └── sqlite_storage.py      # SQLite 持久化（FTS5 + WAL 模式）
├── tests/
│   ├── test_retrieval.py
│   └── test_storage.py
├── .well-known/
│   └── mcp.json               # MCP 注册配置
├── pyproject.toml              # 项目配置与入口
└── requirements.txt
```

## 工具列表

| 工具 | 说明 |
|------|------|
| `search_github` | GitHub API 搜索仓库 |
| `web_search_github` | Bing 搜索 GitHub（API 限流时替代） |
| `search_history` | 查询搜索历史 |
| `search_code` | FTS5 全文搜索已读代码 |
| `list_github_files` | 浏览仓库目录 |
| `read_github_file` | 读取文件并自动索引 |
| `index_status` | 查看索引状态 |
| `db_inspect` | 查看数据库结构 |
| `db_cleanup` | 清理历史数据 |

## 快速开始

```bash
# 安装依赖
uv sync

# 配置 GitHub Token（可选，不配限 60 次/时）
export GITHUB_TOKEN=ghp_xxx

# 运行（stdio 模式）
uv run github-code-rag
```

## 测试

```bash
uv run pytest
```

## 技术特点

- **零外部依赖**：仅 `mcp>=1.0`
- **零 Embedding**：纯 FTS5 trigram 全文搜索，无需向量数据库
- **零 git clone**：通过 GitHub REST API 直接读取文件
- 内置 Bing 搜索作为 GitHub API 限流时的免费替代
- 自动记录搜索历史，支持增量检索
- 提供数据库管理和清理工具