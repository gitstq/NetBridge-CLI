"""配置管理模块 - YAML/JSON配置文件的读写和管理

支持多层级配置（全局配置 + 插件级配置），
配置文件存储在 ~/.netbridge/ 目录下。
"""

import json
import os
import copy
from typing import Any, Optional, Dict

from ..utils.logger import get_logger, warning, info

logger = get_logger("netbridge.config")

# 默认配置目录
DEFAULT_CONFIG_DIR = os.path.expanduser("~/.netbridge")

# 默认配置文件名
CONFIG_FILENAME = "config.json"

# 全局默认配置
DEFAULT_CONFIG: Dict[str, Any] = {
    "version": "0.1.0",
    "cache": {
        "enabled": True,
        "ttl": 3600,           # 默认缓存1小时
        "max_size_mb": 100,    # 最大缓存100MB
        "dir": "~/.netbridge/cache",
    },
    "mcp": {
        "host": "127.0.0.1",
        "port": 8765,
        "transport": "stdio",  # stdio 或 tcp
    },
    "network": {
        "timeout": 15,
        "retries": 2,
        "proxy": "",           # 代理地址，留空则不使用
    },
    "plugins": {},
}


class ConfigManager:
    """配置管理器

    管理全局配置和各插件的配置，支持读写JSON格式配置文件。
    """

    def __init__(self, config_dir: Optional[str] = None):
        """初始化配置管理器

        Args:
            config_dir: 配置目录路径，默认为 ~/.netbridge
        """
        self.config_dir = config_dir or DEFAULT_CONFIG_DIR
        self.config_file = os.path.join(self.config_dir, CONFIG_FILENAME)
        self._config: Dict[str, Any] = copy.deepcopy(DEFAULT_CONFIG)
        self._ensure_config_dir()
        self._load()

    def _ensure_config_dir(self) -> None:
        """确保配置目录存在"""
        os.makedirs(self.config_dir, exist_ok=True)

    def _load(self) -> None:
        """从配置文件加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    file_config = json.load(f)
                self._config = self._deep_merge(self._config, file_config)
                logger.debug(f"配置已加载: {self.config_file}")
            except (json.JSONDecodeError, IOError) as e:
                warning(f"配置文件加载失败，使用默认配置: {e}")
        else:
            # 首次运行，创建默认配置
            self.save()
            info(f"已创建默认配置文件: {self.config_file}")

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并两个字典"""
        result = copy.deepcopy(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = copy.deepcopy(value)
        return result

    def save(self) -> None:
        """保存配置到文件"""
        self._ensure_config_dir()
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            logger.debug(f"配置已保存: {self.config_file}")
        except IOError as e:
            warning(f"配置文件保存失败: {e}")

    @property
    def config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return copy.deepcopy(self._config)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值（支持点号分隔的路径）

        Args:
            key: 配置键，支持 "cache.ttl" 格式
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """设置配置值（支持点号分隔的路径）

        Args:
            key: 配置键，支持 "cache.ttl" 格式
            value: 配置值
        """
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """获取指定插件的配置

        Args:
            plugin_name: 插件名称

        Returns:
            插件配置字典
        """
        plugins_config = self._config.get("plugins", {})
        return plugins_config.get(plugin_name, {})

    def set_plugin_config(self, plugin_name: str, config: Dict[str, Any]) -> None:
        """设置指定插件的配置

        Args:
            plugin_name: 插件名称
            config: 插件配置字典
        """
        if "plugins" not in self._config:
            self._config["plugins"] = {}
        self._config["plugins"][plugin_name] = config

    def get_cache_dir(self) -> str:
        """获取缓存目录路径"""
        cache_dir = self.get("cache.dir", "~/.netbridge/cache")
        return os.path.expanduser(cache_dir)

    def is_cache_enabled(self) -> bool:
        """是否启用缓存"""
        return self.get("cache.enabled", True)

    def get_cache_ttl(self) -> int:
        """获取缓存TTL（秒）"""
        return self.get("cache.ttl", 3600)

    def get_cache_max_size(self) -> int:
        """获取最大缓存大小（MB）"""
        return self.get("cache.max_size_mb", 100)

    def get_network_timeout(self) -> int:
        """获取网络请求超时时间"""
        return self.get("network.timeout", 15)

    def get_network_retries(self) -> int:
        """获取网络请求重试次数"""
        return self.get("network.retries", 2)

    def get_proxy(self) -> str:
        """获取代理设置"""
        return self.get("network.proxy", "")

    def reset(self) -> None:
        """重置为默认配置"""
        self._config = copy.deepcopy(DEFAULT_CONFIG)
        self.save()
        info("配置已重置为默认值")

    def show(self) -> str:
        """以JSON格式显示当前配置"""
        return json.dumps(self._config, ensure_ascii=False, indent=2)
