"""Twitter/X插件 - Cookie认证读取推文

通过Cookie认证访问Twitter/X API，
支持读取推文和用户信息。
"""

import json
import re
from typing import Any, Dict, List, Optional

from .base import BasePlugin
from ..core.normalizer import NormalizedResult, Normalizer
from ..utils.network import get_json, get_text, NetworkError
from ..utils.logger import get_logger

logger = get_logger("netbridge.plugin.twitter")

# Twitter/X API
TWITTER_API = "https://api.x.com"
TWITTER_GRAPHQL = "https://x.com/i/api/graphql"


class TwitterPlugin(BasePlugin):
    """Twitter/X插件

    通过Cookie认证读取推文和用户信息。
    """

    @property
    def name(self) -> str:
        return "twitter"

    @property
    def description(self) -> str:
        return "Twitter/X插件，支持推文读取和搜索"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def tier(self) -> int:
        return 1  # 扩展插件，需要Cookie认证

    @property
    def platform(self) -> str:
        return "twitter"

    def _get_cookies(self) -> Dict[str, str]:
        """获取Twitter Cookie"""
        cookies = self.get_config_value("cookies", {})
        if not cookies:
            import os
            cookie_str = os.environ.get("TWITTER_COOKIES", "")
            if cookie_str:
                cookies = {}
                for item in cookie_str.split(";"):
                    item = item.strip()
                    if "=" in item:
                        k, v = item.split("=", 1)
                        cookies[k.strip()] = v.strip()
        return cookies

    def _get_auth_headers(self) -> Dict[str, str]:
        """获取带认证的请求头"""
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "X-Twitter-Active-User": "yes",
            "X-Twitter-Client-Language": "zh-cn",
            "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
        }

    def _parse_tweet_id(self, url_or_id: str) -> str:
        """解析推文ID"""
        url_or_id = url_or_id.strip()
        patterns = [
            r"twitter\.com/\w+/status/(\d+)",
            r"x\.com/\w+/status/(\d+)",
            r"twitter\.com/\w+/statuses/(\d+)",
            r"x\.com/\w+/statuses/(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)
        return url_or_id

    def search(self, query: str, limit: int = 10) -> NormalizedResult:
        """搜索推文

        通过Twitter搜索API搜索推文。

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
                "未配置Twitter Cookie，请通过 netbridge config 配置 cookies",
            )

        try:
            headers = self._get_auth_headers()
            params = {
                "q": query,
                "count": min(limit, 20),
                "tweet_mode": "extended",
            }
            data = get_json(
                "https://api.twitter.com/2/search/adaptive.json",
                params=params,
                headers=headers,
                cookies=cookies,
                timeout=15,
            )

            results = []
            tweets = data.get("tweets", [])
            for tweet in tweets[:limit]:
                results.append({
                    "title": tweet.get("user", {}).get("screen_name", ""),
                    "url": f"https://twitter.com/{tweet.get('user', {}).get('screen_name', '')}/status/{tweet.get('id_str', '')}",
                    "snippet": tweet.get("full_text", tweet.get("text", ""))[:300],
                    "author": tweet.get("user", {}).get("name", ""),
                    "published_at": tweet.get("created_at", ""),
                    "metadata": {
                        "retweets": tweet.get("retweet_count", 0),
                        "likes": tweet.get("favorite_count", 0),
                        "replies": tweet.get("reply_count", 0),
                    },
                })

            return Normalizer.create_search_result(
                platform=self.platform,
                results=results,
            )

        except (NetworkError, Exception) as e:
            logger.warning(f"Twitter搜索失败: {e}")
            return self._make_error("search", f"搜索失败: {e}")

    def read(self, url_or_id: str) -> NormalizedResult:
        """读取推文

        Args:
            url_or_id: 推文URL或ID

        Returns:
            标准化读取结果
        """
        cookies = self._get_cookies()
        if not cookies:
            return self._make_error(
                "read",
                "未配置Twitter Cookie，请通过 netbridge config 配置 cookies",
            )

        try:
            tweet_id = self._parse_tweet_id(url_or_id)
            headers = self._get_auth_headers()

            # 使用syndication API（不需要完整认证）
            url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{tweet_id}"
            try:
                content = get_text(url, headers=headers, cookies=cookies, timeout=15)
            except Exception:
                # 尝试推文嵌入API
                url = f"https://publish.twitter.com/oembed?url=https://twitter.com/x/status/{tweet_id}"
                data = get_json(url, headers=headers, timeout=15)

                return Normalizer.create_read_result(
                    platform=self.platform,
                    title=data.get("author_name", ""),
                    content=data.get("html", "").replace("<br>", "\n"),
                    url=url_or_id,
                    author=data.get("author_name", ""),
                )

            return Normalizer.create_read_result(
                platform=self.platform,
                title=f"Tweet {tweet_id}",
                content=content[:5000],
                url=f"https://twitter.com/i/status/{tweet_id}",
            )

        except (NetworkError, Exception) as e:
            logger.warning(f"Twitter读取失败: {e}")
            return self._make_error("read", f"读取失败: {e}")

    def check_health(self) -> Dict[str, Any]:
        """健康检查"""
        cookies = self._get_cookies()
        has_cookies = bool(cookies)
        return {
            "healthy": has_cookies,
            "message": "Twitter Cookie 已配置" if has_cookies else "未配置Twitter Cookie",
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
                "description": "Twitter Cookie字典（auth_token, ct0等）",
                "default": {},
            },
        }
