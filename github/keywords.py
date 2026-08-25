"""Chinese → English keyword normalization for GitHub repo search.

GitHub's relevance ranking is unreliable for CJK text (it matches README
content full-text, so Chinese queries return mostly low-quality demo repos).
This module translates common Chinese terms into English technical keywords
and enforces a minimum star filter so searches surface mature, reusable
projects. Pure-English queries pass through untouched.
"""

from __future__ import annotations

import re
from typing import Tuple

_CN_RE = re.compile(r"[一-鿿]+")

# Chinese term → English technical keyword(s). Longest-first matching below,
# so compound terms like 电商网站 win over their parts.
CN_TO_EN: dict[str, str] = {
    # commerce / apps
    "电商平台": "ecommerce", "电商网站": "ecommerce", "电商系统": "ecommerce",
    "电商": "ecommerce", "商城系统": "ecommerce", "商城": "ecommerce",
    "购物车": "ecommerce", "购物": "ecommerce", "商店": "shop",
    # content / social
    "博客系统": "blog", "博客": "blog", "论坛": "forum", "社区": "community",
    "相册": "gallery", "书签": "bookmarks", "新闻": "news", "资讯": "news",
    # productivity
    "待办": "todo", "记事本": "notes", "笔记应用": "notes", "笔记": "notes",
    "日历": "calendar", "日程": "calendar", "记账": "accounting", "财务": "finance",
    "密码管理器": "password manager", "简历": "resume", "表单": "form",
    # communication
    "即时通讯": "chat", "聊天": "chat", "对话": "chat", "客服": "chat",
    "消息推送": "push notification", "推送": "push notification", "通知": "notification",
    # infra / admin
    "管理系统": "admin dashboard", "管理后台": "admin dashboard", "后台": "admin",
    "数据库": "database", "缓存": "cache", "消息队列": "message queue", "队列": "queue",
    "认证": "auth", "登录": "auth", "权限": "rbac", "支付": "payment",
    "监控": "monitoring", "告警": "alerting", "日志": "logging",
    "部署": "deploy", "容器": "docker", "虚拟化": "container", "自动化": "automation",
    "工作流": "workflow",
    # developer tooling
    "脚手架": "starter template", "模板": "starter template", "骨架": "boilerplate",
    "工具箱": "toolkit", "工具": "tool", "编辑器": "editor", "测试": "testing",
    "单元测试": "testing", "可视化": "chart", "图表": "chart", "图表库": "chart",
    # media
    "播放器": "player", "下载器": "downloader", "图床": "image hosting",
    "图片上传": "image hosting", "图片生成": "image generation", "绘图": "image generation",
    "视频生成": "video generation", "视频": "video", "音乐": "music", "图片": "image",
    "壁纸": "wallpaper", "头像": "avatar", "文字识别": "ocr", "语音合成": "tts",
    "文字转语音": "tts", "语音识别": "speech recognition", "语音": "voice",
    "翻译": "translate", "爬虫": "crawler", "抓取": "scraper", "短链接": "url shortener",
    "知识库": "wiki", "文档站": "docs site",
    # AI / agents
    "智能体": "agent", "代理": "agent", "大模型": "llm", "语言模型": "llm",
    "提示词": "prompt", "微调": "fine-tuning", "训练": "fine-tuning",
    "视觉": "vision", "看图": "vision",
    # platform / stack
    "小程序": "mini program", "前端": "frontend", "后端": "backend",
    "桌面应用": "desktop app", "客户端": "desktop app", "网站": "website",
    "官网": "website", "天气": "weather", "地图": "map", "股票": "stock",
}

_CN_TO_EN_SORTED = sorted(CN_TO_EN.items(), key=lambda kv: len(kv[0]), reverse=True)

# Minimum star filter applied only to queries we had to translate, so the
# result set skips throwaway demo repos. Callers can override with an
# explicit "stars:>N" in their query.
DEFAULT_STAR_FILTER = "stars:>50"


def normalize_query(query: str) -> str:
    """Translate Chinese terms in a query to English keywords.

    Returns the query unchanged when it contains no Chinese, or when every
    Chinese term is outside the mapping table (safe degradation — never
    silently drop a query the user explicitly asked for).
    """
    if not _CN_RE.search(query):
        return query

    translated = query
    for cn, en in _CN_TO_EN_SORTED:
        translated = translated.replace(cn, en)
    translated = _CN_RE.sub("", translated)
    translated = re.sub(r"\s+", " ", translated).strip()

    if not translated:
        return query
    return translated


def ensure_star_filter(query: str) -> str:
    """Append a minimum star filter unless the query already has one."""
    if "stars:" in query:
        return query
    return f"{query.strip()} {DEFAULT_STAR_FILTER}"


def build_search_query(query: str) -> Tuple[str, bool]:
    """Return (final_query, was_translated).

    was_translated is True only when Chinese input actually produced English
    keywords; in that case a minimum star filter is appended too.
    """
    normalized = normalize_query(query)
    if normalized == query:
        return query, False
    return ensure_star_filter(normalized), True
