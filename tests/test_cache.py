"""缓存测试模块 - 测试缓存读写和过期"""

import unittest
import os
import sys
import time
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from netbridge.core.cache import FileCache, CacheEntry


class TestCacheEntry(unittest.TestCase):
    """缓存条目测试"""

    def test_cache_entry_creation(self):
        """测试缓存条目创建"""
        entry = CacheEntry(data={"key": "value"}, ttl=60)
        self.assertEqual(entry.data, {"key": "value"})
        self.assertFalse(entry.is_expired)

    def test_cache_entry_expiry(self):
        """测试缓存过期"""
        entry = CacheEntry(data="test", ttl=-1)  # 已过期
        self.assertTrue(entry.is_expired)

    def test_cache_entry_touch(self):
        """测试更新访问时间"""
        entry = CacheEntry(data="test", ttl=3600)
        old_access = entry.accessed_at
        time.sleep(0.01)
        entry.touch()
        self.assertGreaterEqual(entry.accessed_at, old_access)

    def test_cache_entry_serialization(self):
        """测试序列化和反序列化"""
        entry = CacheEntry(data={"foo": "bar", "num": 42}, ttl=3600)
        d = entry.to_dict()

        self.assertIn("data", d)
        self.assertIn("created_at", d)
        self.assertIn("expires_at", d)
        self.assertIn("accessed_at", d)

        restored = CacheEntry.from_dict(d)
        self.assertEqual(restored.data, entry.data)
        self.assertEqual(restored.created_at, entry.created_at)
        self.assertEqual(restored.expires_at, entry.expires_at)


class TestFileCache(unittest.TestCase):
    """文件缓存测试"""

    def setUp(self):
        """测试前准备"""
        self.cache_dir = "/tmp/test_netbridge_cache"
        # 清理旧的测试缓存
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
        self.cache = FileCache(
            cache_dir=self.cache_dir,
            ttl=60,
            max_size_mb=1,
        )

    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)

    def test_cache_dir_creation(self):
        """测试缓存目录创建"""
        self.assertTrue(os.path.exists(self.cache_dir))

    def test_set_and_get(self):
        """测试缓存写入和读取"""
        self.cache.set("web", "test_key", {"title": "测试", "content": "内容"})
        result = self.cache.get("web", "test_key")
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "测试")
        self.assertEqual(result["content"], "内容")

    def test_cache_miss(self):
        """测试缓存未命中"""
        result = self.cache.get("web", "nonexistent_key")
        self.assertIsNone(result)

    def test_cache_expiry(self):
        """测试缓存过期"""
        # 写入TTL为-1的缓存（已过期）
        self.cache.set("web", "expire_test", "data", ttl=-1)
        result = self.cache.get("web", "expire_test")
        self.assertIsNone(result)

    def test_cache_delete(self):
        """测试缓存删除"""
        self.cache.set("web", "delete_test", "data")
        self.assertTrue(self.cache.delete("web", "delete_test"))
        self.assertIsNone(self.cache.get("web", "delete_test"))

    def test_cache_clear(self):
        """测试缓存清空"""
        self.cache.set("web", "key1", "data1")
        self.cache.set("github", "key2", "data2")
        count = self.cache.clear()
        self.assertGreater(count, 0)
        self.assertEqual(self.cache.get_count(), 0)

    def test_cache_clear_by_platform(self):
        """测试按平台清空缓存"""
        self.cache.set("web", "key1", "data1")
        self.cache.set("github", "key2", "data2")
        count = self.cache.clear("web")
        self.assertGreater(count, 0)
        self.assertIsNone(self.cache.get("web", "key1"))
        self.assertIsNotNone(self.cache.get("github", "key2"))

    def test_cache_stats(self):
        """测试缓存统计"""
        self.cache.set("web", "key1", "data1")
        self.cache.set("github", "key2", {"complex": "data"})

        stats = self.cache.get_stats()
        self.assertIn("size_bytes", stats)
        self.assertIn("size_mb", stats)
        self.assertIn("max_size_mb", stats)
        self.assertIn("count", stats)
        self.assertEqual(stats["count"], 2)

    def test_cache_count(self):
        """测试缓存计数"""
        self.assertEqual(self.cache.get_count(), 0)
        self.cache.set("web", "key1", "data1")
        self.cache.set("web", "key2", "data2")
        self.cache.set("github", "key3", "data3")
        self.assertEqual(self.cache.get_count(), 3)

    def test_cleanup_expired(self):
        """测试清理过期缓存"""
        self.cache.set("web", "valid", "data", ttl=3600)
        self.cache.set("web", "expired", "data", ttl=-1)
        count = self.cache.cleanup_expired()
        self.assertGreater(count, 0)
        self.assertIsNone(self.cache.get("web", "expired"))
        self.assertIsNotNone(self.cache.get("web", "valid"))

    def test_different_platforms_isolated(self):
        """测试不同平台缓存隔离"""
        self.cache.set("web", "same_key", "web_data")
        self.cache.set("github", "same_key", "github_data")

        web_result = self.cache.get("web", "same_key")
        github_result = self.cache.get("github", "same_key")

        self.assertEqual(web_result, "web_data")
        self.assertEqual(github_result, "github_data")


if __name__ == "__main__":
    unittest.main()
