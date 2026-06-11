"""基于文件的LRU缓存模块 - JSON存储，支持TTL过期

缓存按平台分目录存储在 ~/.netbridge/cache/ 下，
采用LRU淘汰策略和TTL过期机制。
"""

import json
import os
import hashlib
import time
from typing import Any, Optional, Dict
from pathlib import Path

from ..utils.logger import get_logger, debug, warning

logger = get_logger("netbridge.cache")


class CacheEntry:
    """缓存条目"""

    def __init__(self, data: Any, ttl: int = 3600):
        self.data = data
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl
        self.accessed_at = self.created_at

    @property
    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() > self.expires_at

    def touch(self) -> None:
        """更新访问时间"""
        self.accessed_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "data": self.data,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "accessed_at": self.accessed_at,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CacheEntry":
        """从字典反序列化"""
        entry = cls.__new__(cls)
        entry.data = d["data"]
        entry.created_at = d["created_at"]
        entry.expires_at = d["expires_at"]
        entry.accessed_at = d.get("accessed_at", d["created_at"])
        return entry


class FileCache:
    """基于文件的LRU缓存

    特性：
    - 按平台分目录存储
    - JSON格式存储
    - LRU淘汰策略
    - TTL过期机制
    - 最大缓存大小限制
    """

    def __init__(
        self,
        cache_dir: str = "~/.netbridge/cache",
        ttl: int = 3600,
        max_size_mb: int = 100,
    ):
        """初始化缓存

        Args:
            cache_dir: 缓存根目录
            ttl: 默认TTL（秒）
            max_size_mb: 最大缓存大小（MB）
        """
        self.cache_dir = os.path.expanduser(cache_dir)
        self.default_ttl = ttl
        self.max_size_bytes = max_size_mb * 1024 * 1024
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_platform_dir(self, platform: str) -> str:
        """获取平台缓存目录"""
        platform_dir = os.path.join(self.cache_dir, platform)
        os.makedirs(platform_dir, exist_ok=True)
        return platform_dir

    def _make_key(self, key: str) -> str:
        """生成安全的缓存文件名"""
        # 使用MD5哈希生成文件名，避免路径问题
        hash_hex = hashlib.md5(key.encode("utf-8")).hexdigest()
        return f"{hash_hex}.json"

    def _get_cache_path(self, platform: str, key: str) -> str:
        """获取缓存文件完整路径"""
        return os.path.join(self._get_platform_dir(platform), self._make_key(key))

    def get(self, platform: str, key: str) -> Optional[Any]:
        """从缓存获取数据

        Args:
            platform: 平台名称
            key: 缓存键

        Returns:
            缓存数据，如果不存在或已过期则返回None
        """
        cache_path = self._get_cache_path(platform, key)

        if not os.path.exists(cache_path):
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                entry_data = json.load(f)

            entry = CacheEntry.from_dict(entry_data)

            if entry.is_expired:
                # 过期则删除
                os.remove(cache_path)
                debug(f"缓存过期已删除: {platform}/{key[:30]}...")
                return None

            # 更新访问时间
            entry.touch()
            self._save_entry(cache_path, entry)
            debug(f"缓存命中: {platform}/{key[:30]}...")
            return entry.data

        except (json.JSONDecodeError, IOError, KeyError) as e:
            warning(f"缓存读取失败: {e}")
            # 损坏的缓存文件，删除
            try:
                os.remove(cache_path)
            except OSError:
                pass
            return None

    def set(self, platform: str, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """写入缓存

        Args:
            platform: 平台名称
            key: 缓存键
            data: 缓存数据
            ttl: TTL（秒），None则使用默认值
        """
        ttl = ttl or self.default_ttl
        entry = CacheEntry(data, ttl)
        cache_path = self._get_cache_path(platform, key)
        self._save_entry(cache_path, entry)

        # 检查缓存大小，必要时淘汰
        self._evict_if_needed()
        debug(f"缓存写入: {platform}/{key[:30]}... (TTL={ttl}s)")

    def _save_entry(self, cache_path: str, entry: CacheEntry) -> None:
        """保存缓存条目到文件"""
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(entry.to_dict(), f, ensure_ascii=False)
        except IOError as e:
            warning(f"缓存写入失败: {e}")

    def delete(self, platform: str, key: str) -> bool:
        """删除缓存条目

        Args:
            platform: 平台名称
            key: 缓存键

        Returns:
            是否成功删除
        """
        cache_path = self._get_cache_path(platform, key)
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
                return True
            except OSError:
                return False
        return False

    def clear(self, platform: Optional[str] = None) -> int:
        """清空缓存

        Args:
            platform: 指定平台，None则清空所有

        Returns:
            删除的文件数
        """
        count = 0
        if platform:
            platform_dir = self._get_platform_dir(platform)
            if os.path.exists(platform_dir):
                for filename in os.listdir(platform_dir):
                    if filename.endswith(".json"):
                        try:
                            os.remove(os.path.join(platform_dir, filename))
                            count += 1
                        except OSError:
                            pass
        else:
            for dirname in os.listdir(self.cache_dir):
                dir_path = os.path.join(self.cache_dir, dirname)
                if os.path.isdir(dir_path):
                    for filename in os.listdir(dir_path):
                        if filename.endswith(".json"):
                            try:
                                os.remove(os.path.join(dir_path, filename))
                                count += 1
                            except OSError:
                                pass
        return count

    def get_size(self) -> int:
        """获取当前缓存总大小（字节）"""
        total = 0
        for root, dirs, files in os.walk(self.cache_dir):
            for filename in files:
                if filename.endswith(".json"):
                    filepath = os.path.join(root, filename)
                    try:
                        total += os.path.getsize(filepath)
                    except OSError:
                        pass
        return total

    def get_size_mb(self) -> float:
        """获取当前缓存总大小（MB）"""
        return self.get_size() / (1024 * 1024)

    def get_count(self) -> int:
        """获取缓存条目数"""
        count = 0
        for root, dirs, files in os.walk(self.cache_dir):
            for filename in files:
                if filename.endswith(".json"):
                    count += 1
        return count

    def _evict_if_needed(self) -> None:
        """检查缓存大小，必要时进行LRU淘汰"""
        current_size = self.get_size()
        if current_size <= self.max_size_bytes:
            return

        # 收集所有缓存条目及其访问时间
        entries = []
        for root, dirs, files in os.walk(self.cache_dir):
            for filename in files:
                if filename.endswith(".json"):
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            entry_data = json.load(f)
                        entries.append((
                            filepath,
                            entry_data.get("accessed_at", 0),
                            os.path.getsize(filepath),
                        ))
                    except (json.JSONDecodeError, IOError, KeyError):
                        # 损坏的文件直接删除
                        try:
                            os.remove(filepath)
                        except OSError:
                            pass

        # 按访问时间排序（最旧的在前）
        entries.sort(key=lambda x: x[1])

        # 淘汰最旧的条目直到大小降到限制的80%
        target_size = int(self.max_size_bytes * 0.8)
        for filepath, _, size in entries:
            if current_size <= target_size:
                break
            try:
                os.remove(filepath)
                current_size -= size
                debug(f"LRU淘汰: {filepath}")
            except OSError:
                pass

    def cleanup_expired(self) -> int:
        """清理所有过期缓存

        Returns:
            清理的条目数
        """
        count = 0
        now = time.time()
        for root, dirs, files in os.walk(self.cache_dir):
            for filename in files:
                if filename.endswith(".json"):
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            entry_data = json.load(f)
                        if now > entry_data.get("expires_at", 0):
                            os.remove(filepath)
                            count += 1
                    except (json.JSONDecodeError, IOError, KeyError):
                        try:
                            os.remove(filepath)
                            count += 1
                        except OSError:
                            pass
        return count

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "size_bytes": self.get_size(),
            "size_mb": round(self.get_size_mb(), 2),
            "max_size_mb": self.max_size_bytes // (1024 * 1024),
            "count": self.get_count(),
            "default_ttl": self.default_ttl,
            "cache_dir": self.cache_dir,
        }
