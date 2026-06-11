"""MCP Server实现 - 使用标准库socket/JSON实现JSON-RPC协议

支持stdio传输，兼容Claude Desktop / Cursor等MCP客户端。
暴露search和read工具供AI Agent调用。
"""

import json
import sys
import os
from typing import Any, Dict, List, Optional

from ..core.engine import Engine
from ..core.config import ConfigManager
from ..utils.logger import get_logger, debug, error

logger = get_logger("netbridge.mcp")

# MCP协议版本
MCP_VERSION = "2024-11-05"

# MCP Server信息
SERVER_INFO = {
    "name": "netbridge",
    "version": "0.1.0",
}


class MCPServer:
    """MCP Server实现

    使用stdio传输的JSON-RPC 2.0服务器，
    为AI Agent提供search和read工具。
    """

    def __init__(self, config: Optional[ConfigManager] = None):
        """初始化MCP Server

        Args:
            config: 配置管理器
        """
        self.config = config or ConfigManager()
        self.engine = Engine(self.config)
        self.engine.load_plugins()
        self._request_id = 0

    def _next_id(self) -> int:
        """获取下一个请求ID"""
        self._request_id += 1
        return self._request_id

    def _make_response(self, result: Any, req_id: Optional[int] = None) -> Dict[str, Any]:
        """构建JSON-RPC响应"""
        response: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "result": result,
        }
        if req_id is not None:
            response["id"] = req_id
        return response

    def _make_error(self, code: int, message: str, req_id: Optional[int] = None) -> Dict[str, Any]:
        """构建JSON-RPC错误响应"""
        error_resp: Dict[str, Any] = {
            "jsonrpc": "2.0",
            "error": {
                "code": code,
                "message": message,
            },
        }
        if req_id is not None:
            error_resp["id"] = req_id
        return error_resp

    def _handle_initialize(self, params: Dict[str, Any], req_id: int) -> Dict[str, Any]:
        """处理initialize请求"""
        result = {
            "protocolVersion": MCP_VERSION,
            "capabilities": {
                "tools": {
                    "listChanged": False,
                },
            },
            "serverInfo": SERVER_INFO,
        }
        return self._make_response(result, req_id)

    def _handle_initialized(self, params: Dict[str, Any], req_id: int) -> Dict[str, Any]:
        """处理initialized通知（无需响应）"""
        return {}

    def _handle_tools_list(self, params: Dict[str, Any], req_id: int) -> Dict[str, Any]:
        """处理tools/list请求"""
        tools = [
            {
                "name": "search",
                "description": "在指定平台上搜索内容。支持的平台: web, github, rss, youtube, twitter, reddit, bilibili, xiaohongshu, v2ex, xueqiu, linkedin, xiaoyuzhou",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "platform": {
                            "type": "string",
                            "description": "平台名称",
                            "enum": [
                                "web", "github", "rss", "youtube", "twitter",
                                "reddit", "bilibili", "xiaohongshu", "v2ex",
                                "xueqiu", "linkedin", "xiaoyuzhou",
                            ],
                        },
                        "query": {
                            "type": "string",
                            "description": "搜索关键词",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "结果数量限制，默认10",
                            "default": 10,
                        },
                    },
                    "required": ["platform", "query"],
                },
            },
            {
                "name": "read",
                "description": "读取指定平台上的内容。支持的平台: web, github, rss, youtube, twitter, reddit, bilibili, xiaohongshu, v2ex, xueqiu, linkedin, xiaoyuzhou",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "platform": {
                            "type": "string",
                            "description": "平台名称",
                            "enum": [
                                "web", "github", "rss", "youtube", "twitter",
                                "reddit", "bilibili", "xiaohongshu", "v2ex",
                                "xueqiu", "linkedin", "xiaoyuzhou",
                            ],
                        },
                        "url_or_id": {
                            "type": "string",
                            "description": "URL或内容ID",
                        },
                    },
                    "required": ["platform", "url_or_id"],
                },
            },
            {
                "name": "list_platforms",
                "description": "列出所有可用的平台插件及其状态",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
        ]
        return self._make_response({"tools": tools}, req_id)

    def _handle_tools_call(self, params: Dict[str, Any], req_id: int) -> Dict[str, Any]:
        """处理tools/call请求"""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        try:
            if tool_name == "search":
                return self._tool_search(arguments, req_id)
            elif tool_name == "read":
                return self._tool_read(arguments, req_id)
            elif tool_name == "list_platforms":
                return self._tool_list_platforms(req_id)
            else:
                return self._make_error(
                    -32601,
                    f"未知工具: {tool_name}",
                    req_id,
                )
        except Exception as e:
            error(f"工具调用失败: {e}")
            return self._make_error(-32603, f"工具执行失败: {e}", req_id)

    def _tool_search(self, args: Dict[str, Any], req_id: int) -> Dict[str, Any]:
        """执行search工具"""
        platform = args.get("platform", "")
        query = args.get("query", "")
        limit = args.get("limit", 10)

        if not platform or not query:
            return self._make_error(
                -32602,
                "缺少必要参数: platform 和 query",
                req_id,
            )

        result = self.engine.search(platform, query, limit=limit)
        result_dict = result.to_dict()

        # 构建MCP工具响应
        content = []
        text_content = result.to_json()
        content.append({
            "type": "text",
            "text": text_content,
        })

        return self._make_response({
            "content": content,
            "isError": result_dict.get("data", {}).get("error", False),
        }, req_id)

    def _tool_read(self, args: Dict[str, Any], req_id: int) -> Dict[str, Any]:
        """执行read工具"""
        platform = args.get("platform", "")
        url_or_id = args.get("url_or_id", "")

        if not platform or not url_or_id:
            return self._make_error(
                -32602,
                "缺少必要参数: platform 和 url_or_id",
                req_id,
            )

        result = self.engine.read(platform, url_or_id)
        result_dict = result.to_dict()

        # 构建MCP工具响应
        content = []
        text_content = result.to_json()
        content.append({
            "type": "text",
            "text": text_content,
        })

        return self._make_response({
            "content": content,
            "isError": result_dict.get("data", {}).get("error", False),
        }, req_id)

    def _tool_list_platforms(self, req_id: int) -> Dict[str, Any]:
        """执行list_platforms工具"""
        plugins = self.engine.list_plugins()
        text = json.dumps(plugins, ensure_ascii=False, indent=2)

        return self._make_response({
            "content": [
                {
                    "type": "text",
                    "text": text,
                }
            ],
        }, req_id)

    def _handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理单个JSON-RPC请求

        Args:
            request: JSON-RPC请求字典

        Returns:
            响应字典，通知类型返回None
        """
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id")
        is_notification = "id" not in request

        debug(f"MCP请求: {method}")

        if method == "initialize":
            return self._handle_initialize(params, req_id)
        elif method == "notifications/initialized":
            # 通知，无需响应
            return None
        elif method == "tools/list":
            return self._handle_tools_list(params, req_id)
        elif method == "tools/call":
            return self._handle_tools_call(params, req_id)
        elif method == "ping":
            return self._make_response({}, req_id)
        else:
            if not is_notification:
                return self._make_error(-32601, f"未知方法: {method}", req_id)
            return None

    def run_stdio(self) -> None:
        """以stdio模式运行MCP Server

        从标准输入读取JSON-RPC请求，
        将响应写入标准输出。
        """
        debug("MCP Server 启动 (stdio模式)")

        # 重定向日志到stderr（避免干扰stdio通信）
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")

        reader = sys.stdin
        writer = sys.stdout

        # 逐行读取JSON-RPC请求
        for line in reader:
            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
                response = self._handle_request(request)

                if response is not None:
                    writer.write(json.dumps(response, ensure_ascii=False) + "\n")
                    writer.flush()

            except json.JSONDecodeError as e:
                error(f"JSON解析失败: {e}")
                error_resp = self._make_error(-32700, f"解析错误: {e}")
                writer.write(json.dumps(error_resp, ensure_ascii=False) + "\n")
                writer.flush()

            except Exception as e:
                error(f"请求处理失败: {e}")
                error_resp = self._make_error(-32603, f"内部错误: {e}")
                writer.write(json.dumps(error_resp, ensure_ascii=False) + "\n")
                writer.flush()

    def run_tcp(self, host: str = "127.0.0.1", port: int = 8765) -> None:
        """以TCP模式运行MCP Server

        Args:
            host: 监听地址
            port: 监听端口
        """
        import socket

        debug(f"MCP Server 启动 (TCP模式: {host}:{port})")

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen(1)

        try:
            while True:
                conn, addr = server_socket.accept()
                debug(f"客户端连接: {addr}")
                try:
                    self._handle_tcp_connection(conn)
                except Exception as e:
                    error(f"连接处理失败: {e}")
                finally:
                    conn.close()
        except KeyboardInterrupt:
            debug("MCP Server 停止")
        finally:
            server_socket.close()

    def _handle_tcp_connection(self, conn: Any) -> None:
        """处理TCP连接"""
        buffer = ""
        while True:
            data = conn.recv(4096)
            if not data:
                break

            buffer += data.decode("utf-8", errors="replace")

            # 按行处理
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                    response = self._handle_request(request)

                    if response is not None:
                        conn.sendall(
                            (json.dumps(response, ensure_ascii=False) + "\n").encode("utf-8")
                        )

                except json.JSONDecodeError as e:
                    error_resp = self._make_error(-32700, f"解析错误: {e}")
                    conn.sendall(
                        (json.dumps(error_resp, ensure_ascii=False) + "\n").encode("utf-8")
                    )
