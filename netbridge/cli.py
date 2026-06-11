"""CLI入口模块 - NetBridge命令行界面

使用argparse实现子命令系统，支持彩色输出（ANSI转义码，零依赖）。
"""

import argparse
import json
import sys
import os
from typing import Optional

from . import __version__
from .core.engine import Engine
from .core.config import ConfigManager
from .core.normalizer import Normalizer
from .mcp.server import MCPServer
from .utils.logger import (
    get_logger, info, warning, error, debug,
    success, fail, status, highlight, dim,
    colored_text, Colors,
)

logger = get_logger("netbridge.cli")


class CLI:
    """NetBridge命令行界面"""

    def __init__(self):
        self.parser = self._build_parser()
        self.config = ConfigManager()
        self.engine = Engine(self.config)

    def _build_parser(self) -> argparse.ArgumentParser:
        """构建命令行参数解析器"""
        parser = argparse.ArgumentParser(
            prog="netbridge",
            description=colored_text(
                "NetBridge - AI Agent多平台互联网能力装配引擎",
                Colors.CYAN + Colors.BOLD,
            ),
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self._get_epilog(),
        )

        parser.add_argument(
            "-v", "--version",
            action="version",
            version=f"NetBridge v{__version__}",
        )

        parser.add_argument(
            "--debug",
            action="store_true",
            help="启用调试模式",
        )

        parser.add_argument(
            "--no-cache",
            action="store_true",
            help="禁用缓存",
        )

        subparsers = parser.add_subparsers(
            dest="command",
            help="可用子命令",
            metavar="COMMAND",
        )

        # install 子命令
        install_parser = subparsers.add_parser(
            "install",
            help="安装/检查插件依赖",
            description="安装指定插件的可选依赖，或检查所有插件依赖状态",
        )
        install_parser.add_argument(
            "plugin",
            nargs="?",
            default=None,
            help="插件名称（留空则检查所有）",
        )

        # config 子命令
        config_parser = subparsers.add_parser(
            "config",
            help="管理配置",
            description="查看或修改NetBridge配置",
        )
        config_parser.add_argument(
            "action",
            nargs="?",
            default="show",
            choices=["show", "set", "reset"],
            help="配置操作: show(查看), set(设置), reset(重置)",
        )
        config_parser.add_argument(
            "key",
            nargs="?",
            default=None,
            help="配置键（如 cache.ttl）",
        )
        config_parser.add_argument(
            "value",
            nargs="?",
            default=None,
            help="配置值",
        )

        # check 子命令
        check_parser = subparsers.add_parser(
            "check",
            help="健康检查所有插件状态",
            description="检查所有已加载插件的运行状态",
        )
        check_parser.add_argument(
            "--json",
            action="store_true",
            help="以JSON格式输出",
        )

        # list 子命令
        list_parser = subparsers.add_parser(
            "list",
            help="列出所有可用插件",
            description="列出所有已加载的插件及其信息",
        )
        list_parser.add_argument(
            "--json",
            action="store_true",
            help="以JSON格式输出",
        )

        # search 子命令
        search_parser = subparsers.add_parser(
            "search",
            help="搜索内容",
            description="在指定平台上搜索内容",
        )
        search_parser.add_argument(
            "platform",
            help="平台名称 (web/github/rss/youtube/twitter/reddit/bilibili/xiaohongshu/v2ex/xueqiu/linkedin/xiaoyuzhou)",
        )
        search_parser.add_argument(
            "query",
            help="搜索关键词",
        )
        search_parser.add_argument(
            "-l", "--limit",
            type=int,
            default=10,
            help="结果数量限制（默认10）",
        )
        search_parser.add_argument(
            "--text",
            action="store_true",
            help="以纯文本格式输出",
        )

        # read 子命令
        read_parser = subparsers.add_parser(
            "read",
            help="读取内容",
            description="读取指定平台上的内容",
        )
        read_parser.add_argument(
            "platform",
            help="平台名称",
        )
        read_parser.add_argument(
            "url_or_id",
            help="URL或内容ID",
        )
        read_parser.add_argument(
            "--text",
            action="store_true",
            help="以纯文本格式输出",
        )

        # mcp 子命令
        mcp_parser = subparsers.add_parser(
            "mcp",
            help="启动MCP Server",
            description="启动Model Context Protocol服务器，供AI Agent调用",
        )
        mcp_parser.add_argument(
            "--transport",
            choices=["stdio", "tcp"],
            default="stdio",
            help="传输模式（默认stdio）",
        )
        mcp_parser.add_argument(
            "--host",
            default="127.0.0.1",
            help="TCP监听地址（默认127.0.0.1）",
        )
        mcp_parser.add_argument(
            "--port",
            type=int,
            default=8765,
            help="TCP监听端口（默认8765）",
        )

        # cache 子命令
        cache_parser = subparsers.add_parser(
            "cache",
            help="缓存管理",
            description="管理NetBridge缓存",
        )
        cache_parser.add_argument(
            "action",
            choices=["stats", "clear", "cleanup"],
            help="缓存操作: stats(统计), clear(清空), cleanup(清理过期)",
        )
        cache_parser.add_argument(
            "platform",
            nargs="?",
            default=None,
            help="指定平台（留空则操作所有）",
        )

        return parser

    def _get_epilog(self) -> str:
        """获取帮助信息尾部"""
        return f"""
{colored_text('示例:', Colors.BOLD)}
  netbridge list                    列出所有插件
  netbridge check                   健康检查
  netbridge search github python    搜索GitHub仓库
  netbridge read web https://...   读取网页内容
  netbridge read bilibili BV1xx    读取B站视频
  netbridge install youtube         安装YouTube插件依赖
  netbridge mcp                     启动MCP Server
  netbridge cache stats             查看缓存统计

{colored_text('支持的平台:', Colors.BOLD)}
  web, github, rss, youtube, twitter, reddit, bilibili,
  xiaohongshu, v2ex, xueqiu, linkedin, xiaoyuzhou
"""

    def run(self, args: Optional[list] = None) -> int:
        """运行CLI

        Args:
            args: 命令行参数，None则使用sys.argv

        Returns:
            退出码
        """
        parsed = self.parser.parse_args(args)

        # 调试模式
        if parsed.debug:
            import logging
            get_logger("netbridge", level=logging.DEBUG)

        # 禁用缓存
        if parsed.no_cache:
            self.config.set("cache.enabled", False)

        # 无子命令则显示帮助
        if not parsed.command:
            self.parser.print_help()
            return 0

        try:
            # 路由到对应处理方法
            handler = getattr(self, f"_cmd_{parsed.command}", None)
            if handler:
                return handler(parsed)
            else:
                error(f"未知命令: {parsed.command}")
                return 1
        except KeyboardInterrupt:
            print()
            dim("已取消")
            return 130
        except Exception as e:
            error(f"执行失败: {e}")
            if parsed.debug:
                import traceback
                traceback.print_exc()
            return 1

    def _cmd_install(self, args: argparse.Namespace) -> int:
        """处理install命令"""
        status("检查插件依赖...")
        self.engine.load_plugins()

        results = self.engine.install_plugin_deps(args.plugin)

        success_count = sum(1 for r in results.values() if r["success"])
        fail_count = sum(1 for r in results.values() if not r["success"])

        print()
        if fail_count == 0:
            success(f"所有插件依赖就绪 ({success_count}/{len(results)})")
        else:
            warning(f"部分插件依赖异常 ({success_count}成功, {fail_count}失败)")

        return 0 if fail_count == 0 else 1

    def _cmd_config(self, args: argparse.Namespace) -> int:
        """处理config命令"""
        if args.action == "show":
            print(self.config.show())
        elif args.action == "set":
            if not args.key or args.value is None:
                error("请提供配置键和值，例如: netbridge config set cache.ttl 7200")
                return 1
            self.config.set(args.key, args.value)
            self.config.save()
            success(f"已设置 {args.key} = {args.value}")
        elif args.action == "reset":
            self.config.reset()
            success("配置已重置为默认值")
        return 0

    def _cmd_check(self, args: argparse.Namespace) -> int:
        """处理check命令"""
        status("正在检查插件状态...")
        self.engine.load_plugins()

        results = self.engine.check_all_health()

        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print()
            for item in results:
                name = item["name"]
                healthy = item["healthy"]
                message = item["message"]

                if healthy:
                    success(f"{name}: {message}")
                else:
                    fail(f"{name}: {message}")

            # 汇总
            healthy_count = sum(1 for r in results if r["healthy"])
            total = len(results)
            print()
            if healthy_count == total:
                success(f"所有插件就绪 ({healthy_count}/{total})")
            else:
                warning(f"部分插件异常 ({healthy_count}/{total} 就绪)")

        return 0

    def _cmd_list(self, args: argparse.Namespace) -> int:
        """处理list命令"""
        self.engine.load_plugins()
        plugins = self.engine.list_plugins()

        if args.json:
            print(json.dumps(plugins, ensure_ascii=False, indent=2))
        else:
            print()
            tier_labels = {0: "核心", 1: "扩展", 2: "实验"}
            tier_colors = {
                0: Colors.GREEN,
                1: Colors.YELLOW,
                2: Colors.MAGENTA,
            }

            for plugin in plugins:
                tier = plugin["tier"]
                tier_label = tier_labels.get(tier, "未知")
                tier_color = tier_colors.get(tier, Colors.WHITE)

                # 状态指示
                status_icon = colored_text("OK", Colors.GREEN) if plugin["healthy"] else colored_text("XX", Colors.RED)

                # 插件名称
                name = colored_text(
                    f"{plugin['name']:<14}",
                    Colors.BOLD,
                )

                # Tier标签
                tier_text = colored_text(f"[{tier_label}]", tier_color)

                print(f"  {status_icon} {name} {tier_text}  {plugin['description']}")

            print()
            highlight(f"共 {len(plugins)} 个插件")

        return 0

    def _cmd_search(self, args: argparse.Namespace) -> int:
        """处理search命令"""
        status(f"搜索 [{args.platform}]: {args.query} ...")

        result = self.engine.search(
            args.platform,
            args.query,
            limit=args.limit,
        )

        if args.text:
            print(Normalizer.format_output(result, "text"))
        else:
            print(result.to_json())

        return 0

    def _cmd_read(self, args: argparse.Namespace) -> int:
        """处理read命令"""
        status(f"读取 [{args.platform}]: {args.url_or_id} ...")

        result = self.engine.read(args.platform, args.url_or_id)

        if args.text:
            print(Normalizer.format_output(result, "text"))
        else:
            print(result.to_json())

        return 0

    def _cmd_mcp(self, args: argparse.Namespace) -> int:
        """处理mcp命令"""
        server = MCPServer(self.config)

        if args.transport == "stdio":
            highlight("NetBridge MCP Server 启动 (stdio模式)")
            dim("等待MCP客户端连接...")
            server.run_stdio()
        else:
            highlight(f"NetBridge MCP Server 启动 (TCP: {args.host}:{args.port})")
            server.run_tcp(host=args.host, port=args.port)

        return 0

    def _cmd_cache(self, args: argparse.Namespace) -> int:
        """处理cache命令"""
        if args.action == "stats":
            stats = self.engine.get_cache_stats()
            print(json.dumps(stats, ensure_ascii=False, indent=2))
        elif args.action == "clear":
            count = self.engine.clear_cache(args.platform)
            if args.platform:
                success(f"已清空 {args.platform} 缓存 ({count} 条)")
            else:
                success(f"已清空所有缓存 ({count} 条)")
        elif args.action == "cleanup":
            count = self.engine.cache.cleanup_expired()
            success(f"已清理过期缓存 ({count} 条)")
        return 0


def main() -> int:
    """CLI入口函数"""
    cli = CLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
