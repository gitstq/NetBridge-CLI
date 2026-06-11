"""小红书插件 - Cookie认证读取笔记内容

通过Cookie认证访问小红书API，
支持搜索和读取笔记。
"""

import json
import re
import urllib.parse
from typing import Any, Dict, List, Optional

from .base import BasePlugin
from ..core.normalizer import NormalizedResult, Normalizer
from ..utils.network import get_json, get_text, NetworkError
from ..utils.logger import get_logger

logger = get_logger("netbridge.plugin.xiaohongshu")

# 小红书API
XHS_API = "https://edith.xiaohongshu.com"
XHS_WEB_API = "https://www.xiaohongshu.com"


class XiaohongshuPlugin(BasePlugin):
    """小红书插件

    通过Cookie认证访问小红书API，
    支持搜索和读取笔记内容。
    """

    @property
    def name(self) -> str:
        return "xiaohongshu"

    @property
    def description(self) -> str:
        return "小红书插件，支持笔记搜索和内容读取"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def tier(self) -> int:
        return 1  # 扩展插件，需要Cookie认证

    @property
    def platform(self) -> str:
        return "xiaohongshu"

    def _get_cookies(self) -> Dict[str, str]:
        """获取小红书Cookie"""
        cookies = self.get_config_value("cookies", {})
        if not cookies:
            import os
            cookie_str = os.environ.get("XIAOHONGSHU_COOKIES", "")
            if cookie_str:
                cookies = {}
                for item in cookie_str.split(";"):
                    item = item.strip()
                    if "=" in item:
                        k, v = item.split("=", 1)
                        cookies[k.strip()] = v.strip()
        return cookies

    def _get_headers(self) -> Dict[str, str]:
        """获取小红书API请求头"""
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.xiaohongshu.com/",
            "Origin": "https://www.xiaohongshu.com",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=UTF-8",
        }

    def _parse_note_id(self, url_or_id: str) -> str:
        """解析笔记ID"""
        url_or_id = url_or_id.strip()
        patterns = [
            r"xiaohongshu\.com/explore/([a-f0-9]+)",
            r"xiaohongshu\.com/discovery/item/([a-f0-9]+)",
            r"xhslink\.com/([a-zA-Z0-9]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
        return url_or_id

    def search(self, query: str, limit: int = 10) -> NormalizedResult:
        """搜索小红书笔记

        Args:
            query: 搜索关键词
            limit: 结果数量限制

        Returns:
            标准化搜索结果
        """
        cookies = self._get_cookies()
        if not cookies:
            return self._make_error(
                "search",
                "未配置小红书Cookie，请通过 netbridge config 配置 cookies",
            )

        try:
            params = {
                "keyword": query,
                "page": 1,
                "page_size": min(limit, 20),
                "sort": "general",
                "note_type": 0,
            }
            data = get_json(
                f"{XHS_API}/api/sns/web/v1/search/notes",
                params=params,
                headers=self._get_headers(),
                cookies=cookies,
                timeout=15,
            )

            results = []
            items = data.get("data", {}).get("items", [])
            for item in items[:limit]:
                note = item.get("note_card", {})
                # 清理标题中的特殊字符
                title = note.get("display_title", "")
                desc = note.get("desc", "")[:300]

                results.append({
                    "title": title,
                    "url": f"https://www.xiaohongshu.com/explore/{note.get('note_id', '')}",
                    "snippet": desc,
                    "author": note.get("user", {}).get("nickname", ""),
                    "metadata": {
                        "note_id": note.get("note_id", ""),
                        "type": note.get("type", 0),
                        "liked_count": note.get("interact_info", {}).get("liked_count", "0"),
                        "collected_count": note.get("interact_info", {}).get("collected_count", "0"),
                    },
                })

            return Normalizer.create_search_result(
                platform=self.platform,
                results=results,
            )

        except (NetworkError, Exception) as e:
            logger.warning(f"小红书搜索失败: {e}")
            return self._make_error("search", f"搜索失败: {e}")

    def read(self, url_or_id: str) -> NormalizedResult:
        """读取小红书笔记

        Args:
            url_or_id: 笔记URL或ID

        Returns:
            标准化读取结果
        """
        cookies = self._get_cookies()
        if not cookies:
            return self._make_error(
                "read",
                "未配置小红书Cookie，请通过 netbridge config 配置 cookies",
            )

        try:
            note_id = self._parse_note_id(url_or_id)

            params = {"note_id": note_id}
            data = get_json(
                f"{XHS_API}/api/sns/web/v1/feed",
                params=params,
                headers=self._get_headers(),
                cookies=cookies,
                timeout=15,
            )

            note_data = data.get("data", {}).get("items", [{}])[0].get("note_card", {})
            if not note_data:
                return self._make_error("read", "笔记不存在或已被删除")

            user = note_data.get("user", {})
            interact = note_data.get("interact_info", {})

            # 构建内容
            content_parts = [
                f"# {note_data.get('display_title', '')}",
                "",
                f"**作者**: {user.get('nickname', '未知')}",
                f"**点赞**: {interact.get('liked_count', '0')}",
                f"**收藏**: {interact.get('collected_count', '0')}",
                f"**评论**: {interact.get('comment_count', '0')}",
                f"**发布时间**: {note_data.get('time', '')}",
                "",
                "## 内容",
                note_data.get("desc", "无内容"),
            ]

            # 添加标签
            tag_list = note_data.get("tag_list", [])
            if tag_list:
                content_parts.append("\n## 标签")
                tags = [tag.get("name", "") for tag in tag_list if tag.get("name")]
                content_parts.append(", ".join(tags))

            return Normalizer.create_read_result(
                platform=self.platform,
                title=note_data.get("display_title", ""),
                content="\n".join(content_parts),
                url=f"https://www.xiaohongshu.com/explore/{note_id}",
                author=user.get("nickname", ""),
                metadata={
                    "note_id": note_id,
                    "type": note_data.get("type", 0),
                    "liked_count": interact.get("liked_count", "0"),
                    "collected_count": interact.get("collected_count", "0"),
                },
            )

        except (NetworkError, Exception) as e:
            logger.warning(f"小红书读取失败: {e}")
            return self._make_error("read", f"读取失败: {e}")

    def check_health(self) -> Dict[str, Any]:
        """健康检查"""
        cookies = self._get_cookies()
        has_cookies = bool(cookies)
        return {
            "healthy": has_cookies,
            "message": "小红书Cookie 已配置" if has_cookies else "未配置小红书Cookie",
            "details": {
                "version": self.version,
                "tier": self.tier,
                "authenticated": has_cookies,
            },
        }

    def get_dependencies(self) -> List[str]:
        return []

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "cookies": {
                "type": "dict",
                "description": "小红书Cookie字典",
                "default": {},
            },
        }
