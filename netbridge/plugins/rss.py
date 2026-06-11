"""RSS插件 - 使用feedparser解析RSS/Atom订阅源

可选依赖：feedparser
"""

from typing import Any, Dict, List, Optional

from .base import BasePlugin
from ..core.normalizer import NormalizedResult, Normalizer
from ..utils.logger import get_logger

logger = get_logger("netbridge.plugin.rss")


class RSSPlugin(BasePlugin):
    """RSS/Atom订阅源插件

    使用feedparser解析RSS/Atom订阅源，
    支持搜索和读取订阅内容。
    """

    @property
    def name(self) -> str:
        return "rss"

    @property
    def description(self) -> str:
        return "RSS/Atom订阅源解析插件"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def tier(self) -> int:
        return 1  # 扩展插件，可选依赖

    @property
    def platform(self) -> str:
        return "rss"

    def _get_feedparser(self):
        """动态导入feedparser"""
        try:
            import feedparser
            return feedparser
        except ImportError:
            raise RuntimeError(
                "需要安装feedparser依赖，请运行: pip install feedparser"
            )

    def search(self, query: str, limit: int = 10) -> NormalizedResult:
        """搜索RSS内容

        从配置的RSS源中搜索匹配的文章标题。

        Args:
            query: 搜索关键词
            limit: 结果数量限制

        Returns:
            标准化搜索结果
        """
        try:
            feedparser = self._get_feedparser()

            # 从配置获取RSS源列表
            feeds = self.get_config_value("feeds", [])
            if not feeds:
                return self._make_error(
                    "search",
                    "未配置RSS源，请通过 netbridge config 配置 feeds 列表",
                )

            results = []
            query_lower = query.lower()

            for feed_url in feeds:
                try:
                    feed = feedparser.parse(feed_url)
                    for entry in feed.entries[:limit]:
                        title = entry.get("title", "")
                        if query_lower in title.lower():
                            results.append({
                                "title": title,
                                "url": entry.get("link", ""),
                                "snippet": entry.get("summary", "")[:300],
                                "author": entry.get("author", feed.feed.get("title", "")),
                                "published_at": entry.get("published", entry.get("updated", "")),
                            })
                except Exception as e:
                    logger.warning(f"解析RSS源失败 {feed_url}: {e}")
                    continue

                if len(results) >= limit:
                    break

            if not results:
                results.append({
                    "title": "未找到结果",
                    "url": "",
                    "snippet": f"在已配置的RSS源中未找到与 '{query}' 相关的内容",
                })

            return Normalizer.create_search_result(
                platform=self.platform,
                results=results[:limit],
            )

        except RuntimeError as e:
            return self._make_error("search", str(e))
        except Exception as e:
            logger.warning(f"RSS搜索失败: {e}")
            return self._make_error("search", f"搜索失败: {e}")

    def read(self, url_or_id: str) -> NormalizedResult:
        """读取RSS源或文章

        Args:
            url_or_id: RSS源URL或文章URL

        Returns:
            标准化读取结果
        """
        try:
            feedparser = self._get_feedparser()

            feed = feedparser.parse(url_or_id)

            # 如果是RSS源，返回所有条目
            if feed.entries:
                content_parts = [f"# {feed.feed.get('title', url_or_id)}", ""]
                content_parts.append(f"描述: {feed.feed.get('description', '')}")
                content_parts.append(f"链接: {feed.feed.get('link', '')}")
                content_parts.append("")

                for i, entry in enumerate(feed.entries[:20], 1):
                    content_parts.append(f"## {i}. {entry.get('title', '无标题')}")
                    content_parts.append(f"- 链接: {entry.get('link', '')}")
                    content_parts.append(f"- 作者: {entry.get('author', '未知')}")
                    content_parts.append(f"- 时间: {entry.get('published', entry.get('updated', ''))}")
                    summary = entry.get("summary", "")
                    if summary:
                        # 清理HTML标签
                        import re
                        clean_summary = re.sub(r"<[^>]+>", "", summary)
                        content_parts.append(f"- 摘要: {clean_summary[:200]}")
                    content_parts.append("")

                return Normalizer.create_read_result(
                    platform=self.platform,
                    title=feed.feed.get("title", url_or_id),
                    content="\n".join(content_parts),
                    url=url_or_id,
                    author=feed.feed.get("author", ""),
                )
            else:
                return self._make_error(
                    "read",
                    f"无法解析RSS源或未找到条目: {url_or_id}",
                )

        except RuntimeError as e:
            return self._make_error("read", str(e))
        except Exception as e:
            logger.warning(f"RSS读取失败: {e}")
            return self._make_error("read", f"读取失败: {e}")

    def check_health(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            import feedparser
            feeds = self.get_config_value("feeds", [])
            return {
                "healthy": True,
                "message": f"feedparser 已安装，已配置 {len(feeds)} 个RSS源",
                "details": {
                    "version": self.version,
                    "tier": self.tier,
                    "feeds_count": len(feeds),
                },
            }
        except ImportError:
            return {
                "healthy": False,
                "message": "feedparser 未安装，请运行: pip install feedparser",
                "details": {"version": self.version, "tier": self.tier},
            }

    def get_dependencies(self) -> List[str]:
        return ["feedparser"]

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "feeds": {
                "type": "list",
                "description": "RSS源URL列表",
                "default": [],
            },
        }
