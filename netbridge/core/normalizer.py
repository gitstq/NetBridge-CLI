"""统一输出格式化模块 - 将所有平台返回标准化JSON结构

确保不同平台的数据输出格式一致，方便AI Agent统一处理。
"""

import json
from datetime import datetime, timezone
from typing import Any, Optional, Dict, List, Union


class NormalizedResult:
    """标准化结果对象

    所有插件返回的数据都应通过此类包装，
    确保输出格式统一。
    """

    def __init__(
        self,
        platform: str,
        action: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        cached: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """初始化标准化结果

        Args:
            platform: 平台名称（如 web, github, twitter）
            action: 操作类型（search 或 read）
            data: 数据内容（单条为dict，多条为list）
            cached: 是否来自缓存
            metadata: 额外元数据
        """
        self.platform = platform
        self.action = action
        self.data = data
        self.cached = cached
        self.metadata = metadata or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "platform": self.platform,
            "action": self.action,
            "data": self.data,
            "cached": self.cached,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    def to_json(self, indent: int = 2, ensure_ascii: bool = False) -> str:
        """转换为JSON字符串

        Args:
            indent: 缩进空格数
            ensure_ascii: 是否转义非ASCII字符

        Returns:
            JSON格式字符串
        """
        return json.dumps(
            self.to_dict(),
            indent=indent,
            ensure_ascii=ensure_ascii,
            default=str,
        )

    def __repr__(self) -> str:
        return f"NormalizedResult(platform={self.platform!r}, action={self.action!r}, items={len(self.data) if isinstance(self.data, list) else 1})"


class Normalizer:
    """输出格式化器

    提供便捷方法创建标准化结果。
    """

    @staticmethod
    def create_read_result(
        platform: str,
        title: str,
        content: str,
        url: str = "",
        author: str = "",
        published_at: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        cached: bool = False,
    ) -> NormalizedResult:
        """创建单条读取结果

        Args:
            platform: 平台名称
            title: 标题
            content: 内容
            url: 原始URL
            author: 作者
            published_at: 发布时间
            metadata: 额外元数据
            cached: 是否来自缓存

        Returns:
            标准化结果对象
        """
        data: Dict[str, Any] = {
            "title": title,
            "content": content,
            "url": url,
            "author": author,
            "published_at": published_at,
        }
        if metadata:
            data["metadata"] = metadata

        return NormalizedResult(
            platform=platform,
            action="read",
            data=data,
            cached=cached,
        )

    @staticmethod
    def create_search_result(
        platform: str,
        results: List[Dict[str, Any]],
        cached: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> NormalizedResult:
        """创建搜索结果

        Args:
            platform: 平台名称
            results: 搜索结果列表，每项应包含 title, url, snippet 等字段
            cached: 是否来自缓存
            metadata: 额外元数据

        Returns:
            标准化结果对象
        """
        # 标准化每个搜索结果项
        normalized_items = []
        for item in results:
            normalized_item: Dict[str, Any] = {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("snippet", item.get("content", "")),
                "author": item.get("author", ""),
                "published_at": item.get("published_at", ""),
            }
            # 保留额外的元数据
            extra_keys = set(item.keys()) - {
                "title", "url", "snippet", "content", "author", "published_at"
            }
            if extra_keys:
                normalized_item["metadata"] = {
                    k: item[k] for k in extra_keys
                }
            normalized_items.append(normalized_item)

        return NormalizedResult(
            platform=platform,
            action="search",
            data=normalized_items,
            cached=cached,
            metadata=metadata,
        )

    @staticmethod
    def create_error_result(
        platform: str,
        action: str,
        error: str,
        error_code: Optional[str] = None,
    ) -> NormalizedResult:
        """创建错误结果

        Args:
            platform: 平台名称
            action: 操作类型
            error: 错误信息
            error_code: 错误代码

        Returns:
            标准化错误结果
        """
        data: Dict[str, Any] = {
            "error": True,
            "error_message": error,
        }
        if error_code:
            data["error_code"] = error_code

        return NormalizedResult(
            platform=platform,
            action=action,
            data=data,
            cached=False,
        )

    @staticmethod
    def create_health_result(
        platform: str,
        healthy: bool,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
    ) -> NormalizedResult:
        """创建健康检查结果

        Args:
            platform: 平台名称
            healthy: 是否健康
            message: 状态信息
            details: 详细信息

        Returns:
            标准化健康检查结果
        """
        data: Dict[str, Any] = {
            "healthy": healthy,
            "message": message,
        }
        if details:
            data["details"] = details

        return NormalizedResult(
            platform=platform,
            action="check",
            data=data,
            cached=False,
        )

    @staticmethod
    def format_output(result: NormalizedResult, format_type: str = "json") -> str:
        """格式化输出

        Args:
            result: 标准化结果
            format_type: 输出格式 (json/text)

        Returns:
            格式化后的字符串
        """
        if format_type == "text":
            return Normalizer._format_text(result)
        return result.to_json()

    @staticmethod
    def _format_text(result: NormalizedResult) -> str:
        """文本格式输出"""
        lines = []
        lines.append(f"[{result.platform}] {result.action.upper()}")
        lines.append(f"时间: {result.timestamp}")
        if result.cached:
            lines.append("(来自缓存)")
        lines.append("-" * 50)

        if isinstance(result.data, list):
            for i, item in enumerate(result.data, 1):
                lines.append(f"\n--- 结果 {i} ---")
                if "title" in item:
                    lines.append(f"标题: {item['title']}")
                if "url" in item:
                    lines.append(f"URL: {item['url']}")
                if "snippet" in item:
                    snippet = item["snippet"][:200]
                    lines.append(f"摘要: {snippet}")
                if "author" in item and item["author"]:
                    lines.append(f"作者: {item['author']}")
                if "published_at" in item and item["published_at"]:
                    lines.append(f"发布: {item['published_at']}")
        elif isinstance(result.data, dict):
            if result.data.get("error"):
                lines.append(f"错误: {result.data.get('error_message', '未知错误')}")
            else:
                if "title" in result.data:
                    lines.append(f"标题: {result.data['title']}")
                if "url" in result.data:
                    lines.append(f"URL: {result.data['url']}")
                if "author" in result.data and result.data["author"]:
                    lines.append(f"作者: {result.data['author']}")
                if "published_at" in result.data and result.data["published_at"]:
                    lines.append(f"发布: {result.data['published_at']}")
                if "content" in result.data:
                    content = result.data["content"][:500]
                    lines.append(f"\n内容:\n{content}")
                    if len(result.data["content"]) > 500:
                        lines.append(f"... (共{len(result.data['content'])}字符)")

        return "\n".join(lines)
