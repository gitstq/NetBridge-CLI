"""Reddit插件 - 调用Reddit公开JSON API

通过Reddit的公开JSON API读取帖子和评论，
无需认证即可访问公开内容。
"""

import json
import re
from typing import Any, Dict, List, Optional

from .base import BasePlugin
from ..core.normalizer import NormalizedResult, Normalizer
from ..utils.network import get_json, get_text, NetworkError
from ..utils.logger import get_logger

logger = get_logger("netbridge.plugin.reddit")

# Reddit API
REDDIT_API = "https://www.reddit.com"
REDDIT_OAUTH = "https://oauth.reddit.com"


class RedditPlugin(BasePlugin):
    """Reddit插件

    通过Reddit公开JSON API读取帖子和评论。
    """

    @property
    def name(self) -> str:
        return "reddit"

    @property
    def description(self) -> str:
        return "Reddit插件，支持帖子搜索、读取和评论查看"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def tier(self) -> int:
        return 0  # 核心插件，零依赖（公开API）

    @property
    def platform(self) -> str:
        return "reddit"

    def _get_headers(self) -> Dict[str, str]:
        """获取Reddit API请求头"""
        return {
            "User-Agent": (
                "NetBridge/0.1.0 (AI Agent Internet Capability Engine; "
                "+https://github.com/netbridge)"
            ),
            "Accept": "application/json",
        }

    def search(self, query: str, limit: int = 10) -> NormalizedResult:
        """搜索Reddit帖子

        Args:
            query: 搜索关键词
            limit: 结果数量限制

        Returns:
            标准化搜索结果
        """
        try:
            url = f"{REDDIT_API}/search.json"
            params = {
                "q": query,
                "limit": min(limit, 25),
                "sort": "relevance",
                "type": "link",
            }
            data = get_json(url, params=params, headers=self._get_headers(), timeout=15)

            results = []
            children = data.get("data", {}).get("children", [])
            for child in children[:limit]:
                post = child.get("data", {})
                results.append({
                    "title": post.get("title", ""),
                    "url": f"https://reddit.com{post.get('permalink', '')}",
                    "snippet": post.get("selftext", "")[:300],
                    "author": post.get("author", ""),
                    "published_at": self._format_timestamp(post.get("created_utc", 0)),
                    "metadata": {
                        "subreddit": post.get("subreddit", ""),
                        "score": post.get("score", 0),
                        "num_comments": post.get("num_comments", 0),
                        "upvote_ratio": post.get("upvote_ratio", 0),
                    },
                })

            return Normalizer.create_search_result(
                platform=self.platform,
                results=results,
                metadata={"total": len(children)},
            )

        except (NetworkError, Exception) as e:
            logger.warning(f"Reddit搜索失败: {e}")
            return self._make_error("search", f"搜索失败: {e}")

    def read(self, url_or_id: str) -> NormalizedResult:
        """读取Reddit帖子

        Args:
            url_or_id: 帖子URL或ID

        Returns:
            标准化读取结果
        """
        try:
            # 解析帖子路径
            post_path = self._parse_post_path(url_or_id)

            url = f"{REDDIT_API}{post_path}.json"
            data = get_json(url, headers=self._get_headers(), timeout=15)

            # Reddit返回列表: [0]=帖子, [1]=评论
            if isinstance(data, list) and len(data) >= 1:
                post_data = data[0].get("data", {}).get("children", [{}])[0].get("data", {})

                title = post_data.get("title", "")
                content = post_data.get("selftext", "")
                author = post_data.get("author", "")
                subreddit = post_data.get("subreddit", "")

                # 构建内容
                content_parts = [
                    f"# {title}",
                    "",
                    f"**子版块**: r/{subreddit}",
                    f"**作者**: u/{author}",
                    f"**分数**: {post_data.get('score', 0)}",
                    f"**评论数**: {post_data.get('num_comments', 0)}",
                    "",
                    content or "[链接帖子，无文本内容]",
                ]

                # 添加评论
                if len(data) >= 2:
                    comments = data[1].get("data", {}).get("children", [])
                    if comments:
                        content_parts.append("\n## 评论")
                        for i, comment_child in enumerate(comments[:20], 1):
                            if comment_child.get("kind") != "t1":
                                continue
                            comment = comment_child.get("data", {})
                            comment_text = comment.get("body", "")[:200]
                            content_parts.append(
                                f"\n### {i}. {comment.get('author', '[deleted]')} "
                                f"(+{comment.get('ups', 0)})"
                            )
                            content_parts.append(comment_text)

                return Normalizer.create_read_result(
                    platform=self.platform,
                    title=title,
                    content="\n".join(content_parts),
                    url=f"https://reddit.com{post_data.get('permalink', '')}",
                    author=author,
                    published_at=self._format_timestamp(post_data.get("created_utc", 0)),
                    metadata={
                        "subreddit": subreddit,
                        "score": post_data.get("score", 0),
                        "num_comments": post_data.get("num_comments", 0),
                    },
                )

            return self._make_error("read", "无法解析帖子数据")

        except (NetworkError, Exception) as e:
            logger.warning(f"Reddit读取失败: {e}")
            return self._make_error("read", f"读取失败: {e}")

    def _parse_post_path(self, url_or_id: str) -> str:
        """解析帖子路径"""
        url_or_id = url_or_id.strip()

        # 完整URL
        if "reddit.com" in url_or_id:
            match = re.search(r"(reddit\.com/r/\w+/comments/\w+)", url_or_id)
            if match:
                return "/" + match.group(1)

        # 纯ID
        if url_or_id.startswith("t3_"):
            return f"/comments/{url_or_id[3:]}"

        return f"/comments/{url_or_id}"

    def _format_timestamp(self, utc_timestamp: float) -> str:
        """格式化UTC时间戳"""
        if not utc_timestamp:
            return ""
        from datetime import datetime, timezone
        try:
            dt = datetime.fromtimestamp(utc_timestamp, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except (ValueError, OSError):
            return ""

    def check_health(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            data = get_json(
                f"{REDDIT_API}/r/popular.json?limit=1",
                headers=self._get_headers(),
                timeout=10,
            )
            healthy = "data" in data
            return {
                "healthy": healthy,
                "message": "Reddit API 可用" if healthy else "Reddit API 无响应",
                "details": {
                    "version": self.version,
                    "tier": self.tier,
                },
            }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Reddit API 不可用: {e}",
                "details": {"version": self.version, "tier": self.tier},
            }

    def get_dependencies(self) -> List[str]:
        return []

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "client_id": {
                "type": "string",
                "description": "Reddit OAuth Client ID（可选，用于提高速率限制）",
                "default": "",
            },
            "client_secret": {
                "type": "string",
                "description": "Reddit OAuth Client Secret",
                "default": "",
            },
        }
