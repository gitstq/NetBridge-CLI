# NetBridge-CLI

AI Agent多平台互联网能力装配引擎

## 安装

```bash
pip install -e .
```

安装所有可选依赖：

```bash
pip install -e ".[all]"
```

## 使用

```bash
# 列出所有插件
netbridge list

# 健康检查
netbridge check

# 搜索内容
netbridge search github python
netbridge search bilibili AI教程

# 读取内容
netbridge read web https://example.com
netbridge read github python/cpython
netbridge read bilibili BV1xx411c7mD

# 启动MCP Server
netbridge mcp

# 缓存管理
netbridge cache stats
netbridge cache clear
```

## 支持的平台

| 平台 | 层级 | 说明 |
|------|------|------|
| web | 核心 | 网页读取（Jina Reader） |
| github | 核心 | GitHub REST API |
| reddit | 核心 | Reddit 公开API |
| bilibili | 核心 | B站 API |
| v2ex | 核心 | V2EX 公开API |
| xueqiu | 核心 | 雪球 API |
| linkedin | 核心 | LinkedIn（Jina Reader） |
| xiaoyuzhou | 核心 | 小宇宙播客 API |
| rss | 扩展 | RSS/Atom（需要feedparser） |
| youtube | 扩展 | YouTube（需要yt-dlp） |
| twitter | 扩展 | Twitter/X（需要Cookie） |
| xiaohongshu | 扩展 | 小红书（需要Cookie） |

## MCP Server

NetBridge内置MCP Server，支持stdio和TCP两种传输模式。

Claude Desktop配置示例：

```json
{
  "mcpServers": {
    "netbridge": {
      "command": "netbridge",
      "args": ["mcp"]
    }
  }
}
```

## License

MIT
