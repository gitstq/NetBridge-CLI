"""格式化测试模块 - 测试输出格式化"""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from netbridge.core.normalizer import NormalizedResult, Normalizer


class TestNormalizedResult(unittest.TestCase):
    """标准化结果测试"""

    def test_creation(self):
        """测试创建标准化结果"""
        result = NormalizedResult(
            platform="web",
            action="read",
            data={"title": "测试", "content": "内容"},
        )
        self.assertEqual(result.platform, "web")
        self.assertEqual(result.action, "read")
        self.assertEqual(result.data["title"], "测试")
        self.assertFalse(result.cached)
        self.assertIsNotNone(result.timestamp)

    def test_to_dict(self):
        """测试转换为字典"""
        result = NormalizedResult(
            platform="github",
            action="search",
            data=[{"title": "repo1"}, {"title": "repo2"}],
        )
        d = result.to_dict()
        self.assertEqual(d["platform"], "github")
        self.assertEqual(d["action"], "search")
        self.assertIsInstance(d["data"], list)
        self.assertEqual(len(d["data"]), 2)
        self.assertIn("timestamp", d)
        self.assertIn("cached", d)

    def test_to_json(self):
        """测试转换为JSON"""
        result = NormalizedResult(
            platform="web",
            action="read",
            data={"title": "测试", "content": "内容"},
        )
        json_str = result.to_json()
        self.assertIsInstance(json_str, str)
        # 确保是有效的JSON
        import json
        parsed = json.loads(json_str)
        self.assertEqual(parsed["platform"], "web")
        self.assertEqual(parsed["data"]["title"], "测试")

    def test_repr(self):
        """测试字符串表示"""
        result = NormalizedResult(
            platform="web",
            action="read",
            data={"title": "test"},
        )
        repr_str = repr(result)
        self.assertIn("web", repr_str)
        self.assertIn("read", repr_str)


class TestNormalizer(unittest.TestCase):
    """格式化器测试"""

    def test_create_read_result(self):
        """测试创建读取结果"""
        result = Normalizer.create_read_result(
            platform="web",
            title="测试标题",
            content="测试内容",
            url="https://example.com",
            author="作者",
            published_at="2026-01-01",
        )
        self.assertEqual(result.platform, "web")
        self.assertEqual(result.action, "read")
        self.assertEqual(result.data["title"], "测试标题")
        self.assertEqual(result.data["content"], "测试内容")
        self.assertEqual(result.data["url"], "https://example.com")
        self.assertEqual(result.data["author"], "作者")
        self.assertEqual(result.data["published_at"], "2026-01-01")

    def test_create_search_result(self):
        """测试创建搜索结果"""
        results = [
            {"title": "结果1", "url": "https://1.com", "snippet": "摘要1"},
            {"title": "结果2", "url": "https://2.com", "snippet": "摘要2"},
        ]
        result = Normalizer.create_search_result(
            platform="github",
            results=results,
        )
        self.assertEqual(result.platform, "github")
        self.assertEqual(result.action, "search")
        self.assertIsInstance(result.data, list)
        self.assertEqual(len(result.data), 2)
        self.assertEqual(result.data[0]["title"], "结果1")
        self.assertEqual(result.data[0]["url"], "https://1.com")

    def test_create_search_result_with_metadata(self):
        """测试搜索结果保留额外元数据"""
        results = [
            {
                "title": "结果",
                "url": "https://example.com",
                "snippet": "摘要",
                "stars": 100,
                "language": "Python",
            },
        ]
        result = Normalizer.create_search_result(
            platform="github",
            results=results,
        )
        self.assertIn("metadata", result.data[0])
        self.assertEqual(result.data[0]["metadata"]["stars"], 100)
        self.assertEqual(result.data[0]["metadata"]["language"], "Python")

    def test_create_error_result(self):
        """测试创建错误结果"""
        result = Normalizer.create_error_result(
            platform="web",
            action="read",
            error="连接超时",
            error_code="TIMEOUT",
        )
        self.assertEqual(result.platform, "web")
        self.assertEqual(result.action, "read")
        self.assertTrue(result.data["error"])
        self.assertEqual(result.data["error_message"], "连接超时")
        self.assertEqual(result.data["error_code"], "TIMEOUT")

    def test_create_health_result(self):
        """测试创建健康检查结果"""
        result = Normalizer.create_health_result(
            platform="web",
            healthy=True,
            message="服务正常",
            details={"latency": 100},
        )
        self.assertEqual(result.platform, "web")
        self.assertEqual(result.action, "check")
        self.assertTrue(result.data["healthy"])
        self.assertEqual(result.data["message"], "服务正常")
        self.assertEqual(result.data["details"]["latency"], 100)

    def test_format_output_json(self):
        """测试JSON格式输出"""
        result = Normalizer.create_read_result(
            platform="web",
            title="测试",
            content="内容",
        )
        output = Normalizer.format_output(result, "json")
        import json
        parsed = json.loads(output)
        self.assertEqual(parsed["platform"], "web")

    def test_format_output_text(self):
        """测试文本格式输出"""
        result = Normalizer.create_read_result(
            platform="web",
            title="测试标题",
            content="测试内容" * 100,
            url="https://example.com",
            author="作者",
        )
        output = Normalizer.format_output(result, "text")
        self.assertIn("测试标题", output)
        self.assertIn("https://example.com", output)
        self.assertIn("作者", output)

    def test_format_text_search(self):
        """测试文本格式搜索输出"""
        results = [
            {"title": "结果1", "url": "https://1.com", "snippet": "摘要1"},
            {"title": "结果2", "url": "https://2.com", "snippet": "摘要2"},
        ]
        result = Normalizer.create_search_result(
            platform="github",
            results=results,
        )
        output = Normalizer.format_output(result, "text")
        self.assertIn("结果1", output)
        self.assertIn("结果2", output)
        self.assertIn("SEARCH", output)

    def test_cached_flag(self):
        """测试缓存标记"""
        result = Normalizer.create_read_result(
            platform="web",
            title="测试",
            content="内容",
            cached=True,
        )
        self.assertTrue(result.cached)
        d = result.to_dict()
        self.assertTrue(d["cached"])


if __name__ == "__main__":
    unittest.main()
