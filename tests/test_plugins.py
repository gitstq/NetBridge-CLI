"""插件测试模块 - 测试web和github插件"""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from netbridge.plugins.web import WebPlugin
from netbridge.plugins.github import GitHubPlugin
from netbridge.plugins.reddit import RedditPlugin
from netbridge.plugins.bilibili import BilibiliPlugin
from netbridge.plugins.v2ex import V2EXPlugin


class TestWebPlugin(unittest.TestCase):
    """Web插件测试"""

    def setUp(self):
        self.plugin = WebPlugin()

    def test_plugin_properties(self):
        """测试插件属性"""
        self.assertEqual(self.plugin.name, "web")
        self.assertEqual(self.plugin.platform, "web")
        self.assertEqual(self.plugin.tier, 0)
        self.assertEqual(self.plugin.version, "0.1.0")
        self.assertIsNotNone(self.plugin.description)

    def test_no_dependencies(self):
        """测试零依赖"""
        deps = self.plugin.get_dependencies()
        self.assertEqual(deps, [])

    def test_config_schema(self):
        """测试配置模板"""
        schema = self.plugin.get_config_schema()
        self.assertIsInstance(schema, dict)
        self.assertIn("jina_reader_url", schema)

    def test_search_result_structure(self):
        """测试搜索结果结构"""
        result = self.plugin.search("test query")
        self.assertIsNotNone(result)
        self.assertEqual(result.platform, "web")
        self.assertEqual(result.action, "search")
        # 网络不可用时返回错误字典，可用时返回列表
        if isinstance(result.data, dict) and result.data.get("error"):
            self.assertIn("error_message", result.data)
        else:
            self.assertIsInstance(result.data, list)

    def test_read_result_structure(self):
        """测试读取结果结构"""
        result = self.plugin.read("https://example.com")
        self.assertIsNotNone(result)
        self.assertEqual(result.platform, "web")
        self.assertEqual(result.action, "read")
        # 网络不可用时返回错误字典，可用时返回内容字典
        if isinstance(result.data, dict) and result.data.get("error"):
            self.assertIn("error_message", result.data)
        else:
            self.assertIsInstance(result.data, dict)
            self.assertIn("title", result.data)
            self.assertIn("content", result.data)

    def test_read_without_protocol(self):
        """测试无协议前缀的URL"""
        result = self.plugin.read("example.com")
        self.assertIsNotNone(result)
        self.assertEqual(result.platform, "web")

    def test_health_check(self):
        """测试健康检查"""
        health = self.plugin.check_health()
        self.assertIn("healthy", health)
        self.assertIn("message", health)
        self.assertIn("details", health)


class TestGitHubPlugin(unittest.TestCase):
    """GitHub插件测试"""

    def setUp(self):
        self.plugin = GitHubPlugin()

    def test_plugin_properties(self):
        """测试插件属性"""
        self.assertEqual(self.plugin.name, "github")
        self.assertEqual(self.plugin.platform, "github")
        self.assertEqual(self.plugin.tier, 0)
        self.assertEqual(self.plugin.version, "0.1.0")

    def test_no_dependencies(self):
        """测试零依赖"""
        deps = self.plugin.get_dependencies()
        self.assertEqual(deps, [])

    def test_config_schema(self):
        """测试配置模板"""
        schema = self.plugin.get_config_schema()
        self.assertIn("token", schema)

    def test_search_result_structure(self):
        """测试搜索结果结构"""
        result = self.plugin.search("python")
        self.assertIsNotNone(result)
        self.assertEqual(result.platform, "github")
        self.assertEqual(result.action, "search")
        self.assertIsInstance(result.data, list)

    def test_search_with_type(self):
        """测试带类型的搜索"""
        result = self.plugin.search("type:repos python")
        self.assertIsNotNone(result)
        self.assertEqual(result.platform, "github")

    def test_read_repo(self):
        """测试读取仓库"""
        result = self.plugin.read("python/cpython")
        self.assertIsNotNone(result)
        self.assertEqual(result.platform, "github")
        self.assertIsInstance(result.data, dict)
        self.assertIn("title", result.data)

    def test_parse_github_ref(self):
        """测试GitHub引用解析"""
        self.assertEqual(
            self.plugin._parse_github_ref("python/cpython"),
            ("python", "cpython", ""),
        )
        self.assertEqual(
            self.plugin._parse_github_ref("https://github.com/python/cpython"),
            ("python", "cpython", ""),
        )
        self.assertEqual(
            self.plugin._parse_github_ref("python/cpython/readme"),
            ("python", "cpython", "readme"),
        )

    def test_health_check(self):
        """测试健康检查"""
        health = self.plugin.check_health()
        self.assertIn("healthy", health)
        self.assertIn("message", health)


class TestRedditPlugin(unittest.TestCase):
    """Reddit插件测试"""

    def setUp(self):
        self.plugin = RedditPlugin()

    def test_plugin_properties(self):
        """测试插件属性"""
        self.assertEqual(self.plugin.name, "reddit")
        self.assertEqual(self.plugin.platform, "reddit")
        self.assertEqual(self.plugin.tier, 0)

    def test_search_result_structure(self):
        """测试搜索结果结构"""
        result = self.plugin.search("python")
        self.assertIsNotNone(result)
        self.assertEqual(result.platform, "reddit")
        self.assertEqual(result.action, "search")
        # 网络不可用时返回错误字典，可用时返回列表
        if isinstance(result.data, dict) and result.data.get("error"):
            self.assertIn("error_message", result.data)
        else:
            self.assertIsInstance(result.data, list)


class TestBilibiliPlugin(unittest.TestCase):
    """B站插件测试"""

    def setUp(self):
        self.plugin = BilibiliPlugin()

    def test_plugin_properties(self):
        """测试插件属性"""
        self.assertEqual(self.plugin.name, "bilibili")
        self.assertEqual(self.plugin.platform, "bilibili")
        self.assertEqual(self.plugin.tier, 0)

    def test_parse_bv_id(self):
        """测试BV号解析"""
        self.assertEqual(
            self.plugin._parse_bv_id("BV1xx411c7mD"),
            "BV1xx411c7mD",
        )
        self.assertEqual(
            self.plugin._parse_bv_id("https://www.bilibili.com/video/BV1xx411c7mD"),
            "BV1xx411c7mD",
        )

    def test_format_duration(self):
        """测试时长格式化"""
        self.assertEqual(self.plugin._format_duration(0), "00:00")
        self.assertEqual(self.plugin._format_duration(65), "01:05")
        self.assertEqual(self.plugin._format_duration(3665), "1:01:05")


class TestV2EXPlugin(unittest.TestCase):
    """V2EX插件测试"""

    def setUp(self):
        self.plugin = V2EXPlugin()

    def test_plugin_properties(self):
        """测试插件属性"""
        self.assertEqual(self.plugin.name, "v2ex")
        self.assertEqual(self.plugin.platform, "v2ex")
        self.assertEqual(self.plugin.tier, 0)


if __name__ == "__main__":
    unittest.main()
