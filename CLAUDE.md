# GitHub Code RAG MCP

## 工具优先级

搜索 GitHub 相关问题时，必须按以下优先级使用工具：

1. **github-code-rag 的 `search_github`** — 优先使用，GitHub API 搜索
2. **github-code-rag 的 `web_search_github`** — search_github 限流时用，免费无限
3. **github-code-rag 的 `search_history`** — 查历史记录
4. **github-code-rag 的 `search_code`** — 搜已读代码

**禁止使用 Tavily、Exa 等外部搜索工具代替 github-code-rag 的内置搜索工具。** 它们搜不到 GitHub 仓库的详细信息。

## 工作流

用户说"做个XX"时：
1. 先调 `search_history("XX")` 查历史
2. 没有记录 → `search_github("XX")` 搜 GitHub
3. `list_github_files(url)` 浏览目录
4. `read_github_file(url, path)` 读文件