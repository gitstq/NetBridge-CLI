<p align="center">
  <img src="assets/logo.jpg" alt="NetBridge-CLI Logo" width="120" height="120" />
</p>

<h1 align="center">NetBridge-CLI</h1>

<p align="center">
  <strong>AI Agent 多平台互联网能力装配引擎</strong>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/" target="_blank">
    <img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg" alt="Python 3.10+" />
  </a>
  <a href="https://github.com/gitstq/NetBridge-CLI/blob/main/LICENSE" target="_blank">
    <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT" />
  </a>
  <img src="https://img.shields.io/badge/Version-v0.1.0-orange.svg" alt="Version: v0.1.0" />
  <a href="https://github.com/gitstq/NetBridge-CLI" target="_blank">
    <img src="https://img.shields.io/badge/GitHub-NetBridge--CLI-black.svg?logo=github" alt="GitHub" />
  </a>
  <a href="https://pypi.org/project/netbridge-cli/" target="_blank">
    <img src="https://img.shields.io/badge/PyPI-netbridge--cli-blue.svg?logo=pypi" alt="PyPI" />
  </a>
</p>

<p align="center">
  <a href="#"><strong>简体中文</strong></a> | <a href="#english"><strong>English</strong></a> | <a href="#繁體中文"><strong>繁體中文</strong></a>
</p>

---

## 🎉 项目介绍

**NetBridge-CLI** 是一款为 AI Agent 设计的多平台互联网能力装配引擎。它通过统一的命令行接口和 MCP（Model Context Protocol）Server，让 AI Agent 能够轻松访问和操作 12 个主流互联网平台的内容。

### 🤔 为什么需要 NetBridge？

在 AI Agent 快速发展的今天，Agent 需要获取来自不同互联网平台的实时信息。然而，每个平台的 API 接口、数据格式、认证方式都各不相同，为 Agent 集成互联网能力带来了巨大挑战。

NetBridge 的核心理念是 **"装配"** 而非 "集成"：

- 🧩 **插件化架构**：每个平台是一个独立插件，按需加载
- 🔌 **零依赖核心**：核心功能仅使用 Python 标准库，安装即用
- 📡 **MCP 协议**：原生支持 Model Context Protocol，与 Claude Desktop / Cursor 无缝对接
- 🔄 **统一输出**：所有平台返回标准化 JSON，Agent 无需关心底层差异
- 💾 **智能缓存**：LRU + TTL 缓存机制，有效节省 Token 消耗

### 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────┐
│                   AI Agent                          │
│          (Claude Desktop / Cursor / ...)            │
└──────────────────────┬──────────────────────────────┘
                       │ MCP Protocol (JSON-RPC 2.0)
                       │
┌──────────────────────▼──────────────────────────────┐
│                 NetBridge-CLI                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ MCP Server│  │ CLI 引擎 │  │  智能缓存系统     │  │
│  │ (stdio/  │  │ (argparse│  │  (LRU + TTL)     │  │
│  │  TCP)    │  │  彩色输出)│  │                  │  │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
│       │              │                  │            │
│  ┌────▼──────────────▼──────────────────▼─────────┐│
│  │              核心引擎 (Engine)                    ││
│  │         插件发现 / 加载 / 路由                    ││
│  └────────────────────┬────────────────────────────┘│
│                       │                              │
│  ┌────────────────────▼────────────────────────────┐│
│  │              插件层 (Plugins)                     ││
│  │  web │ github │ youtube │ twitter │ reddit │ ... ││
│  └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

---

## ✨ 核心特性

| 特性 | 描述 |
|:---:|:---|
| 🧩 **插件化架构** | 自动发现加载机制，新增平台只需编写一个 Python 文件，无需修改核心代码 |
| 🚫 **零依赖核心** | 核心功能仅使用 Python 标准库（`urllib`、`json`、`argparse`），安装即用 |
| 📋 **统一输出格式** | 所有平台返回标准化 JSON 格式，Agent 无需适配不同数据结构 |
| 💾 **智能缓存系统** | 基于文件的 LRU 缓存 + TTL 过期机制，有效节省 Token 消耗 |
| 📡 **内置 MCP Server** | 原生支持 JSON-RPC 2.0，兼容 Claude Desktop / Cursor 等 MCP 客户端 |
| 🎛️ **交互式配置向导** | TUI 配置界面，降低使用门槛，支持 `show` / `set` / `reset` 操作 |
| 🎨 **彩色终端输出** | 基于 ANSI 转义码的彩色输出，零外部依赖 |
| 🧪 **57 个单元测试** | 完整的测试覆盖，确保代码质量和稳定性 |

---

## 🌐 支持平台

NetBridge 当前支持 **12 个互联网平台**，覆盖社交媒体、开发者社区、内容平台和资讯聚合等多个领域。

| 平台 | 标识符 | 层级 | 说明 | 额外依赖 |
|:---:|:---:|:---:|:---|:---:|
| 🌍 Web 网页 | `web` | 核心 | 网页内容读取（Jina Reader） | 无 |
| 🐙 GitHub | `github` | 核心 | GitHub REST API（仓库、Issue、PR） | 无 |
| 📺 YouTube | `youtube` | 扩展 | 视频搜索与信息获取 | `yt-dlp` |
| 🐦 Twitter/X | `twitter` | 扩展 | 推文搜索与读取 | Cookie |
| 🔴 Reddit | `reddit` | 核心 | Reddit 公开 API | 无 |
| 📱 Bilibili (B站) | `bilibili` | 核心 | B站视频搜索与读取 | 无 |
| 📕 小红书 | `xiaohongshu` | 扩展 | 笔记搜索与读取 | Cookie |
| 💬 V2EX | `v2ex` | 核心 | V2EX 社区 API | 无 |
| 📈 雪球 | `xueqiu` | 核心 | 雪球财经 API | 无 |
| 💼 LinkedIn | `linkedin` | 核心 | LinkedIn 内容读取（Jina Reader） | 无 |
| 📡 RSS 订阅 | `rss` | 扩展 | RSS/Atom 订阅源解析 | `feedparser` |
| 🎙️ 小宇宙播客 | `xiaoyuzhou` | 核心 | 播客搜索与读取 | 无 |

> **层级说明**：
> - **核心**（Tier 0）：零外部依赖，安装即用
> - **扩展**（Tier 1）：需要额外依赖或配置，通过 `netbridge install <plugin>` 安装

---

## 🚀 快速开始

### 📦 安装

```bash
# 从 GitHub 安装（推荐）
pip install git+https://github.com/gitstq/NetBridge-CLI.git

# 或克隆后本地安装
git clone https://github.com/gitstq/NetBridge-CLI.git
cd NetBridge-CLI
pip install -e .

# 安装所有可选依赖（RSS、YouTube 等）
pip install -e ".[all]"
```

### 🔍 第一步：验证安装

```bash
# 查看版本
netbridge --version

# 列出所有可用插件
netbridge list

# 健康检查
netbridge check
```

### 🎯 立即体验

```bash
# 搜索 GitHub 仓库
netbridge search github "python/cpython"

# 读取 GitHub 仓库信息
netbridge read github "python/cpython"

# 搜索 Web 内容
netbridge search web "AI agent tools"

# 读取网页内容
netbridge read web "https://example.com"

# 搜索 B站视频
netbridge search bilibili "AI教程"

# 读取 B站视频信息
netbridge read bilibili "BV1xx411c7mD"
```

---

## 📖 详细使用指南

### `netbridge install [plugin]` - 安装插件依赖

安装指定插件的可选依赖，或检查所有插件的依赖状态。

```bash
# 安装 YouTube 插件依赖
netbridge install youtube

# 安装 RSS 插件依赖
netbridge install rss

# 检查所有插件依赖状态
netbridge install
```

### `netbridge config` - 配置管理

查看或修改 NetBridge 配置。

```bash
# 查看当前配置
netbridge config show

# 设置配置项
netbridge config set cache.ttl 7200

# 重置为默认配置
netbridge config reset
```

### `netbridge check` - 健康检查

检查所有已加载插件的运行状态。

```bash
# 彩色终端输出
netbridge check

# JSON 格式输出（便于程序处理）
netbridge check --json
```

### `netbridge list` - 列出插件

列出所有已加载的插件及其详细信息。

```bash
# 彩色终端输出
netbridge list

# JSON 格式输出
netbridge list --json
```

### `netbridge search <platform> <query>` - 搜索内容

在指定平台上搜索内容。

```bash
# 基本搜索
netbridge search github "fastapi"
netbridge search web "Python async tutorial"
netbridge search bilibili "机器学习入门"
netbridge search reddit "python tips"

# 限制结果数量
netbridge search github "cli tools" --limit 5

# 纯文本格式输出
netbridge search github "langchain" --text
```

### `netbridge read <platform> <url/id>` - 读取内容

读取指定平台上的内容详情。

```bash
# 读取 GitHub 仓库
netbridge read github "python/cpython"

# 读取网页内容
netbridge read web "https://docs.python.org/3/"

# 读取 B站视频
netbridge read bilibili "BV1xx411c7mD"

# 读取 Reddit 帖子
netbridge read reddit "python/rPython"

# 纯文本格式输出
netbridge read github "python/cpython" --text
```

### `netbridge mcp` - 启动 MCP Server

启动 Model Context Protocol 服务器，供 AI Agent 调用。

```bash
# stdio 模式（默认，适用于 Claude Desktop）
netbridge mcp

# TCP 模式
netbridge mcp --transport tcp --host 127.0.0.1 --port 8765
```

### `netbridge cache` - 缓存管理

管理 NetBridge 的智能缓存系统。

```bash
# 查看缓存统计
netbridge cache stats

# 清空所有缓存
netbridge cache clear

# 清空指定平台缓存
netbridge cache clear github

# 清理过期缓存
netbridge cache cleanup
```

### 🎛️ 全局选项

```bash
# 启用调试模式（输出详细日志）
netbridge --debug search github "test"

# 禁用缓存
netbridge --no-cache read web "https://example.com"

# 查看版本
netbridge --version
```

---

## 🔌 MCP Server 配置

NetBridge 内置 MCP（Model Context Protocol）Server，支持 **stdio** 和 **TCP** 两种传输模式，兼容 Claude Desktop、Cursor 等 MCP 客户端。

### Claude Desktop 配置

编辑 Claude Desktop 配置文件（`claude_desktop_config.json`）：

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

配置完成后，Claude Desktop 将自动获得以下工具：

| 工具名 | 描述 | 参数 |
|:---:|:---|:---|
| `search` | 在指定平台上搜索内容 | `platform`, `query`, `limit` |
| `read` | 读取指定平台上的内容 | `platform`, `url_or_id` |
| `list_platforms` | 列出所有可用平台及其状态 | 无 |

### Cursor 配置

编辑 Cursor 的 MCP 配置文件：

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

### TCP 模式

适用于需要远程连接的场景：

```bash
# 启动 TCP 模式 MCP Server
netbridge mcp --transport tcp --host 127.0.0.1 --port 8765
```

### 在 Agent 中使用示例

配置完成后，你可以在 Claude Desktop 或 Cursor 中直接让 Agent 执行以下操作：

> "帮我搜索 GitHub 上最热门的 Python CLI 工具"
>
> "读取这个 B站视频的内容：BV1xx411c7mD"
>
> "帮我查看小红书上关于 AI 编程的最新笔记"

---

## 🏗️ 插件开发指南

NetBridge 的插件化架构让新增平台变得非常简单。只需创建一个继承 `BasePlugin` 的 Python 文件即可。

### 最小插件示例

```python
# netbridge/plugins/my_platform.py
"""MyPlatform 插件 - 示例插件"""

from typing import Any, Dict, List
from .base import BasePlugin
from ..core.normalizer import NormalizedResult, Normalizer


class MyPlatformPlugin(BasePlugin):
    """自定义平台插件"""

    @property
    def name(self) -> str:
        return "MyPlatform"

    @property
    def description(self) -> str:
        return "我的自定义平台"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def tier(self) -> int:
        return 0  # 0=核心(零依赖), 1=扩展(可选依赖), 2=实验性

    @property
    def platform(self) -> str:
        return "myplatform"

    def search(self, query: str, limit: int = 10) -> NormalizedResult:
        """搜索内容"""
        # 在此实现搜索逻辑
        results = [{"title": "结果1", "url": "https://example.com/1"}]
        return Normalizer.create_search_result(
            platform=self.platform,
            results=results,
        )

    def read(self, url_or_id: str) -> NormalizedResult:
        """读取内容"""
        # 在此实现读取逻辑
        data = {"title": "文章标题", "content": "文章内容", "url": url_or_id}
        return Normalizer.create_read_result(
            platform=self.platform,
            **data,
        )
```

### 插件开发要点

1. **文件位置**：将插件文件放在 `netbridge/plugins/` 目录下
2. **自动发现**：引擎会自动扫描该目录，无需手动注册
3. **必须实现**：`name`、`description`、`version`、`tier`、`platform`、`search()`、`read()`
4. **可选覆盖**：`check_health()`、`install_deps()`、`get_dependencies()`、`get_config_schema()`
5. **标准化输出**：使用 `Normalizer.create_search_result()` 和 `Normalizer.create_read_result()` 确保输出格式统一
6. **错误处理**：使用 `self._make_error()` 创建标准化错误结果

### 插件层级说明

| 层级 | 值 | 说明 | 示例 |
|:---:|:---:|:---|:---|
| 核心 | 0 | 零外部依赖，安装即用 | `web`、`github`、`reddit` |
| 扩展 | 1 | 需要额外依赖或配置 | `youtube`、`rss`、`twitter` |
| 实验 | 2 | 实验性功能，可能不稳定 | 自定义实验插件 |

---

## 💡 设计思路与迭代规划

### 🎯 设计哲学

1. **极简核心**：核心功能零外部依赖，确保在任何 Python 环境中都能运行
2. **约定优于配置**：插件自动发现、标准化输出、默认配置开箱即用
3. **渐进式复杂度**：简单场景零配置，复杂场景按需扩展
4. **Agent 优先**：所有设计决策以 AI Agent 的使用场景为第一优先级

### 📅 迭代规划

#### v0.1.0（当前版本）- 基础能力
- [x] 插件化架构与自动发现
- [x] 12 个平台插件
- [x] CLI 命令行接口
- [x] MCP Server（stdio + TCP）
- [x] 智能缓存系统（LRU + TTL）
- [x] 彩色终端输出
- [x] 57 个单元测试

#### v0.2.0（规划中）- 增强能力
- [ ] 插件市场与在线安装
- [ ] 异步请求支持（`asyncio`）
- [ ] 代理与认证管理增强
- [ ] 输出格式扩展（Markdown、HTML）
- [ ] Web Dashboard 可视化管理

#### v0.3.0（远期规划）- 生态建设
- [ ] 多语言 SDK（JavaScript / Go / Rust）
- [ ] Agent 工作流编排
- [ ] 分布式缓存支持（Redis）
- [ ] 插件沙箱与安全隔离

---

## 📦 打包与部署指南

### 本地开发

```bash
# 克隆项目
git clone https://github.com/gitstq/NetBridge-CLI.git
cd NetBridge-CLI

# 安装开发模式
pip install -e .

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
python -m pytest tests/ -v

# 代码检查
ruff check netbridge/ tests/

# 类型检查
mypy netbridge/
```

### 使用 Makefile

项目提供了便捷的 Makefile 命令：

```bash
make install        # 安装项目（开发模式）
make install-all    # 安装项目及所有可选依赖
make install-dev    # 安装开发依赖
make test           # 运行测试
make test-cov       # 运行测试（含覆盖率）
make lint           # 代码检查
make format         # 代码格式化
make typecheck      # 类型检查
make check          # 完整检查（lint + typecheck + test）
make build          # 构建分发包
make clean          # 清理构建产物
```

### 构建 PyPI 分发包

```bash
# 安装构建工具
pip install build

# 构建 sdist 和 wheel
python -m build

# 构建产物在 dist/ 目录下
ls dist/
# netbridge_cli-0.1.0-py3-none-any.whl
# netbridge-cli-0.1.0.tar.gz
```

### 发布到 PyPI

```bash
# 安装 twine
pip install twine

# 检查分发包
twine check dist/*

# 上传到 PyPI
twine upload dist/*
```

---

## 🤝 贡献指南

我们欢迎并感谢所有形式的贡献！无论是提交 Bug、改进文档，还是开发新插件。

### 🍴 参与贡献的步骤

1. **Fork** 本仓库
2. 创建特性分支：`git checkout -b feature/my-new-plugin`
3. 提交更改：`git commit -m 'Add new plugin: myplatform'`
4. 推送分支：`git push origin feature/my-new-plugin`
5. 提交 **Pull Request**

### 📝 贡献规范

- **代码风格**：遵循 [PEP 8](https://peps.python.org/pep-0008/)，使用 `ruff` 进行格式化和检查
- **类型注解**：所有公共方法请添加类型注解
- **测试覆盖**：新增功能请附带对应的单元测试
- **提交信息**：使用语义化提交信息（Conventional Commits）
- **文档更新**：新增插件请同步更新 README 和使用文档

### 🐛 报告问题

如果发现 Bug 或有功能建议，请通过 [GitHub Issues](https://github.com/gitstq/NetBridge-CLI/issues) 提交。

---

## 📄 开源协议

本项目基于 [MIT License](https://github.com/gitstq/NetBridge-CLI/blob/main/LICENSE) 开源。

```
MIT License

Copyright (c) 2024 NetBridge Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/gitstq/NetBridge-CLI">NetBridge Team</a>
</p>

---

<!-- English -->

<a id="english"></a>

<p align="center">
  <img src="assets/logo.jpg" alt="NetBridge-CLI Logo" width="120" height="120" />
</p>

<h1 align="center">NetBridge-CLI</h1>

<p align="center">
  <strong>AI Agent Multi-Platform Internet Capability Assembly Engine</strong>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/" target="_blank">
    <img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg" alt="Python 3.10+" />
  </a>
  <a href="https://github.com/gitstq/NetBridge-CLI/blob/main/LICENSE" target="_blank">
    <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT" />
  </a>
  <img src="https://img.shields.io/badge/Version-v0.1.0-orange.svg" alt="Version: v0.1.0" />
  <a href="https://github.com/gitstq/NetBridge-CLI" target="_blank">
    <img src="https://img.shields.io/badge/GitHub-NetBridge--CLI-black.svg?logo=github" alt="GitHub" />
  </a>
  <a href="https://pypi.org/project/netbridge-cli/" target="_blank">
    <img src="https://img.shields.io/badge/PyPI-netbridge--cli-blue.svg?logo=pypi" alt="PyPI" />
  </a>
</p>

<p align="center">
  <a href="#"><strong>简体中文</strong></a> | <a href="#english"><strong>English</strong></a> | <a href="#繁體中文"><strong>繁體中文</strong></a>
</p>

---

## 🎉 Introduction

**NetBridge-CLI** is a multi-platform internet capability assembly engine designed for AI Agents. It provides a unified CLI interface and MCP (Model Context Protocol) Server, enabling AI Agents to easily access and interact with content from **12 major internet platforms**.

### 🤔 Why NetBridge?

As AI Agents evolve rapidly, they need real-time information from various internet platforms. However, each platform has different API interfaces, data formats, and authentication methods, creating a significant challenge for Agent integration.

NetBridge's core philosophy is **"Assembly"** over "Integration":

- 🧩 **Plugin Architecture**: Each platform is an independent plugin, loaded on demand
- 🔌 **Zero-Dependency Core**: Core functionality uses only Python standard library, ready to use out of the box
- 📡 **MCP Protocol**: Native support for Model Context Protocol, seamlessly compatible with Claude Desktop / Cursor
- 🔄 **Unified Output**: All platforms return standardized JSON, Agents don't need to handle format differences
- 💾 **Smart Caching**: LRU + TTL caching mechanism to effectively save Token consumption

### 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   AI Agent                          │
│          (Claude Desktop / Cursor / ...)            │
└──────────────────────┬──────────────────────────────┘
                       │ MCP Protocol (JSON-RPC 2.0)
                       │
┌──────────────────────▼──────────────────────────────┐
│                 NetBridge-CLI                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ MCP Server│  │ CLI Engine│  │  Smart Cache     │  │
│  │ (stdio/  │  │ (argparse│  │  (LRU + TTL)     │  │
│  │  TCP)    │  │  colored)│  │                  │  │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
│       │              │                  │            │
│  ┌────▼──────────────▼──────────────────▼─────────┐│
│  │              Core Engine                          ││
│  │         Discovery / Loading / Routing            ││
│  └────────────────────┬────────────────────────────┘│
│                       │                              │
│  ┌────────────────────▼────────────────────────────┐│
│  │              Plugin Layer                        ││
│  │  web │ github │ youtube │ twitter │ reddit │ ... ││
│  └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

---

## ✨ Core Features

| Feature | Description |
|:---:|:---|
| 🧩 **Plugin Architecture** | Auto-discovery and loading mechanism. Add a new platform by writing a single Python file |
| 🚫 **Zero-Dependency Core** | Core uses only Python standard library (`urllib`, `json`, `argparse`). Ready to use |
| 📋 **Unified Output Format** | All platforms return standardized JSON format |
| 💾 **Smart Cache System** | File-based LRU cache with TTL expiration, saving Token consumption |
| 📡 **Built-in MCP Server** | Native JSON-RPC 2.0 support, compatible with Claude Desktop / Cursor |
| 🎛️ **Interactive Config Wizard** | TUI configuration interface with `show` / `set` / `reset` operations |
| 🎨 **Colored Terminal Output** | ANSI escape code-based colored output, zero external dependencies |
| 🧪 **57 Unit Tests** | Comprehensive test coverage ensuring code quality and stability |

---

## 🌐 Supported Platforms

NetBridge currently supports **12 internet platforms** covering social media, developer communities, content platforms, and news aggregation.

| Platform | Identifier | Tier | Description | Extra Deps |
|:---:|:---:|:---:|:---|:---:|
| 🌍 Web | `web` | Core | Web page reading (Jina Reader) | None |
| 🐙 GitHub | `github` | Core | GitHub REST API (repos, issues, PRs) | None |
| 📺 YouTube | `youtube` | Extended | Video search and info retrieval | `yt-dlp` |
| 🐦 Twitter/X | `twitter` | Extended | Tweet search and reading | Cookie |
| 🔴 Reddit | `reddit` | Core | Reddit public API | None |
| 📱 Bilibili | `bilibili` | Core | Bilibili video search and reading | None |
| 📕 Xiaohongshu | `xiaohongshu` | Extended | Note search and reading | Cookie |
| 💬 V2EX | `v2ex` | Core | V2EX community API | None |
| 📈 Xueqiu | `xueqiu` | Core | Xueqiu financial API | None |
| 💼 LinkedIn | `linkedin` | Core | LinkedIn content reading (Jina Reader) | None |
| 📡 RSS | `rss` | Extended | RSS/Atom feed parsing | `feedparser` |
| 🎙️ Xiaoyuzhou Podcast | `xiaoyuzhou` | Core | Podcast search and reading | None |

> **Tier Legend**:
> - **Core** (Tier 0): Zero external dependencies, ready to use
> - **Extended** (Tier 1): Requires additional dependencies or configuration. Install via `netbridge install <plugin>`

---

## 🚀 Quick Start

### 📦 Installation

```bash
# Install from GitHub (recommended)
pip install git+https://github.com/gitstq/NetBridge-CLI.git

# Or clone and install locally
git clone https://github.com/gitstq/NetBridge-CLI.git
cd NetBridge-CLI
pip install -e .

# Install all optional dependencies (RSS, YouTube, etc.)
pip install -e ".[all]"
```

### 🔍 First Steps

```bash
# Check version
netbridge --version

# List all available plugins
netbridge list

# Health check
netbridge check
```

### 🎯 Try It Out

```bash
# Search GitHub repositories
netbridge search github "python/cpython"

# Read GitHub repository info
netbridge read github "python/cpython"

# Search the web
netbridge search web "AI agent tools"

# Read a web page
netbridge read web "https://example.com"

# Search Bilibili videos
netbridge search bilibili "AI tutorial"

# Read Bilibili video info
netbridge read bilibili "BV1xx411c7mD"
```

---

## 📖 Detailed Usage Guide

### `netbridge install [plugin]` - Install Plugin Dependencies

Install optional dependencies for a specific plugin or check all plugin dependency status.

```bash
# Install YouTube plugin dependencies
netbridge install youtube

# Install RSS plugin dependencies
netbridge install rss

# Check all plugin dependency status
netbridge install
```

### `netbridge config` - Configuration Management

View or modify NetBridge configuration.

```bash
# View current configuration
netbridge config show

# Set a configuration value
netbridge config set cache.ttl 7200

# Reset to default configuration
netbridge config reset
```

### `netbridge check` - Health Check

Check the status of all loaded plugins.

```bash
# Colored terminal output
netbridge check

# JSON format output (for programmatic use)
netbridge check --json
```

### `netbridge list` - List Plugins

List all loaded plugins with detailed information.

```bash
# Colored terminal output
netbridge list

# JSON format output
netbridge list --json
```

### `netbridge search <platform> <query>` - Search Content

Search for content on a specified platform.

```bash
# Basic search
netbridge search github "fastapi"
netbridge search web "Python async tutorial"
netbridge search bilibili "machine learning intro"
netbridge search reddit "python tips"

# Limit results
netbridge search github "cli tools" --limit 5

# Plain text output
netbridge search github "langchain" --text
```

### `netbridge read <platform> <url/id>` - Read Content

Read content details from a specified platform.

```bash
# Read a GitHub repository
netbridge read github "python/cpython"

# Read a web page
netbridge read web "https://docs.python.org/3/"

# Read a Bilibili video
netbridge read bilibili "BV1xx411c7mD"

# Read a Reddit post
netbridge read reddit "python/rPython"

# Plain text output
netbridge read github "python/cpython" --text
```

### `netbridge mcp` - Start MCP Server

Start the Model Context Protocol server for AI Agent integration.

```bash
# stdio mode (default, for Claude Desktop)
netbridge mcp

# TCP mode
netbridge mcp --transport tcp --host 127.0.0.1 --port 8765
```

### `netbridge cache` - Cache Management

Manage NetBridge's smart caching system.

```bash
# View cache statistics
netbridge cache stats

# Clear all cache
netbridge cache clear

# Clear cache for a specific platform
netbridge cache clear github

# Clean up expired cache entries
netbridge cache cleanup
```

### 🎛️ Global Options

```bash
# Enable debug mode (verbose logging)
netbridge --debug search github "test"

# Disable cache
netbridge --no-cache read web "https://example.com"

# Show version
netbridge --version
```

---

## 🔌 MCP Server Configuration

NetBridge includes a built-in MCP (Model Context Protocol) Server supporting **stdio** and **TCP** transport modes, compatible with Claude Desktop, Cursor, and other MCP clients.

### Claude Desktop Configuration

Edit your Claude Desktop config file (`claude_desktop_config.json`):

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

After configuration, Claude Desktop will automatically have access to the following tools:

| Tool | Description | Parameters |
|:---:|:---|:---|
| `search` | Search content on a specified platform | `platform`, `query`, `limit` |
| `read` | Read content from a specified platform | `platform`, `url_or_id` |
| `list_platforms` | List all available platforms and their status | None |

### Cursor Configuration

Edit your Cursor MCP config file:

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

### TCP Mode

For scenarios requiring remote connections:

```bash
# Start TCP mode MCP Server
netbridge mcp --transport tcp --host 127.0.0.1 --port 8765
```

### Usage Examples in Agent

Once configured, you can ask Claude Desktop or Cursor to:

> "Search for the most popular Python CLI tools on GitHub"
>
> "Read the content of this Bilibili video: BV1xx411c7mD"
>
> "Find the latest notes about AI programming on Xiaohongshu"

---

## 🏗️ Plugin Development Guide

NetBridge's plugin architecture makes adding new platforms incredibly simple. Just create a Python file that inherits from `BasePlugin`.

### Minimal Plugin Example

```python
# netbridge/plugins/my_platform.py
"""MyPlatform Plugin - Example Plugin"""

from typing import Any, Dict, List
from .base import BasePlugin
from ..core.normalizer import NormalizedResult, Normalizer


class MyPlatformPlugin(BasePlugin):
    """Custom platform plugin"""

    @property
    def name(self) -> str:
        return "MyPlatform"

    @property
    def description(self) -> str:
        return "My custom platform"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def tier(self) -> int:
        return 0  # 0=Core (no deps), 1=Extended (optional deps), 2=Experimental

    @property
    def platform(self) -> str:
        return "myplatform"

    def search(self, query: str, limit: int = 10) -> NormalizedResult:
        """Search content"""
        # Implement your search logic here
        results = [{"title": "Result 1", "url": "https://example.com/1"}]
        return Normalizer.create_search_result(
            platform=self.platform,
            results=results,
        )

    def read(self, url_or_id: str) -> NormalizedResult:
        """Read content"""
        # Implement your read logic here
        data = {"title": "Article Title", "content": "Article content", "url": url_or_id}
        return Normalizer.create_read_result(
            platform=self.platform,
            **data,
        )
```

### Plugin Development Key Points

1. **File Location**: Place your plugin file in the `netbridge/plugins/` directory
2. **Auto-Discovery**: The engine automatically scans this directory, no manual registration needed
3. **Required Implementations**: `name`, `description`, `version`, `tier`, `platform`, `search()`, `read()`
4. **Optional Overrides**: `check_health()`, `install_deps()`, `get_dependencies()`, `get_config_schema()`
5. **Standardized Output**: Use `Normalizer.create_search_result()` and `Normalizer.create_read_result()` for consistent output
6. **Error Handling**: Use `self._make_error()` to create standardized error results

### Plugin Tier Explanation

| Tier | Value | Description | Examples |
|:---:|:---:|:---|:---|
| Core | 0 | Zero external dependencies, ready to use | `web`, `github`, `reddit` |
| Extended | 1 | Requires additional dependencies or configuration | `youtube`, `rss`, `twitter` |
| Experimental | 2 | Experimental features, may be unstable | Custom experimental plugins |

---

## 💡 Design Philosophy & Roadmap

### 🎯 Design Philosophy

1. **Minimal Core**: Zero external dependencies for core functionality, ensuring it runs in any Python environment
2. **Convention over Configuration**: Auto-discovery plugins, standardized output, default configs ready to use
3. **Progressive Complexity**: Zero config for simple scenarios, extendable for complex ones
4. **Agent First**: All design decisions prioritize AI Agent usage scenarios

### 📅 Roadmap

#### v0.1.0 (Current) - Foundation
- [x] Plugin architecture with auto-discovery
- [x] 12 platform plugins
- [x] CLI command-line interface
- [x] MCP Server (stdio + TCP)
- [x] Smart cache system (LRU + TTL)
- [x] Colored terminal output
- [x] 57 unit tests

#### v0.2.0 (Planned) - Enhanced Capabilities
- [ ] Plugin marketplace with online installation
- [ ] Async request support (`asyncio`)
- [ ] Enhanced proxy and authentication management
- [ ] Extended output formats (Markdown, HTML)
- [ ] Web Dashboard for visual management

#### v0.3.0 (Long-term) - Ecosystem
- [ ] Multi-language SDKs (JavaScript / Go / Rust)
- [ ] Agent workflow orchestration
- [ ] Distributed cache support (Redis)
- [ ] Plugin sandbox and security isolation

---

## 📦 Build & Deployment Guide

### Local Development

```bash
# Clone the project
git clone https://github.com/gitstq/NetBridge-CLI.git
cd NetBridge-CLI

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v

# Code linting
ruff check netbridge/ tests/

# Type checking
mypy netbridge/
```

### Using Makefile

The project provides convenient Makefile commands:

```bash
make install        # Install project (development mode)
make install-all    # Install project with all optional dependencies
make install-dev    # Install development dependencies
make test           # Run tests
make test-cov       # Run tests with coverage
make lint           # Code linting
make format         # Code formatting
make typecheck      # Type checking
make check          # Full check (lint + typecheck + test)
make build          # Build distribution packages
make clean          # Clean build artifacts
```

### Building PyPI Distribution

```bash
# Install build tools
pip install build

# Build sdist and wheel
python -m build

# Distribution packages are in the dist/ directory
ls dist/
# netbridge_cli-0.1.0-py3-none-any.whl
# netbridge-cli-0.1.0.tar.gz
```

### Publishing to PyPI

```bash
# Install twine
pip install twine

# Check distribution packages
twine check dist/*

# Upload to PyPI
twine upload dist/*
```

---

## 🤝 Contributing

We welcome and appreciate all forms of contributions! Whether it's reporting bugs, improving documentation, or developing new plugins.

### 🍴 How to Contribute

1. **Fork** this repository
2. Create a feature branch: `git checkout -b feature/my-new-plugin`
3. Commit your changes: `git commit -m 'Add new plugin: myplatform'`
4. Push to the branch: `git push origin feature/my-new-plugin`
5. Submit a **Pull Request**

### 📝 Contribution Guidelines

- **Code Style**: Follow [PEP 8](https://peps.python.org/pep-0008/), use `ruff` for formatting and linting
- **Type Annotations**: Add type annotations to all public methods
- **Test Coverage**: Include unit tests for new features
- **Commit Messages**: Use semantic commit messages (Conventional Commits)
- **Documentation**: Update README and documentation when adding new plugins

### 🐛 Reporting Issues

If you find a bug or have a feature suggestion, please submit it via [GitHub Issues](https://github.com/gitstq/NetBridge-CLI/issues).

---

## 📄 License

This project is licensed under the [MIT License](https://github.com/gitstq/NetBridge-CLI/blob/main/LICENSE).

```
MIT License

Copyright (c) 2024 NetBridge Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/gitstq/NetBridge-CLI">NetBridge Team</a>
</p>

---

<!-- Traditional Chinese -->

<a id="繁體中文"></a>

<p align="center">
  <img src="assets/logo.jpg" alt="NetBridge-CLI Logo" width="120" height="120" />
</p>

<h1 align="center">NetBridge-CLI</h1>

<p align="center">
  <strong>AI Agent 多平台網際網路能力裝配引擎</strong>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/" target="_blank">
    <img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg" alt="Python 3.10+" />
  </a>
  <a href="https://github.com/gitstq/NetBridge-CLI/blob/main/LICENSE" target="_blank">
    <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT" />
  </a>
  <img src="https://img.shields.io/badge/Version-v0.1.0-orange.svg" alt="Version: v0.1.0" />
  <a href="https://github.com/gitstq/NetBridge-CLI" target="_blank">
    <img src="https://img.shields.io/badge/GitHub-NetBridge--CLI-black.svg?logo=github" alt="GitHub" />
  </a>
  <a href="https://pypi.org/project/netbridge-cli/" target="_blank">
    <img src="https://img.shields.io/badge/PyPI-netbridge--cli-blue.svg?logo=pypi" alt="PyPI" />
  </a>
</p>

<p align="center">
  <a href="#"><strong>簡體中文</strong></a> | <a href="#english"><strong>English</strong></a> | <a href="#繁體中文"><strong>繁體中文</strong></a>
</p>

---

## 🎉 專案介紹

**NetBridge-CLI** 是一款為 AI Agent 設計的多平台網際網路能力裝配引擎。它透過統一的命令列介面和 MCP（Model Context Protocol）Server，讓 AI Agent 能夠輕鬆存取和操作 **12 個主流網際網路平台**的內容。

### 🤔 為什麼需要 NetBridge？

在 AI Agent 快速發展的今天，Agent 需要獲取來自不同網際網路平台的即時資訊。然而，每個平台的 API 介面、資料格式、認證方式都各不相同，為 Agent 整合網際網路能力帶來了巨大挑戰。

NetBridge 的核心理念是 **「裝配」** 而非「整合」：

- 🧩 **外掛架構**：每個平台是一個獨立外掛，按需載入
- 🔌 **零依賴核心**：核心功能僅使用 Python 標準函式庫，安裝即用
- 📡 **MCP 協議**：原生支援 Model Context Protocol，與 Claude Desktop / Cursor 無縫對接
- 🔄 **統一輸出**：所有平台回傳標準化 JSON，Agent 無需關心底層差異
- 💾 **智慧快取**：LRU + TTL 快取機制，有效節省 Token 消耗

### 🏗️ 架構概覽

```
┌─────────────────────────────────────────────────────┐
│                   AI Agent                          │
│          (Claude Desktop / Cursor / ...)            │
└──────────────────────┬──────────────────────────────┘
                       │ MCP Protocol (JSON-RPC 2.0)
                       │
┌──────────────────────▼──────────────────────────────┐
│                 NetBridge-CLI                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ MCP Server│  │ CLI 引擎 │  │  智慧快取系統     │  │
│  │ (stdio/  │  │ (argparse│  │  (LRU + TTL)     │  │
│  │  TCP)    │  │  彩色輸出)│  │                  │  │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
│       │              │                  │            │
│  ┌────▼──────────────▼──────────────────▼─────────┐│
│  │              核心引擎 (Engine)                    ││
│  │         外掛發現 / 載入 / 路由                    ││
│  └────────────────────┬────────────────────────────┘│
│                       │                              │
│  ┌────────────────────▼────────────────────────────┐│
│  │              外掛層 (Plugins)                     ││
│  │  web │ github │ youtube │ twitter │ reddit │ ... ││
│  └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

---

## ✨ 核心特性

| 特性 | 描述 |
|:---:|:---|
| 🧩 **外掛架構** | 自動發現載入機制，新增平台只需編寫一個 Python 檔案，無需修改核心程式碼 |
| 🚫 **零依賴核心** | 核心功能僅使用 Python 標準函式庫（`urllib`、`json`、`argparse`），安裝即用 |
| 📋 **統一輸出格式** | 所有平台回傳標準化 JSON 格式，Agent 無需適配不同資料結構 |
| 💾 **智慧快取系統** | 基於檔案的 LRU 快取 + TTL 過期機制，有效節省 Token 消耗 |
| 📡 **內建 MCP Server** | 原生支援 JSON-RPC 2.0，相容 Claude Desktop / Cursor 等 MCP 客戶端 |
| 🎛️ **互動式設定精靈** | TUI 設定介面，降低使用門檻，支援 `show` / `set` / `reset` 操作 |
| 🎨 **彩色終端輸出** | 基於 ANSI 跳脫碼的彩色輸出，零外部依賴 |
| 🧪 **57 個單元測試** | 完整的測試覆蓋，確保程式碼品質和穩定性 |

---

## 🌐 支援平台

NetBridge 目前支援 **12 個網際網路平台**，涵蓋社群媒體、開發者社群、內容平台和資訊聚合等多個領域。

| 平台 | 識別符 | 層級 | 說明 | 額外依賴 |
|:---:|:---:|:---:|:---|:---:|
| 🌍 Web 網頁 | `web` | 核心 | 網頁內容讀取（Jina Reader） | 無 |
| 🐙 GitHub | `github` | 核心 | GitHub REST API（倉庫、Issue、PR） | 無 |
| 📺 YouTube | `youtube` | 擴充 | 影片搜尋與資訊取得 | `yt-dlp` |
| 🐦 Twitter/X | `twitter` | 擴充 | 推文搜尋與讀取 | Cookie |
| 🔴 Reddit | `reddit` | 核心 | Reddit 公開 API | 無 |
| 📱 Bilibili (B站) | `bilibili` | 核心 | B站影片搜尋與讀取 | 無 |
| 📕 小紅書 | `xiaohongshu` | 擴充 | 筆記搜尋與讀取 | Cookie |
| 💬 V2EX | `v2ex` | 核心 | V2EX 社群 API | 無 |
| 📈 雪球 | `xueqiu` | 核心 | 雪球財經 API | 無 |
| 💼 LinkedIn | `linkedin` | 核心 | LinkedIn 內容讀取（Jina Reader） | 無 |
| 📡 RSS 訂閱 | `rss` | 擴充 | RSS/Atom 訂閱源解析 | `feedparser` |
| 🎙️ 小宇宙播客 | `xiaoyuzhou` | 核心 | 播客搜尋與讀取 | 無 |

> **層級說明**：
> - **核心**（Tier 0）：零外部依賴，安裝即用
> - **擴充**（Tier 1）：需要額外依賴或設定，透過 `netbridge install <plugin>` 安裝

---

## 🚀 快速開始

### 📦 安裝

```bash
# 從 GitHub 安裝（推薦）
pip install git+https://github.com/gitstq/NetBridge-CLI.git

# 或複製後本地安裝
git clone https://github.com/gitstq/NetBridge-CLI.git
cd NetBridge-CLI
pip install -e .

# 安裝所有可選依賴（RSS、YouTube 等）
pip install -e ".[all]"
```

### 🔍 第一步：驗證安裝

```bash
# 查看版本
netbridge --version

# 列出所有可用外掛
netbridge list

# 健康檢查
netbridge check
```

### 🎯 立即體驗

```bash
# 搜尋 GitHub 倉庫
netbridge search github "python/cpython"

# 讀取 GitHub 倉庫資訊
netbridge read github "python/cpython"

# 搜尋 Web 內容
netbridge search web "AI agent tools"

# 讀取網頁內容
netbridge read web "https://example.com"

# 搜尋 B站影片
netbridge search bilibili "AI教程"

# 讀取 B站影片資訊
netbridge read bilibili "BV1xx411c7mD"
```

---

## 📖 詳細使用指南

### `netbridge install [plugin]` - 安裝外掛依賴

安裝指定外掛的可選依賴，或檢查所有外掛的依賴狀態。

```bash
# 安裝 YouTube 外掛依賴
netbridge install youtube

# 安裝 RSS 外掛依賴
netbridge install rss

# 檢查所有外掛依賴狀態
netbridge install
```

### `netbridge config` - 設定管理

查看或修改 NetBridge 設定。

```bash
# 查看目前設定
netbridge config show

# 設定配置項
netbridge config set cache.ttl 7200

# 重設為預設設定
netbridge config reset
```

### `netbridge check` - 健康檢查

檢查所有已載入外掛的運行狀態。

```bash
# 彩色終端輸出
netbridge check

# JSON 格式輸出（便於程式處理）
netbridge check --json
```

### `netbridge list` - 列出外掛

列出所有已載入的外掛及其詳細資訊。

```bash
# 彩色終端輸出
netbridge list

# JSON 格式輸出
netbridge list --json
```

### `netbridge search <platform> <query>` - 搜尋內容

在指定平台上搜尋內容。

```bash
# 基本搜尋
netbridge search github "fastapi"
netbridge search web "Python async tutorial"
netbridge search bilibili "機器學習入門"
netbridge search reddit "python tips"

# 限制結果數量
netbridge search github "cli tools" --limit 5

# 純文字格式輸出
netbridge search github "langchain" --text
```

### `netbridge read <platform> <url/id>` - 讀取內容

讀取指定平台上的內容詳情。

```bash
# 讀取 GitHub 倉庫
netbridge read github "python/cpython"

# 讀取網頁內容
netbridge read web "https://docs.python.org/3/"

# 讀取 B站影片
netbridge read bilibili "BV1xx411c7mD"

# 讀取 Reddit 貼文
netbridge read reddit "python/rPython"

# 純文字格式輸出
netbridge read github "python/cpython" --text
```

### `netbridge mcp` - 啟動 MCP Server

啟動 Model Context Protocol 伺服器，供 AI Agent 呼叫。

```bash
# stdio 模式（預設，適用於 Claude Desktop）
netbridge mcp

# TCP 模式
netbridge mcp --transport tcp --host 127.0.0.1 --port 8765
```

### `netbridge cache` - 快取管理

管理 NetBridge 的智慧快取系統。

```bash
# 查看快取統計
netbridge cache stats

# 清空所有快取
netbridge cache clear

# 清空指定平台快取
netbridge cache clear github

# 清理過期快取
netbridge cache cleanup
```

### 🎛️ 全域選項

```bash
# 啟用除錯模式（輸出詳細日誌）
netbridge --debug search github "test"

# 停用快取
netbridge --no-cache read web "https://example.com"

# 查看版本
netbridge --version
```

---

## 🔌 MCP Server 設定

NetBridge 內建 MCP（Model Context Protocol）Server，支援 **stdio** 和 **TCP** 兩種傳輸模式，相容 Claude Desktop、Cursor 等 MCP 客戶端。

### Claude Desktop 設定

編輯 Claude Desktop 設定檔（`claude_desktop_config.json`）：

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

設定完成後，Claude Desktop 將自動獲得以下工具：

| 工具名 | 描述 | 參數 |
|:---:|:---|:---|
| `search` | 在指定平台上搜尋內容 | `platform`, `query`, `limit` |
| `read` | 讀取指定平台上的內容 | `platform`, `url_or_id` |
| `list_platforms` | 列出所有可用平台及其狀態 | 無 |

### Cursor 設定

編輯 Cursor 的 MCP 設定檔：

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

### TCP 模式

適用於需要遠端連線的場景：

```bash
# 啟動 TCP 模式 MCP Server
netbridge mcp --transport tcp --host 127.0.0.1 --port 8765
```

### 在 Agent 中使用範例

設定完成後，你可以在 Claude Desktop 或 Cursor 中直接讓 Agent 執行以下操作：

> 「幫我搜尋 GitHub 上最熱門的 Python CLI 工具」
>
> 「讀取這個 B站影片的內容：BV1xx411c7mD」
>
> 「幫我查看小紅書上關於 AI 程式設計的最新筆記」

---

## 🏗️ 外掛開發指南

NetBridge 的外掛架構讓新增平台變得非常簡單。只需建立一個繼承 `BasePlugin` 的 Python 檔案即可。

### 最小外掛範例

```python
# netbridge/plugins/my_platform.py
"""MyPlatform 外掛 - 範例外掛"""

from typing import Any, Dict, List
from .base import BasePlugin
from ..core.normalizer import NormalizedResult, Normalizer


class MyPlatformPlugin(BasePlugin):
    """自訂平台外掛"""

    @property
    def name(self) -> str:
        return "MyPlatform"

    @property
    def description(self) -> str:
        return "我的自訂平台"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def tier(self) -> int:
        return 0  # 0=核心(零依賴), 1=擴充(可選依賴), 2=實驗性

    @property
    def platform(self) -> str:
        return "myplatform"

    def search(self, query: str, limit: int = 10) -> NormalizedResult:
        """搜尋內容"""
        # 在此實作搜尋邏輯
        results = [{"title": "結果1", "url": "https://example.com/1"}]
        return Normalizer.create_search_result(
            platform=self.platform,
            results=results,
        )

    def read(self, url_or_id: str) -> NormalizedResult:
        """讀取內容"""
        # 在此實作讀取邏輯
        data = {"title": "文章標題", "content": "文章內容", "url": url_or_id}
        return Normalizer.create_read_result(
            platform=self.platform,
            **data,
        )
```

### 外掛開發要點

1. **檔案位置**：將外掛檔案放在 `netbridge/plugins/` 目錄下
2. **自動發現**：引擎會自動掃描該目錄，無需手動註冊
3. **必須實作**：`name`、`description`、`version`、`tier`、`platform`、`search()`、`read()`
4. **可選覆寫**：`check_health()`、`install_deps()`、`get_dependencies()`、`get_config_schema()`
5. **標準化輸出**：使用 `Normalizer.create_search_result()` 和 `Normalizer.create_read_result()` 確保輸出格式統一
6. **錯誤處理**：使用 `self._make_error()` 建立標準化錯誤結果

### 外掛層級說明

| 層級 | 值 | 說明 | 範例 |
|:---:|:---:|:---|:---|
| 核心 | 0 | 零外部依賴，安裝即用 | `web`、`github`、`reddit` |
| 擴充 | 1 | 需要額外依賴或設定 | `youtube`、`rss`、`twitter` |
| 實驗 | 2 | 實驗性功能，可能不穩定 | 自訂實驗外掛 |

---

## 💡 設計思路與迭代規劃

### 🎯 設計哲學

1. **極簡核心**：核心功能零外部依賴，確保在任何 Python 環境中都能運行
2. **約定優於設定**：外掛自動發現、標準化輸出、預設設定開箱即用
3. **漸進式複雜度**：簡單場景零設定，複雜場景按需擴充
4. **Agent 優先**：所有設計決策以 AI Agent 的使用場景為第一優先級

### 📅 迭代規劃

#### v0.1.0（目前版本）- 基礎能力
- [x] 外掛架構與自動發現
- [x] 12 個平台外掛
- [x] CLI 命令列介面
- [x] MCP Server（stdio + TCP）
- [x] 智慧快取系統（LRU + TTL）
- [x] 彩色終端輸出
- [x] 57 個單元測試

#### v0.2.0（規劃中）- 增強能力
- [ ] 外掛市場與線上安裝
- [ ] 非同步請求支援（`asyncio`）
- [ ] 代理與認證管理增強
- [ ] 輸出格式擴充（Markdown、HTML）
- [ ] Web Dashboard 视覺化管理

#### v0.3.0（遠期規劃）- 生態建設
- [ ] 多語言 SDK（JavaScript / Go / Rust）
- [ ] Agent 工作流程編排
- [ ] 分散式快取支援（Redis）
- [ ] 外掛沙箱與安全隔離

---

## 📦 打包與部署指南

### 本地開發

```bash
# 複製專案
git clone https://github.com/gitstq/NetBridge-CLI.git
cd NetBridge-CLI

# 安裝開發模式
pip install -e .

# 安裝開發依賴
pip install -e ".[dev]"

# 執行測試
python -m pytest tests/ -v

# 程式碼檢查
ruff check netbridge/ tests/

# 類型檢查
mypy netbridge/
```

### 使用 Makefile

專案提供了便捷的 Makefile 命令：

```bash
make install        # 安裝專案（開發模式）
make install-all    # 安裝專案及所有可選依賴
make install-dev    # 安裝開發依賴
make test           # 執行測試
make test-cov       # 執行測試（含覆蓋率）
make lint           # 程式碼檢查
make format         # 程式碼格式化
make typecheck      # 類型檢查
make check          # 完整檢查（lint + typecheck + test）
make build          # 建構分發包
make clean          # 清理建構產物
```

### 建構 PyPI 分發包

```bash
# 安裝建構工具
pip install build

# 建構 sdist 和 wheel
python -m build

# 建構產物在 dist/ 目錄下
ls dist/
# netbridge_cli-0.1.0-py3-none-any.whl
# netbridge-cli-0.1.0.tar.gz
```

### 發佈到 PyPI

```bash
# 安裝 twine
pip install twine

# 檢查分發包
twine check dist/*

# 上傳到 PyPI
twine upload dist/*
```

---

## 🤝 貢獻指南

我們歡迎並感謝所有形式的貢獻！無論是提交 Bug、改進文件，還是開發新外掛。

### 🍴 參與貢獻的步驟

1. **Fork** 本倉庫
2. 建立特性分支：`git checkout -b feature/my-new-plugin`
3. 提交更改：`git commit -m 'Add new plugin: myplatform'`
4. 推送分支：`git push origin feature/my-new-plugin`
5. 提交 **Pull Request**

### 📝 貢獻規範

- **程式碼風格**：遵循 [PEP 8](https://peps.python.org/pep-0008/)，使用 `ruff` 進行格式化和檢查
- **類型註解**：所有公共方法請新增類型註解
- **測試覆蓋**：新增功能請附帶對應的單元測試
- **提交資訊**：使用語義化提交資訊（Conventional Commits）
- **文件更新**：新增外掛請同步更新 README 和使用文件

### 🐛 回報問題

如果發現 Bug 或有功能建議，請透過 [GitHub Issues](https://github.com/gitstq/NetBridge-CLI/issues) 提交。

---

## 📄 開源協議

本專案基於 [MIT License](https://github.com/gitstq/NetBridge-CLI/blob/main/LICENSE) 開源。

```
MIT License

Copyright (c) 2024 NetBridge Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/gitstq/NetBridge-CLI">NetBridge Team</a>
</p>
