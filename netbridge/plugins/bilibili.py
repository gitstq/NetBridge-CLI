"""B站插件 - 调用B站API进行搜索和视频信息获取

支持视频搜索、视频信息读取和字幕提取。
"""

import json
import re
from typing import Any, Dict, List, Optional

from .base import BasePlugin
from ..core.normalizer import NormalizedResult, Normalizer
from ..utils.network import get_json, get_text, NetworkError
from ..utils.logger import get_logger

logger = get_logger("netbridge.plugin.bilibili")

# B站API
BILIBILI_API = "https://api.bilibili.com"
BILIBILI_SEARCH = "https://api.bilibili.com/x/web-interface/search/type"
BILIBILI_VIDEO = "https://api.bilibili.com/x/web-interface/view"
BILIBILI_WBI = "https://api.bilibili.com/x/web-interface/nav"


class BilibiliPlugin(BasePlugin):
    """B站插件

    支持视频搜索、视频信息读取和字幕提取。
    """

    @property
    def name(self) -> str:
        return "bilibili"

    @property
    def description(self) -> str:
        return "B站插件，支持视频搜索、信息读取和字幕提取"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def tier(self) -> int:
        return 0  # 核心插件，公开API

    @property
    def platform(self) -> str:
        return "bilibili"

    def _get_headers(self) -> Dict[str, str]:
        """获取B站API请求头"""
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.bilibili.com",
            "Accept": "application/json",
        }

    def _get_cookies(self) -> Dict[str, str]:
        """获取B站Cookie（可选）"""
        cookies = self.get_config_value("cookies", {})
        if not cookies:
            import os
            cookie_str = os.environ.get("BILIBILI_COOKIES", "")
            if cookie_str:
                cookies = {}
                for item in cookie_str.split(";"):
                    item = item.strip()
                    if "=" in item:
                        k, v = item.split("=", 1)
                        cookies[k.strip()] = v.strip()
        return cookies

    def _parse_bv_id(self, url_or_id: str) -> str:
        """解析BV号"""
        url_or_id = url_or_id.strip()
        patterns = [
            r"(BV[a-zA-Z0-9]+)",
            r"bilibili\.com/video/(BV[a-zA-Z0-9]+)",
            r"b23\.tv/(BV[a-zA-Z0-9]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
        # 如果是AV号
        av_match = re.search(r"(av\d+)", url_or_id, re.IGNORECASE)
        if av_match:
            return av_match.group(1)
        return url_or_id

    def search(self, query: str, limit: int = 10) -> NormalizedResult:
        """搜索B站视频

        Args:
            query: 搜索关键词
            limit: 结果数量限制

        Returns:
            标准化搜索结果
        """
        try:
            params = {
                "search_type": "video",
                "keyword": query,
                "page": 1,
                "page_size": min(limit, 20),
            }
            data = get_json(
                BILIBILI_SEARCH,
                params=params,
                headers=self._get_headers(),
                cookies=self._get_cookies(),
                timeout=15,
            )

            results = []
            result_data = data.get("data", {})
            if result_data.get("numResults", 0) > 0 or result_data.get("result"):
                items = result_data.get("result", [])
                for item in items[:limit]:
                    # 清理HTML标签
                    title = re.sub(r"<[^>]+>", "", item.get("title", ""))
                    description = re.sub(r"<[^>]+>", "", item.get("description", ""))

                    results.append({
                        "title": title,
                        "url": f"https://www.bilibili.com/video/{item.get('bvid', '')}",
                        "snippet": description[:300],
                        "author": item.get("author", ""),
                        "published_at": item.get("pubdate", ""),
                        "metadata": {
                            "bvid": item.get("bvid", ""),
                            "duration": item.get("duration", ""),
                            "play": item.get("play", 0),
                            "danmaku": item.get("video_review", 0),
                            "favorites": item.get("favorites", 0),
                            "tag": item.get("tag", ""),
                        },
                    })

            if not results:
                results.append({
                    "title": "未找到结果",
                    "url": "",
                    "snippet": f"没有找到与 '{query}' 相关的B站视频",
                })

            return Normalizer.create_search_result(
                platform=self.platform,
                results=results,
            )

        except (NetworkError, Exception) as e:
            logger.warning(f"B站搜索失败: {e}")
            return self._make_error("search", f"搜索失败: {e}")

    def read(self, url_or_id: str) -> NormalizedResult:
        """读取B站视频信息

        Args:
            url_or_id: 视频URL或BV号

        Returns:
            标准化读取结果
        """
        try:
            video_id = self._parse_bv_id(url_or_id)

            params = {}
            if video_id.startswith("BV"):
                params["bvid"] = video_id
            elif video_id.lower().startswith("av"):
                params["aid"] = video_id[2:]
            else:
                params["bvid"] = video_id

            data = get_json(
                BILIBILI_VIDEO,
                params=params,
                headers=self._get_headers(),
                cookies=self._get_cookies(),
                timeout=15,
            )

            video_data = data.get("data", {})
            if not video_data:
                return self._make_error("read", "视频不存在或已被删除")

            owner = video_data.get("owner", {})
            stat = video_data.get("stat", {})

            # 构建内容
            content_parts = [
                f"# {video_data.get('title', '')}",
                "",
                f"**UP主**: {owner.get('name', '未知')}",
                f"**播放量**: {stat.get('view', 0):,}",
                f"**弹幕数**: {stat.get('danmaku', 0):,}",
                f"**点赞数**: {stat.get('like', 0):,}",
                f"**投币数**: {stat.get('coin', 0):,}",
                f"**收藏数**: {stat.get('favorite', 0):,}",
                f"**分享数**: {stat.get('share', 0):,}",
                f"**时长**: {self._format_duration(video_data.get('duration', 0))}",
                f"**发布日期**: {video_data.get('pubdate', '')}",
                "",
                "## 简介",
                video_data.get("desc", "无简介"),
            ]

            # 添加分P信息
            pages = video_data.get("pages", [])
            if pages and len(pages) > 1:
                content_parts.append("\n## 分P列表")
                for i, page in enumerate(pages, 1):
                    content_parts.append(
                        f"- P{i}: {page.get('part', '')} ({self._format_duration(page.get('duration', 0))})"
                    )

            # 尝试获取字幕
            subtitle = video_data.get("subtitle", {})
            subtitle_list = subtitle.get("list", [])
            if subtitle_list:
                content_parts.append("\n## 字幕")
                for sub_info in subtitle_list[:3]:
                    sub_url = sub_info.get("subtitle_url", "")
                    if sub_url:
                        if not sub_url.startswith("http"):
                            sub_url = f"https:{sub_url}"
                        try:
                            sub_data = get_json(sub_url, headers=self._get_headers(), timeout=10)
                            sub_text = " ".join(
                                item.get("content", "")
                                for item in sub_data.get("body", [])
                            )
                            content_parts.append(f"\n### {sub_info.get('lan', '')}")
                            content_parts.append(sub_text[:3000])
                        except Exception:
                            pass
                        break

            url = f"https://www.bilibili.com/video/{video_data.get('bvid', video_id)}"

            return Normalizer.create_read_result(
                platform=self.platform,
                title=video_data.get("title", ""),
                content="\n".join(content_parts),
                url=url,
                author=owner.get("name", ""),
                published_at=str(video_data.get("pubdate", "")),
                metadata={
                    "bvid": video_data.get("bvid", ""),
                    "aid": video_data.get("aid", 0),
                    "cid": video_data.get("cid", 0),
                    "duration": video_data.get("duration", 0),
                    "view": stat.get("view", 0),
                    "danmaku": stat.get("danmaku", 0),
                    "like": stat.get("like", 0),
                    "tags": [t.get("name", "") for t in video_data.get("tags", [])],
                },
            )

        except (NetworkError, Exception) as e:
            logger.warning(f"B站读取失败: {e}")
            return self._make_error("read", f"读取失败: {e}")

    def _format_duration(self, seconds: int) -> str:
        """格式化时长"""
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def check_health(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            data = get_json(
                BILIBILI_WBI,
                headers=self._get_headers(),
                timeout=10,
            )
            healthy = data.get("code", -1) == 0
            return {
                "healthy": healthy,
                "message": "B站API 可用" if healthy else "B站API 返回异常",
                "details": {
                    "version": self.version,
                    "tier": self.tier,
                    "mid": data.get("data", {}).get("mid", "未登录"),
                },
            }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"B站API 不可用: {e}",
                "details": {"version": self.version, "tier": self.tier},
            }

    def get_dependencies(self) -> List[str]:
        return []

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "cookies": {
                "type": "dict",
                "description": "B站Cookie（可选，用于获取更多内容）",
                "default": {},
            },
        }
