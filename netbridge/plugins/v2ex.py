"""V2EX插件 - 调用V2EX公开API

通过V2EX公开API读取帖子、节点信息和最新主题。
"""

import json
from typing import Any, Dict, List, Optional

from .base import BasePlugin
from ..core.normalizer import NormalizedResult, Normalizer
from ..utils.network import get_json, NetworkError
from ..utils.logger import get_logger

logger = get_logger("netbridge.plugin.v2ex")

# V2EX API
V2EX_API = "https://www.v2ex.com/api"


class V2EXPlugin(BasePlugin):
    """V2EX插件

    通过V2EX公开API读取帖子和节点信息。
    """

    @property
    def name(self) -> str:
        return "v2ex"

    @property
    def description(self) -> str:
        return "V2EX插件，支持帖子搜索、读取和节点浏览"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def tier(self) -> int:
        return 0  # 核心插件，公开API

    @property
    def platform(self) -> str:
        return "v2ex"

    def _get_headers(self) -> Dict[str, str]:
        """获取V2EX API请求头"""
        return {
            "User-Agent": "NetBridge/0.1.0 (AI Agent Internet Capability Engine)",
            "Accept": "application/json",
        }

    def search(self, query: str, limit: int = 10) -> NormalizedResult:
        """搜索V2EX帖子

        V2EX API没有直接搜索接口，使用最新主题过滤。

        Args:
            query: 搜索关键词
            limit: 结果数量限制

        Returns:
            标准化搜索结果
        """
        try:
            # 获取最新主题
            data = get_json(
                f"{V2EX_API}/topics/latest.json",
                headers=self._get_headers(),
                timeout=15,
            )

            query_lower = query.lower()
            results = []

            for topic in data:
                title = topic.get("title", "")
                content = topic.get("content", "")
                if query_lower in title.lower() or query_lower in content.lower():
                    results.append({
                        "title": title,
                        "url": f"https://www.v2ex.com/t/{topic.get('id', '')}",
                        "snippet": content[:300],
                        "author": topic.get("member", {}).get("username", ""),
                        "published_at": topic.get("created", "")[:19] if topic.get("created") else "",
                        "metadata": {
                            "node": topic.get("node", {}).get("name", ""),
                            "replies": topic.get("replies", 0),
                        },
                    })

                if len(results) >= limit:
                    break

            if not results:
                # 没有匹配结果，返回最新的帖子
                for topic in data[:limit]:
                    results.append({
                        "title": topic.get("title", ""),
                        "url": f"https://www.v2ex.com/t/{topic.get('id', '')}",
                        "snippet": topic.get("content", "")[:300],
                        "author": topic.get("member", {}).get("username", ""),
                        "published_at": topic.get("created", "")[:19] if topic.get("created") else "",
                        "metadata": {
                            "node": topic.get("node", {}).get("name", ""),
                            "replies": topic.get("replies", 0),
                        },
                    })

            return Normalizer.create_search_result(
                platform=self.platform,
                results=results[:limit],
            )

        except (NetworkError, Exception) as e:
            logger.warning(f"V2EX搜索失败: {e}")
            return self._make_error("search", f"搜索失败: {e}")

    def read(self, url_or_id: str) -> NormalizedResult:
        """读取V2EX帖子

        Args:
            url_or_id: 帖子URL或ID

        Returns:
            标准化读取结果
        """
        try:
            # 解析帖子ID
            topic_id = url_or_id.strip()
            import re
            match = re.search(r"v2ex\.com/t/(\d+)", topic_id)
            if match:
                topic_id = match.group(1)

            data = get_json(
                f"{V2EX_API}/topics/show.json?id={topic_id}",
                headers=self._get_headers(),
                timeout=15,
            )

            if not data or not isinstance(data, list) or len(data) == 0:
                return self._make_error("read", "帖子不存在")

            topic = data[0]
            member = topic.get("member", {})
            node = topic.get("node", {})

            # 获取回复
            replies_data = get_json(
                f"{V2EX_API}/replies/show.json?topic_id={topic_id}&page=1",
                headers=self._get_headers(),
                timeout=15,
            )

            # 构建内容
            content_parts = [
                f"# {topic.get('title', '')}",
                "",
                f"**作者**: {member.get('username', '未知')}",
                f"**节点**: {node.get('name', '')}",
                f"**回复数**: {topic.get('replies', 0)}",
                "",
                "## 正文",
                topic.get("content", "无内容"),
            ]

            # 添加回复
            if replies_data:
                content_parts.append("\n## 回复")
                for i, reply in enumerate(replies_data[:20], 1):
                    reply_member = reply.get("member", {})
                    content_parts.append(
                        f"\n### {i}. {reply_member.get('username', '[deleted]')} "
                        f"(+{reply.get('ups', 0)})"
                    )
                    content_parts.append(reply.get("content", "")[:300])

            return Normalizer.create_read_result(
                platform=self.platform,
                title=topic.get("title", ""),
                content="\n".join(content_parts),
                url=f"https://www.v2ex.com/t/{topic_id}",
                author=member.get("username", ""),
                published_at=topic.get("created", "")[:19] if topic.get("created") else "",
                metadata={
                    "node": node.get("name", ""),
                    "replies": topic.get("replies", 0),
                    "views": topic.get("views", 0),
                },
            )

        except (NetworkError, Exception) as e:
            logger.warning(f"V2EX读取失败: {e}")
            return self._make_error("read", f"读取失败: {e}")

    def check_health(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            data = get_json(
                f"{V2EX_API}/topics/latest.json?limit=1",
                headers=self._get_headers(),
                timeout=10,
            )
            healthy = isinstance(data, list)
            return {
                "healthy": healthy,
                "message": "V2EX API 可用" if healthy else "V2EX API 返回异常",
                "details": {
                    "version": self.version,
                    "tier": self.tier,
                },
            }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"V2EX API 不可用: {e}",
                "details": {"version": self.version, "tier": self.tier},
            }

    def get_dependencies(self) -> List[str]:
        return []

    def get_config_schema(self) -> Dict[str, Any]:
        return {}
