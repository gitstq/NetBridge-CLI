"""核心引擎模块 - 插件发现、加载、路由、缓存管理

NetBridge的核心，负责管理所有插件的生命周期，
包括发现、加载、路由请求、缓存管理等。
"""

import importlib
import os
import sys
from typing import Any, Dict, List, Optional

from ..plugins.base import BasePlugin
from ..core.cache import FileCache
from ..core.config import ConfigManager
from ..core.normalizer import NormalizedResult, Normalizer
from ..utils.logger import (
    get_logger, info, warning, error, debug,
    success, fail, colored_text, Colors,
)

logger = get_logger("netbridge.engine")

# 内置插件列表（按tier排序）
BUILTIN_PLUGINS = [
    "web",
    "github",
    "rss",
    "youtube",
    "twitter",
    "reddit",
    "bilibili",
    "xiaohongshu",
    "v2ex",
    "xueqiu",
    "linkedin",
    "xiaoyuzhou",
]


class Engine:
    """NetBridge核心引擎

    负责插件的发现、加载、路由和缓存管理。
    """

    def __init__(self, config: Optional[ConfigManager] = None):
        """初始化引擎

        Args:
            config: 配置管理器，None则自动创建
        """
        self.config = config or ConfigManager()
        self._plugins: Dict[str, BasePlugin] = {}
        self._cache = FileCache(
            cache_dir=self.config.get_cache_dir(),
            ttl=self.config.get_cache_ttl(),
            max_size_mb=self.config.get_cache_max_size(),
        )
        self._loaded = False

    @property
    def cache(self) -> FileCache:
        """获取缓存实例"""
        return self._cache

    def discover_plugins(self) -> List[str]:
        """发现所有可用插件

        Returns:
            可用插件名称列表
        """
        available = []
        plugins_dir = os.path.join(os.path.dirname(__file__), "..", "plugins")

        for filename in os.listdir(plugins_dir):
            if filename.endswith(".py") and filename not in ("__init__.py", "base.py"):
                plugin_name = filename[:-3]  # 去掉.py后缀
                available.append(plugin_name)

        return sorted(available)

    def load_plugins(self) -> int:
        """加载所有插件

        Returns:
            成功加载的插件数量
        """
        if self._loaded:
            return len(self._plugins)

        plugin_names = self.discover_plugins()
        loaded_count = 0

        for name in plugin_names:
            try:
                plugin = self._load_plugin(name)
                if plugin:
                    self._plugins[name] = plugin
                    loaded_count += 1
                    tier_label = {0: "核心", 1: "扩展", 2: "实验"}.get(plugin.tier, "未知")
                    debug(f"插件加载成功: {name} (tier={tier_label})")
            except Exception as e:
                warning(f"插件加载失败: {name} - {e}")

        self._loaded = True
        info(f"已加载 {loaded_count}/{len(plugin_names)} 个插件")
        return loaded_count

    def _load_plugin(self, name: str) -> Optional[BasePlugin]:
        """加载单个插件

        Args:
            name: 插件名称

        Returns:
            插件实例，加载失败返回None
        """
        try:
            module = importlib.import_module(f"netbridge.plugins.{name}")
            # 查找模块中的插件类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BasePlugin)
                    and attr is not BasePlugin
                ):
                    # 获取插件配置
                    plugin_config = self.config.get_plugin_config(name)
                    return attr(config=plugin_config)
        except ImportError as e:
            debug(f"插件模块导入失败: {name} - {e}")
        except Exception as e:
            warning(f"插件实例化失败: {name} - {e}")
        return None

    def get_plugin(self, platform: str) -> Optional[BasePlugin]:
        """获取指定平台的插件

        Args:
            platform: 平台名称

        Returns:
            插件实例，不存在返回None
        """
        if not self._loaded:
            self.load_plugins()

        # 支持别名
        aliases = {
            "gh": "github",
            "yt": "youtube",
            "x": "twitter",
            "b": "bilibili",
            "xhs": "xiaohongshu",
            "podcast": "xiaoyuzhou",
            "webpage": "web",
        }
        platform = aliases.get(platform.lower(), platform.lower())
        return self._plugins.get(platform)

    def list_plugins(self) -> List[Dict[str, Any]]:
        """列出所有已加载的插件信息

        Returns:
            插件信息列表
        """
        if not self._loaded:
            self.load_plugins()

        result = []
        for name, plugin in sorted(self._plugins.items()):
            health = plugin.check_health()
            result.append({
                "name": plugin.name,
                "description": plugin.description,
                "version": plugin.version,
                "tier": plugin.tier,
                "platform": plugin.platform,
                "healthy": health.get("healthy", False),
                "message": health.get("message", ""),
            })
        return result

    def search(
        self,
        platform: str,
        query: str,
        limit: int = 10,
        use_cache: bool = True,
    ) -> NormalizedResult:
        """搜索内容

        Args:
            platform: 平台名称
            query: 搜索关键词
            limit: 结果数量限制
            use_cache: 是否使用缓存

        Returns:
            标准化搜索结果
        """
        plugin = self.get_plugin(platform)
        if not plugin:
            return Normalizer.create_error_result(
                platform=platform,
                action="search",
                error=f"未找到平台 '{platform}' 的插件",
                error_code="PLUGIN_NOT_FOUND",
            )

        # 检查缓存
        cache_key = f"search:{query}:limit={limit}"
        if use_cache and self.config.is_cache_enabled():
            cached = self._cache.get(platform, cache_key)
            if cached is not None:
                debug(f"搜索缓存命中: {platform}")
                return Normalizer.create_search_result(
                    platform=platform,
                    results=cached,
                    cached=True,
                )

        # 执行搜索
        try:
            result = plugin.search(query, limit=limit)
            # 缓存结果
            if use_cache and self.config.is_cache_enabled():
                self._cache.set(platform, cache_key, result.data if isinstance(result.data, list) else [result.data])
            return result
        except Exception as e:
            error(f"搜索失败 [{platform}]: {e}")
            return Normalizer.create_error_result(
                platform=platform,
                action="search",
                error=str(e),
                error_code="SEARCH_ERROR",
            )

    def read(
        self,
        platform: str,
        url_or_id: str,
        use_cache: bool = True,
    ) -> NormalizedResult:
        """读取内容

        Args:
            platform: 平台名称
            url_or_id: URL或ID
            use_cache: 是否使用缓存

        Returns:
            标准化读取结果
        """
        plugin = self.get_plugin(platform)
        if not plugin:
            return Normalizer.create_error_result(
                platform=platform,
                action="read",
                error=f"未找到平台 '{platform}' 的插件",
                error_code="PLUGIN_NOT_FOUND",
            )

        # 检查缓存
        cache_key = f"read:{url_or_id}"
        if use_cache and self.config.is_cache_enabled():
            cached = self._cache.get(platform, cache_key)
            if cached is not None:
                debug(f"读取缓存命中: {platform}")
                return Normalizer.create_read_result(
                    platform=platform,
                    **cached,
                    cached=True,
                )

        # 执行读取
        try:
            result = plugin.read(url_or_id)
            # 缓存结果
            if use_cache and self.config.is_cache_enabled() and isinstance(result.data, dict):
                self._cache.set(platform, cache_key, result.data)
            return result
        except Exception as e:
            error(f"读取失败 [{platform}]: {e}")
            return Normalizer.create_error_result(
                platform=platform,
                action="read",
                error=str(e),
                error_code="READ_ERROR",
            )

    def check_all_health(self) -> List[Dict[str, Any]]:
        """检查所有插件的健康状态

        Returns:
            健康状态列表
        """
        if not self._loaded:
            self.load_plugins()

        results = []
        for name, plugin in sorted(self._plugins.items()):
            health = plugin.check_health()
            results.append({
                "name": name,
                "healthy": health.get("healthy", False),
                "message": health.get("message", ""),
                "details": health.get("details", {}),
            })
        return results

    def install_plugin_deps(self, plugin_name: Optional[str] = None) -> Dict[str, Any]:
        """安装插件依赖

        Args:
            plugin_name: 插件名称，None则安装所有

        Returns:
            安装结果
        """
        if not self._loaded:
            self.load_plugins()

        results = {}
        plugins_to_install = (
            {plugin_name: self._plugins[plugin_name]}
            if plugin_name and plugin_name in self._plugins
            else self._plugins
        )

        for name, plugin in plugins_to_install.items():
            try:
                install_result = plugin.install_deps()
                results[name] = {
                    "success": True,
                    "message": install_result,
                }
                success(f"{name}: {install_result}")
            except Exception as e:
                results[name] = {
                    "success": False,
                    "message": str(e),
                }
                fail(f"{name}: {e}")

        return results

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return self._cache.get_stats()

    def clear_cache(self, platform: Optional[str] = None) -> int:
        """清空缓存

        Args:
            platform: 指定平台，None则清空所有

        Returns:
            删除的条目数
        """
        count = self._cache.clear(platform)
        return count
