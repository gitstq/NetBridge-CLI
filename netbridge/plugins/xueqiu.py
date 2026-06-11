"""雪球插件 - 调用雪球API获取财经信息

通过雪球公开API获取股票、基金等财经信息。
"""

import json
import re
from typing import Any, Dict, List, Optional

from .base import BasePlugin
from ..core.normalizer import NormalizedResult, Normalizer
from ..utils.network import get_json, get_text, NetworkError
from ..utils.logger import get_logger

logger = get_logger("netbridge.plugin.xueqiu")

# 雪球API
XUEQIU_API = "https://xueqiu.com"
XUEQIU_QUERY = "https://xueqiu.com/query/v1"
XUEQIU_STOCK = "https://stock.xueqiu.com"


class XueqiuPlugin(BasePlugin):
    """雪球插件

    通过雪球API获取股票信息和财经资讯。
    """

    @property
    def name(self) -> str:
        return "xueqiu"

    @property
    def description(self) -> str:
        return "雪球插件，支持股票搜索和财经信息获取"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def tier(self) -> int:
        return 0  # 核心插件，公开API

    @property
    def platform(self) -> str:
        return "xueqiu"

    def _get_headers(self) -> Dict[str, str]:
        """获取雪球API请求头"""
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            "Referer": "https://xueqiu.com/",
            "Origin": "https://xueqiu.com",
            "Accept": "application/json",
        }

    def _get_cookies(self) -> Dict[str, str]:
        """获取雪球Cookie（用于获取token）"""
        cookies = self.get_config_value("cookies", {})
        if not cookies:
            # 尝试自动获取token
            try:
                import urllib.request
                req = urllib.request.Request(
                    "https://xueqiu.com/",
                    headers=self._get_headers(),
                )
                resp = urllib.request.urlopen(req, timeout=10)
                set_cookie = resp.headers.get("Set-Cookie", "")
                if set_cookie:
                    cookies = {}
                    for item in set_cookie.split(";"):
                        item = item.strip()
                        if "=" in item:
                            k, v = item.split("=", 1)
                            cookies[k.strip()] = v.strip()
            except Exception:
                pass
        return cookies

    def _get_xq_token(self) -> str:
        """获取xq_a_token"""
        cookies = self._get_cookies()
        return cookies.get("xq_a_token", cookies.get("xq_a_token", ""))

    def search(self, query: str, limit: int = 10) -> NormalizedResult:
        """搜索雪球内容

        Args:
            query: 搜索关键词（股票代码、名称等）
            limit: 结果数量限制

        Returns:
            标准化搜索结果
        """
        try:
            cookies = self._get_cookies()
            params = {
                "q": query,
                "count": min(limit, 10),
                "page": 1,
                "type": 10,
            }
            data = get_json(
                f"{XUEQIU_API}/query/v1/suggest.json",
                params=params,
                headers=self._get_headers(),
                cookies=cookies,
                timeout=15,
            )

            results = []
            suggestions = data.get("suggestions", [])
            for item in suggestions[:limit]:
                item_type = item.get("type", "")
                if item_type in ("stock", "fund", "etf"):
                    symbol = item.get("symbol", "")
                    name = item.get("name", "")
                    code = item.get("code", "")
                    results.append({
                        "title": f"{name} ({code})",
                        "url": f"https://xueqiu.com/S/{symbol}",
                        "snippet": f"{item_type.upper()} {symbol}",
                        "author": "",
                        "metadata": {
                            "symbol": symbol,
                            "code": code,
                            "type": item_type,
                            "exchange": item.get("exchange", ""),
                        },
                    })

            if not results:
                results.append({
                    "title": "未找到结果",
                    "url": "",
                    "snippet": f"没有找到与 '{query}' 相关的股票/基金",
                })

            return Normalizer.create_search_result(
                platform=self.platform,
                results=results[:limit],
            )

        except (NetworkError, Exception) as e:
            logger.warning(f"雪球搜索失败: {e}")
            return self._make_error("search", f"搜索失败: {e}")

    def read(self, url_or_id: str) -> NormalizedResult:
        """读取雪球股票/基金信息

        Args:
            url_or_id: 股票代码（如 SH600519）或雪球URL

        Returns:
            标准化读取结果
        """
        try:
            symbol = self._parse_symbol(url_or_id)
            cookies = self._get_cookies()

            # 获取股票详情
            params = {"symbol": symbol}
            data = get_json(
                f"{XUEQIU_API}/statuses/search.json",
                params=params,
                headers=self._get_headers(),
                cookies=cookies,
                timeout=15,
            )

            # 获取行情数据
            quote_data = get_json(
                f"{XUEQIU_API}/v4/stock/quote.json",
                params={"symbol": symbol},
                headers=self._get_headers(),
                cookies=cookies,
                timeout=15,
            )

            quote = quote_data.get("data", {}).get("quote", {})
            name = quote.get("name", symbol)
            current = quote.get("current", 0)
            high = quote.get("high", 0)
            low = quote.get("low", 0)
            open_price = quote.get("open", 0)
            volume = quote.get("volume", 0)
            market_capital = quote.get("market_capital", 0)
            chg = quote.get("chg", 0)
            percent = quote.get("percent", 0)

            # 构建内容
            content_parts = [
                f"# {name} ({symbol})",
                "",
                f"**当前价格**: {current}",
                f"**涨跌额**: {chg} ({percent}%)",
                f"**今开**: {open_price}",
                f"**最高**: {high}",
                f"**最低**: {low}",
                f"**成交量**: {volume:,}",
                f"**市值**: {market_capital:,.0f}",
            ]

            # 获取相关讨论
            statuses = data.get("list", []) if isinstance(data, dict) else []
            if statuses:
                content_parts.append("\n## 最新讨论")
                for i, status in enumerate(statuses[:10], 1):
                    user = status.get("user", {})
                    content_parts.append(
                        f"\n### {i}. {user.get('screen_name', '未知')}"
                    )
                    content_parts.append(status.get("text", "")[:200])

            return Normalizer.create_read_result(
                platform=self.platform,
                title=f"{name} ({symbol})",
                content="\n".join(content_parts),
                url=f"https://xueqiu.com/S/{symbol}",
                metadata={
                    "symbol": symbol,
                    "current": current,
                    "chg": chg,
                    "percent": percent,
                    "market_capital": market_capital,
                },
            )

        except (NetworkError, Exception) as e:
            logger.warning(f"雪球读取失败: {e}")
            return self._make_error("read", f"读取失败: {e}")

    def _parse_symbol(self, url_or_id: str) -> str:
        """解析股票代码"""
        url_or_id = url_or_id.strip().upper()

        # 从URL提取
        match = re.search(r"xueqiu\.com/S/([A-Z0-9]+)", url_or_id)
        if match:
            return match.group(1)

        # 如果已经是标准格式（如SH600519）
        if re.match(r"^(SH|SZ|BJ)\d{6}$", url_or_id):
            return url_or_id

        # 纯数字，尝试推断市场
        if url_or_id.isdigit():
            if url_or_id.startswith("6"):
                return f"SH{url_or_id}"
            elif url_or_id.startswith("0") or url_or_id.startswith("3"):
                return f"SZ{url_or_id}"
            else:
                return f"SH{url_or_id}"

        return url_or_id

    def check_health(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            cookies = self._get_cookies()
            data = get_json(
                f"{XUEQIU_API}/v4/stock/quote.json?symbol=SH600519",
                headers=self._get_headers(),
                cookies=cookies,
                timeout=10,
            )
            healthy = "data" in data
            return {
                "healthy": healthy,
                "message": "雪球API 可用" if healthy else "雪球API 返回异常",
                "details": {
                    "version": self.version,
                    "tier": self.tier,
                },
            }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"雪球API 不可用: {e}",
                "details": {"version": self.version, "tier": self.tier},
            }

    def get_dependencies(self) -> List[str]:
        return []

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "cookies": {
                "type": "dict",
                "description": "雪球Cookie（可选，自动获取）",
                "default": {},
            },
        }
