"""LinkedIn插件 - 通过Jina Reader读取LinkedIn内容

利用Jina Reader API读取LinkedIn公开页面，
无需额外认证。
"""

import re
from typing import Any, Dict, List, Optional

from .base import BasePlugin
from ..core.normalizer import NormalizedResult, Normalizer
from ..utils.network import get_text, NetworkError
from ..utils.logger import get_logger

logger = get_logger("netbridge.plugin.linkedin")

# Jina Reader API
JINA_READER_URL = "https://r.jina.ai"


class LinkedInPlugin(BasePlugin):
    """LinkedIn插件

    通过Jina Reader API读取LinkedIn公开页面内容。
    """

    @property
    def name(self) -> str:
        return "linkedin"

    @property
    def description(self) -> str:
        return "LinkedIn插件，通过Jina Reader读取公开页面"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def tier(self) -> int:
        return 0  # 核心插件，零依赖

    @property
    def platform(self) -> str:
        return "linkedin"

    def search(self, query: str, limit: int = 10) -> NormalizedResult:
        """搜索LinkedIn内容

        通过Jina Reader搜索LinkedIn公开内容。

        Args:
            query: 搜索关键词
            limit: 结果数量限制

        Returns:
            标准化搜索结果
        """
        try:
            # 使用Google搜索LinkedIn内容
            search_url = f"https://www.google.com/search?q=site:linkedin.com+{query}"
            headers = {
                "Accept": "text/markdown",
                "X-Return-Format": "markdown",
            }
            content = get_text(
                f"{JINA_READER_URL}/{search_url}",
                headers=headers,
                timeout=20,
            )

            # 解析搜索结果
            results = []
            lines = content.split("\n")
            current_title = ""
            current_url = ""
            current_snippet = ""

            for line in lines:
                # 查找LinkedIn链接
                linkedin_match = re.search(r"\[.*?\]\((https?://(?:www\.)?linkedin\.com/[^\)]+)\)", line)
                if linkedin_match:
                    if current_title:
                        results.append({
                            "title": current_title,
                            "url": current_url,
                            "snippet": current_snippet[:300],
                        })
                    current_url = linkedin_match.group(1)
                    current_title = line.strip()
                    current_snippet = ""
                elif current_url:
                    current_snippet += line + " "

                if len(results) >= limit:
                    break

            if not results:
                results.append({
                    "title": "未找到结果",
                    "url": "",
                    "snippet": f"没有找到与 '{query}' 相关的LinkedIn内容",
                })

            return Normalizer.create_search_result(
                platform=self.platform,
                results=results[:limit],
            )

        except (NetworkError, Exception) as e:
            logger.warning(f"LinkedIn搜索失败: {e}")
            return self._make_error("search", f"搜索失败: {e}")

    def read(self, url_or_id: str) -> NormalizedResult:
        """读取LinkedIn页面

        Args:
            url_or_id: LinkedIn URL

        Returns:
            标准化读取结果
        """
        url = url_or_id.strip()

        # 确保URL完整
        if not url.startswith(("http://", "https://")):
            url = f"https://www.linkedin.com/{url}"

        try:
            headers = {
                "Accept": "text/markdown",
                "X-Return-Format": "markdown",
            }
            content = get_text(
                f"{JINA_READER_URL}/{url}",
                headers=headers,
                timeout=20,
            )

            # 提取标题
            title = ""
            lines = content.strip().split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith("#"):
                    title = line.lstrip("#").strip()
                    break

            if not title:
                title = url

            # 提取作者
            author = ""
            author_match = re.search(r"LinkedIn(?:\.com)?/in/([a-zA-Z0-9-]+)", url)
            if author_match:
                author = author_match.group(1)

            return Normalizer.create_read_result(
                platform=self.platform,
                title=title,
                content=content.strip(),
                url=url,
                author=author,
            )

        except (NetworkError, Exception) as e:
            logger.warning(f"LinkedIn读取失败: {e}")
            return self._make_error("read", f"读取失败: {e}")

    def check_health(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            content = get_text(
                f"{JINA_READER_URL}/https://www.linkedin.com/company/linkedin",
                headers={"Accept": "text/markdown"},
                timeout=15,
            )
            healthy = len(content) > 100
            return {
                "healthy": healthy,
                "message": "LinkedIn (via Jina Reader) 可用" if healthy else "LinkedIn 读取受限",
                "details": {
                    "version": self.version,
                    "tier": self.tier,
                    "via": "jina_reader",
                },
            }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"LinkedIn 不可用: {e}",
                "details": {"version": self.version, "tier": self.tier},
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
