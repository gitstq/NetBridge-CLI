"""小宇宙播客插件 - 调用小宇宙API获取播客信息

通过小宇宙API获取播客节目、单集信息和评论。
"""

import json
import re
from typing import Any, Dict, List, Optional

from .base import BasePlugin
from ..core.normalizer import NormalizedResult, Normalizer
from ..utils.network import get_json, get_text, NetworkError
from ..utils.logger import get_logger

logger = get_logger("netbridge.plugin.xiaoyuzhou")

# 小宇宙API
XIAOYUZHOU_API = "https://www.xiaoyuzhoufm.com"
XIAOYUZHOU_SEARCH = "https://www.xiaoyuzhoufm.com/search"


class XiaoyuzhouPlugin(BasePlugin):
    """小宇宙播客插件

    通过小宇宙API获取播客节目和单集信息。
    """

    @property
    def name(self) -> str:
        return "xiaoyuzhou"

    @property
    def description(self) -> str:
        return "小宇宙播客插件，支持播客搜索和单集信息获取"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def tier(self) -> int:
        return 0  # 核心插件，公开API

    @property
    def platform(self) -> str:
        return "xiaoyuzhou"

    def _get_headers(self) -> Dict[str, str]:
        """获取小宇宙API请求头"""
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.xiaoyuzhoufm.com/",
            "Accept": "application/json",
        }

    def search(self, query: str, limit: int = 10) -> NormalizedResult:
        """搜索小宇宙播客

        Args:
            query: 搜索关键词
            limit: 结果数量限制

        Returns:
            标准化搜索结果
        """
        try:
            params = {
                "q": query,
                "type": 1,  # 1=播客, 2=单集
                "page": 1,
            }
            data = get_json(
                f"{XIAOYUZHOU_API}/search",
                params=params,
                headers=self._get_headers(),
                timeout=15,
            )

            results = []
            pods = data.get("data", {}).get("podcast", {}).get("result", [])
            for pod in pods[:limit]:
                results.append({
                    "title": pod.get("title", ""),
                    "url": f"https://www.xiaoyuzhoufm.com/podcast/{pod.get('id', '')}",
                    "snippet": pod.get("description", "")[:300],
                    "author": pod.get("author", ""),
                    "metadata": {
                        "podcast_id": pod.get("id", ""),
                        "episode_count": pod.get("episode_count", 0),
                        "subscriber_count": pod.get("subscriber_count", 0),
                    },
                })

            # 也搜索单集
            episodes = data.get("data", {}).get("episode", {}).get("result", [])
            for ep in episodes[:limit]:
                results.append({
                    "title": ep.get("title", ""),
                    "url": f"https://www.xiaoyuzhoufm.com/episode/{ep.get('eid', '')}",
                    "snippet": ep.get("description", "")[:300],
                    "author": ep.get("podcast_title", ""),
                    "published_at": ep.get("pub_time", ""),
                    "metadata": {
                        "episode_id": ep.get("eid", ""),
                        "podcast_id": ep.get("podcast_id", ""),
                        "duration": ep.get("duration", 0),
                    },
                })

            if not results:
                results.append({
                    "title": "未找到结果",
                    "url": "",
                    "snippet": f"没有找到与 '{query}' 相关的播客内容",
                })

            return Normalizer.create_search_result(
                platform=self.platform,
                results=results[:limit],
            )

        except (NetworkError, Exception) as e:
            logger.warning(f"小宇宙搜索失败: {e}")
            return self._make_error("search", f"搜索失败: {e}")

    def read(self, url_or_id: str) -> NormalizedResult:
        """读取小宇宙播客/单集信息

        Args:
            url_or_id: 播客/单集URL或ID

        Returns:
            标准化读取结果
        """
        try:
            # 判断是播客还是单集
            is_episode = "episode" in url_or_id.lower() or re.match(r"^\d+$", url_or_id.strip())

            if is_episode:
                return self._read_episode(url_or_id)
            else:
                return self._read_podcast(url_or_id)

        except (NetworkError, Exception) as e:
            logger.warning(f"小宇宙读取失败: {e}")
            return self._make_error("read", f"读取失败: {e}")

    def _read_podcast(self, url_or_id: str) -> NormalizedResult:
        """读取播客信息"""
        podcast_id = self._parse_id(url_or_id)

        data = get_json(
            f"{XIAOYUZHOU_API}/podcast/{podcast_id}",
            headers=self._get_headers(),
            timeout=15,
        )

        pod_data = data.get("data", {}).get("podcast", {})
        if not pod_data:
            return self._make_error("read", "播客不存在")

        # 获取最新单集列表
        episodes_data = get_json(
            f"{XIAOYUZHOU_API}/podcast/{podcast_id}/episodes",
            params={"page": 1, "limit": 20},
            headers=self._get_headers(),
            timeout=15,
        )

        content_parts = [
            f"# {pod_data.get('title', '')}",
            "",
            f"**作者**: {pod_data.get('author', '未知')}",
            f"**单集数**: {pod_data.get('episode_count', 0)}",
            f"**订阅数**: {pod_data.get('subscriber_count', 0)}",
            "",
            "## 简介",
            pod_data.get("description", "无简介"),
        ]

        # 添加最新单集
        episodes = episodes_data.get("data", {}).get("episodes", [])
        if episodes:
            content_parts.append("\n## 最新单集")
            for i, ep in enumerate(episodes[:20], 1):
                content_parts.append(
                    f"- {i}. {ep.get('title', '')} "
                    f"({self._format_duration(ep.get('duration', 0))})"
                )

        return Normalizer.create_read_result(
            platform=self.platform,
            title=pod_data.get("title", ""),
            content="\n".join(content_parts),
            url=f"https://www.xiaoyuzhoufm.com/podcast/{podcast_id}",
            author=pod_data.get("author", ""),
            metadata={
                "podcast_id": podcast_id,
                "episode_count": pod_data.get("episode_count", 0),
            },
        )

    def _read_episode(self, url_or_id: str) -> NormalizedResult:
        """读取单集信息"""
        episode_id = self._parse_id(url_or_id)

        data = get_json(
            f"{XIAOYUZHOU_API}/episode/{episode_id}",
            headers=self._get_headers(),
            timeout=15,
        )

        ep_data = data.get("data", {}).get("episode", {})
        if not ep_data:
            return self._make_error("read", "单集不存在")

        content_parts = [
            f"# {ep_data.get('title', '')}",
            "",
            f"**播客**: {ep_data.get('podcast_title', '')}",
            f"**时长**: {self._format_duration(ep_data.get('duration', 0))}",
            f"**发布时间**: {ep_data.get('pub_time', '')}",
            "",
            "## 简介",
            ep_data.get("description", "无简介"),
        ]

        # 获取评论
        try:
            comments_data = get_json(
                f"{XIAOYUZHOU_API}/episode/{episode_id}/comments",
                params={"page": 1},
                headers=self._get_headers(),
                timeout=10,
            )
            comments = comments_data.get("data", {}).get("comments", [])
            if comments:
                content_parts.append("\n## 热门评论")
                for i, comment in enumerate(comments[:10], 1):
                    content_parts.append(
                        f"\n### {i}. {comment.get('user_name', '未知')}"
                    )
                    content_parts.append(comment.get("body", "")[:200])
        except Exception:
            pass

        return Normalizer.create_read_result(
            platform=self.platform,
            title=ep_data.get("title", ""),
            content="\n".join(content_parts),
            url=f"https://www.xiaoyuzhoufm.com/episode/{episode_id}",
            author=ep_data.get("podcast_title", ""),
            published_at=ep_data.get("pub_time", ""),
            metadata={
                "episode_id": episode_id,
                "podcast_id": ep_data.get("podcast_id", ""),
                "duration": ep_data.get("duration", 0),
            },
        )

    def _parse_id(self, url_or_id: str) -> str:
        """解析ID"""
        url_or_id = url_or_id.strip()
        match = re.search(r"xiaoyuzhoufm\.com/(?:podcast|episode)/(\w+)", url_or_id)
        if match:
            return match.group(1)
        return url_or_id

    def _format_duration(self, seconds: int) -> str:
        """格式化时长"""
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    def check_health(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            data = get_json(
                f"{XIAOYUZHOU_API}/search?q=test&type=1&page=1",
                headers=self._get_headers(),
                timeout=10,
            )
            healthy = "data" in data
            return {
                "healthy": healthy,
                "message": "小宇宙API 可用" if healthy else "小宇宙API 返回异常",
                "details": {
                    "version": self.version,
                    "tier": self.tier,
                },
            }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"小宇宙API 不可用: {e}",
                "details": {"version": self.version, "tier": self.tier},
            }

    def get_dependencies(self) -> List[str]:
        return []

    def get_config_schema(self) -> Dict[str, Any]:
        return {}
