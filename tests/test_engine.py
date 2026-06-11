"""引擎测试模块 - 测试插件发现和加载"""

import unittest
import os
import sys

# 确保可以导入netbridge包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from netbridge.core.engine import Engine
from netbridge.core.config import ConfigManager


class TestEngine(unittest.TestCase):
    """引擎测试"""

    def setUp(self):
        """测试前准备"""
        self.config = ConfigManager(config_dir="/tmp/test_netbridge_config")
        self.engine = Engine(config=self.config)

    def test_engine_creation(self):
        """测试引擎创建"""
        self.assertIsNotNone(self.engine)
        self.assertIsNotNone(self.engine.cache)
        self.assertIsNotNone(self.engine.config)

    def test_discover_plugins(self):
        """测试插件发现"""
        plugins = self.engine.discover_plugins()
        self.assertIsInstance(plugins, list)
        self.assertIn("web", plugins)
        self.assertIn("github", plugins)
        self.assertIn("bilibili", plugins)
        self.assertIn("reddit", plugins)
        self.assertIn("v2ex", plugins)
        # 确保不包含基类和初始化模块
        self.assertNotIn("base", plugins)
        self.assertNotIn("__init__", plugins)

    def test_load_plugins(self):
        """测试插件加载"""
        count = self.engine.load_plugins()
        self.assertGreater(count, 0)
        # 至少加载了核心插件
        self.assertIn("web", self.engine._plugins)
        self.assertIn("github", self.engine._plugins)

    def test_get_plugin(self):
        """测试获取插件"""
        self.engine.load_plugins()

        # 测试存在的插件
        web_plugin = self.engine.get_plugin("web")
        self.assertIsNotNone(web_plugin)
        self.assertEqual(web_plugin.name, "web")

        # 测试别名
        gh_plugin = self.engine.get_plugin("gh")
        self.assertIsNotNone(gh_plugin)
        self.assertEqual(gh_plugin.name, "github")

        # 测试不存在的插件
        none_plugin = self.engine.get_plugin("nonexistent")
        self.assertIsNone(none_plugin)

    def test_list_plugins(self):
        """测试列出插件"""
        self.engine.load_plugins()
        plugins = self.engine.list_plugins()
        self.assertIsInstance(plugins, list)
        self.assertGreater(len(plugins), 0)

        # 检查每个插件的信息结构
        for plugin in plugins:
            self.assertIn("name", plugin)
            self.assertIn("description", plugin)
            self.assertIn("version", plugin)
            self.assertIn("tier", plugin)
            self.assertIn("platform", plugin)
            self.assertIn("healthy", plugin)

    def test_search_nonexistent_platform(self):
        """测试搜索不存在的平台"""
        result = self.engine.search("nonexistent", "test")
        self.assertEqual(result.platform, "nonexistent")
        self.assertEqual(result.action, "search")
        self.assertIn("error", result.data)

    def test_read_nonexistent_platform(self):
        """测试读取不存在的平台"""
        result = self.engine.read("nonexistent", "test")
        self.assertEqual(result.platform, "nonexistent")
        self.assertEqual(result.action, "read")
        self.assertIn("error", result.data)

    def test_check_all_health(self):
        """测试健康检查"""
        self.engine.load_plugins()
        results = self.engine.check_all_health()
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

        for result in results:
            self.assertIn("name", result)
            self.assertIn("healthy", result)
            self.assertIn("message", result)


if __name__ == "__main__":
    unittest.main()
