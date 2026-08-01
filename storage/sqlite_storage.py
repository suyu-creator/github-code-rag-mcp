"""SQLite persistence with FTS5 full-text search + search history.

Two core features:
1. File content indexing with FTS5 for code search
2. Search history registry (category → repos) for incremental updates

Reference: srclight db.py, dinosn/claude-recall
"""

from __future__ import annotations

import os
import sqlite3
import time
from typing import List, Optional, Tuple

from core.models import RepoInfo, SearchHistory, SearchResult


# Common directories to skip when indexing repos
SKIP_DIRS = frozenset({
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox",
    "dist", "build", "target", "bin", "obj", ".eggs",
    ".svn", ".hg", ".idea", ".vscode", "images", "fonts",
})

# Source file extensions to index
SOURCE_EXTENSIONS = frozenset({
    ".py", ".js", ".ts", ".jsx", ".tsx", ".rs", ".go", ".java",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".rb", ".php", ".swift",
    ".kt", ".scala", ".m", ".mm", ".dart", ".lua", ".r", ".sql",
    ".sh", ".bash", ".zsh", ".yaml", ".yml", ".toml", ".ini",
    ".cfg", ".conf", ".md", ".rst", ".txt", ".json", ".xml",
    ".css", ".scss", ".less", ".html", ".vue", ".svelte",
})


class Storage:
    """SQLite-backed persistence with FTS5 code search and search history."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def _init_db(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS repos (
                name TEXT PRIMARY KEY,
                url TEXT DEFAULT '',
                language TEXT DEFAULT '',
                indexed_at TEXT DEFAULT '',
                file_count INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                category TEXT NOT NULL,
                repo_name TEXT NOT NULL,
                repo_url TEXT DEFAULT '',
                language TEXT DEFAULT '',
                indexed_at TEXT DEFAULT '',
                PRIMARY KEY (category, repo_name)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo TEXT NOT NULL,
                file_path TEXT NOT NULL,
                language TEXT DEFAULT '',
                content TEXT DEFAULT '',
                indexed_at TEXT DEFAULT '',
                UNIQUE(repo, file_path)
            )
        """)
        # FTS5 on file content for code search
        try:
            conn.executescript("""
                CREATE VIRTUAL TABLE IF NOT EXISTS file_content_fts
                USING fts5(
                    file_path, content,
                    tokenize='trigram',
                    content=files,
                    content_rowid=id
                );

                -- Triggers to keep FTS5 in sync with files table
                CREATE TRIGGER IF NOT EXISTS files_ai AFTER INSERT ON files BEGIN
                    INSERT INTO file_content_fts(rowid, file_path, content)
                    VALUES (new.id, new.file_path, new.content);
                END;

                CREATE TRIGGER IF NOT EXISTS files_ad AFTER DELETE ON files BEGIN
                    INSERT INTO file_content_fts(file_content_fts, rowid, file_path, content)
                    VALUES('delete', old.id, old.file_path, old.content);
                END;

                CREATE TRIGGER IF NOT EXISTS files_au AFTER UPDATE ON files BEGIN
                    INSERT INTO file_content_fts(file_content_fts, rowid, file_path, content)
                    VALUES('delete', old.id, old.file_path, old.content);
                    INSERT INTO file_content_fts(rowid, file_path, content)
                    VALUES (new.id, new.file_path, new.content);
                END;
            """)
        except sqlite3.OperationalError:
            # FTS5 might not be available
            # Fallback: create regular FTS5 tables without content sync
            conn.executescript("""
                CREATE VIRTUAL TABLE IF NOT EXISTS file_content_fts
                USING fts5(file_path, content, tokenize='trigram');
            """)
        conn.commit()

    # ── File indexing ────────────────────────────────────────────────

    def index_file(self, repo: str, file_path: str, content: str) -> None:
        """Index a single file into the files table and FTS5 index."""
        language = self._detect_language(file_path)
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO files
               (repo, file_path, language, content, indexed_at)
               VALUES (?, ?, ?, ?, ?)""",
            (repo, file_path, language, content, now),
        )
        conn.commit()

    def index_repo_files(self, repo: str, repo_path: str) -> int:
        """Walk a repo directory and index all source files.

        Returns:
            Number of files indexed
        """
        count = 0
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                if ext not in SOURCE_EXTENSIONS:
                    continue
                file_path = os.path.join(root, fname)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    rel_path = os.path.relpath(file_path, repo_path)
                    self.index_file(repo, rel_path, content)
                    count += 1
                except Exception:
                    continue
        return count

    def delete_repo_files(self, repo: str) -> None:
        """Delete all files for a repository from the index."""
        conn = self._get_conn()
        # Triggers handle FTS5 cleanup automatically
        conn.execute("DELETE FROM files WHERE repo = ?", (repo,))
        conn.commit()

    # ── FTS5 search ──────────────────────────────────────────────────

    def search_code(
        self, query: str, top_k: int = 10, repo: Optional[str] = None
    ) -> List[SearchResult]:
        """Search indexed code using FTS5 trigram search.

        Args:
            query: Search keywords (code patterns, function names, etc.)
            top_k: Maximum results
            repo: Optional repo filter

        Returns:
            List of SearchResult with matched file paths and snippets
        """
        # Build FTS5 query: match individual words across content
        words = [w.strip() for w in query.split() if len(w.strip()) >= 2]
        if not words:
            return []

        fts_query = " OR ".join(words)

        try:
            sql = """
                SELECT f.repo, f.file_path, f.language, f.content,
                       rank
                FROM file_content_fts fts
                JOIN files f ON fts.rowid = f.id
                WHERE file_content_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """
            params: List = [fts_query, top_k * 2]

            if repo:
                sql = """
                    SELECT f.repo, f.file_path, f.language, f.content,
                           rank
                    FROM file_content_fts fts
                    JOIN files f ON fts.rowid = f.id
                    WHERE file_content_fts MATCH ?
                      AND f.repo = ?
                    ORDER BY rank
                    LIMIT ?
                """
                params = [fts_query, repo, top_k * 2]

            rows = self._get_conn().execute(sql, params).fetchall()
        except sqlite3.OperationalError:
            return []

        results = []
        for row in rows:
            repo_name, file_path, language, content, rank = row
            # Extract snippet around the first match
            snippet = self._extract_snippet(content, words[0])
            results.append(SearchResult(
                repo=repo_name,
                file_path=file_path,
                language=language,
                snippet=snippet,
                score=self._rank_to_score(float(rank)),
                matched_by="fts5",
            ))

        # Sort by score descending, take top_k
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    @staticmethod
    def _extract_snippet(content: str, keyword: str, context_lines: int = 2) -> str:
        """Extract a snippet around the first occurrence of keyword."""
        if not content or not keyword:
            return content[:500] if content else ""

        lines = content.splitlines()
        keyword_lower = keyword.lower()

        for i, line in enumerate(lines):
            if keyword_lower in line.lower():
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                snippet_lines = []
                for j in range(start, end):
                    prefix = "..." if j == start and start > 0 else ""
                    suffix = "..." if j == end - 1 and end < len(lines) else ""
                    snippet_lines.append(f"{prefix}{lines[j]}{suffix}")
                return "\n".join(snippet_lines)

        # No match found in line-by-line, return first few lines
        return "\n".join(lines[:5])

    @staticmethod
    def _rank_to_score(rank: float) -> float:
        """Convert FTS5 rank (negative = better) to a 0-1 score."""
        # FTS5 BM25 rank: negative is good, lower is better
        # Map: rank=-10 → score=1.0, rank=0 → score=0.5, rank=10 → score=0.0
        score = 1.0 / (1.0 + abs(rank))
        return round(score, 4)

    @staticmethod
    def _detect_language(file_path: str) -> str:
        """Detect language from file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        mapping = {
            ".py": "python", ".js": "javascript", ".ts": "typescript",
            ".jsx": "javascript", ".tsx": "typescript", ".rs": "rust",
            ".go": "go", ".java": "java", ".c": "c", ".cpp": "cpp",
            ".cs": "csharp", ".rb": "ruby", ".php": "php", ".swift": "swift",
            ".kt": "kotlin", ".scala": "scala", ".dart": "dart",
            ".html": "html", ".css": "css", ".md": "markdown",
            ".sql": "sql", ".sh": "shell", ".yaml": "yaml", ".json": "json",
        }
        return mapping.get(ext, "")

    # ── Search history ───────────────────────────────────────────────

    def record_search(self, category: str, repo: RepoInfo) -> None:
        """Record that a repo was found and indexed for a category."""
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO search_history
               (category, repo_name, repo_url, language, indexed_at)
               VALUES (?, ?, ?, ?, ?)""",
            (category, repo.name, repo.url, repo.language, repo.indexed_at),
        )
        conn.commit()

    def get_search_history(self, category: str) -> List[SearchHistory]:
        """Get all repos indexed for a given category."""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT category, repo_name, repo_url, language, indexed_at
               FROM search_history WHERE category = ?
               ORDER BY indexed_at DESC""",
            (category,),
        ).fetchall()
        return [
            SearchHistory(
                category=r[0], repo_name=r[1], repo_url=r[2] or "",
                language=r[3] or "", indexed_at=r[4] or "",
            )
            for r in rows
        ]

    def get_all_categories(self) -> List[str]:
        """Get all distinct search categories."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT DISTINCT category FROM search_history ORDER BY category"
        ).fetchall()
        return [r[0] for r in rows]

    def get_latest_index_time(self, category: str) -> Optional[str]:
        """Get the most recent index time for a category."""
        conn = self._get_conn()
        row = conn.execute(
            """SELECT MAX(indexed_at) FROM search_history WHERE category = ?""",
            (category,),
        ).fetchone()
        return row[0] if row and row[0] else None

    # ── Repository management ────────────────────────────────────────

    def save_repo_info(self, repo: RepoInfo) -> None:
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO repos
               (name, url, language, indexed_at, file_count)
               VALUES (?, ?, ?, ?, ?)""",
            (repo.name, repo.url, repo.language, repo.indexed_at, repo.file_count),
        )
        conn.commit()

    def list_indexed_repos(self) -> List[RepoInfo]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT name, url, language, indexed_at, file_count FROM repos"
        ).fetchall()
        return [
            RepoInfo(name=r[0], url=r[1] or "", language=r[2] or "",
                     indexed_at=r[3] or "", file_count=r[4])
            for r in rows
        ]

    def delete_repo_data(self, repo_name: str) -> None:
        """Delete all data for a repository."""
        conn = self._get_conn()
        conn.execute("DELETE FROM repos WHERE name = ?", (repo_name,))
        conn.execute("DELETE FROM search_history WHERE repo_name = ?", (repo_name,))
        conn.execute("DELETE FROM files WHERE repo = ?", (repo_name,))
        conn.commit()

    def get_stats(self) -> dict:
        conn = self._get_conn()
        repos = conn.execute("SELECT COUNT(*) FROM repos").fetchone()[0]
        files = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        categories = conn.execute(
            "SELECT COUNT(DISTINCT category) FROM search_history"
        ).fetchone()[0]
        has_fts = False
        try:
            has_fts = conn.execute(
                "SELECT COUNT(*) FROM file_content_fts"
            ).fetchone()[0] > 0
        except sqlite3.OperationalError:
            pass
        return {
            "repos": repos,
            "files": files,
            "categories": categories,
            "has_fts": has_fts,
            "db_path": self.db_path,
        }