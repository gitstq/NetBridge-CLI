"""网页读取插件 - 使用urllib通过r.jina.ai读取网页内容，零依赖

通过Jina Reader API将网页转换为Markdown格式，
无需额外依赖，直接使用标准库urllib。
"""

import json
import re
from typing import Any, Dict, List, Optional

from .base import BasePlugin
from ..core.normalizer import NormalizedResult, Normalizer
from ..utils.network import get_text, get_json, NetworkError
from ..utils.logger import get_logger

logger = get_logger("netbridge.plugin.web")

# Jina Reader API地址
JINA_READER_URL = "https://r.jina.ai"


class WebPlugin(BasePlugin):
    """网页读取插件

    通过r.jina.ai将网页转换为Markdown格式，
    支持搜索和读取网页内容。
    """

    @property
    def name(self) -> str:
        return "web"

    @property
    def description(self) -> str:
        return "网页读取插件，通过Jina Reader将网页转换为Markdown格式"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def tier(self) -> int:
        return 0  # 核心插件，零依赖

    @property
    def platform(self) -> str:
        return "web"

    def search(self, query: str, limit: int = 10) -> NormalizedResult:
        """搜索网页内容

        使用DuckDuckGo的即时回答API进行简单搜索。

        Args:
            query: 搜索关键词
            limit: 结果数量限制

        Returns:
            标准化搜索结果
        """
        try:
            # 使用DuckDuckGo即时回答API
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1",
            }
            data = get_json(url, params=params, timeout=10)

            results = []

            # 从Abstract获取主要结果
            abstract = data.get("Abstract", "")
            abstract_url = data.get("AbstractURL", "")
            abstract_source = data.get("AbstractSource", "")
            if abstract:
                results.append({
                    "title": abstract_source or query,
                    "url": abstract_url,
                    "snippet": abstract[:500],
                    "author": abstract_source,
                })

            # 从RelatedTopics获取相关结果
            related = data.get("RelatedTopics", [])
            for topic in related[:limit - 1]:
                if isinstance(topic, dict) and "Text" in topic:
                    results.append({
                        "title": topic.get("Text", "")[:100],
                        "url": topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", "")[:300],
                    })

            if not results:
                return Normalizer.create_search_result(
                    platform=self.platform,
                    results=[{
                        "title": "未找到结果",
                        "url": "",
                        "snippet": f"没有找到与 '{query}' 相关的网页结果",
                    }],
                )

            return Normalizer.create_search_result(
                platform=self.platform,
                results=results[:limit],
            )

        except (NetworkError, Exception) as e:
            logger.warning(f"网页搜索失败: {e}")
            return self._make_error("search", f"搜索失败: {e}")

    def read(self, url_or_id: str) -> NormalizedResult:
        """读取网页内容

        通过Jina Reader API将网页转换为Markdown。

        Args:
            url_or_id: 网页URL

        Returns:
            标准化读取结果
        """
        # 确保URL有协议前缀
        url = url_or_id
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            # 通过Jina Reader读取
            reader_url = f"{JINA_READER_URL}/{url}"
            headers = {
                "Accept": "text/markdown",
                "X-Return-Format": "markdown",
            }
            content = get_text(reader_url, headers=headers, timeout=20)

            # 提取标题（Markdown第一行通常是标题）
            title = ""
            lines = content.strip().split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith("#"):
                    title = line.lstrip("#").strip()
                    break

            if not title:
                title = url

            # 清理内容
            content = content.strip()

            return Normalizer.create_read_result(
                platform=self.platform,
                title=title,
                content=content,
                url=url,
            )

        except (NetworkError, Exception) as e:
            logger.warning(f"网页读取失败: {e}")
            return self._make_error("read", f"读取失败: {e}")

    def check_health(self) -> Dict[str, Any]:
        """健康检查 - 测试Jina Reader连通性"""
        try:
            # 简单测试连通性
            content = get_text(
                f"{JINA_READER_URL}/https://example.com",
                headers={"Accept": "text/markdown"},
                timeout=10,
            )
            healthy = len(content) > 0
            return {
                "healthy": healthy,
                "message": "Jina Reader 连通" if healthy else "Jina Reader 无响应",
                "details": {
                    "version": self.version,
                    "tier": self.tier,
                    "jina_reader": "accessible" if healthy else "unreachable",
                },
            }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Jina Reader 不可用: {e}",
                "details": {
                    "version": self.version,
                    "tier": self.tier,
                },
            }

    def get_dependencies(self) -> List[str]:
        return []

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "jina_reader_url": {
                "type": "string",
                "description": "Jina Reader API地址",
                "default": JINA_READER_URL,
            },
        }
