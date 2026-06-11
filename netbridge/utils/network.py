"""网络请求工具模块 - 基于urllib的HTTP客户端封装，零依赖实现

提供GET/POST请求、JSON解析、错误处理等功能。
针对中国大陆网络环境做了超时和重试优化。
"""

import json
import ssl
import urllib.request
import urllib.parse
import urllib.error
from typing import Any, Optional, Dict, Union
from datetime import datetime

from .logger import get_logger

logger = get_logger("netbridge.network")

# 默认请求头
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "identity",
}

# 默认超时（秒）
DEFAULT_TIMEOUT = 15

# 默认重试次数
DEFAULT_RETRIES = 2


class NetBridgeError(Exception):
    """NetBridge基础异常类"""
    pass


class NetworkError(NetBridgeError):
    """网络请求异常"""

    def __init__(self, message: str, status_code: int = 0, url: str = ""):
        self.status_code = status_code
        self.url = url
        super().__init__(f"{message} (status={status_code}, url={url})")


class RateLimitError(NetworkError):
    """速率限制异常"""
    pass


class AuthError(NetworkError):
    """认证异常"""
    pass


def _create_ssl_context() -> ssl.SSLContext:
    """创建SSL上下文，兼容不同Python版本"""
    try:
        ctx = ssl.create_default_context()
        # 不验证证书（某些场景需要）
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    except Exception:
        return ssl._create_unverified_context()


def _merge_headers(headers: Optional[Dict[str, str]]) -> Dict[str, str]:
    """合并默认请求头和自定义请求头"""
    merged = DEFAULT_HEADERS.copy()
    if headers:
        merged.update(headers)
    return merged


def request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, str]] = None,
    data: Optional[Union[Dict[str, Any], str, bytes]] = None,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    cookies: Optional[Dict[str, str]] = None,
    ssl_verify: bool = False,
) -> bytes:
    """发送HTTP请求

    Args:
        url: 请求URL
        method: HTTP方法 (GET/POST/PUT/DELETE)
        headers: 自定义请求头
        params: URL查询参数
        data: 请求体数据
        timeout: 超时时间（秒）
        retries: 重试次数
        cookies: Cookie字典
        ssl_verify: 是否验证SSL证书

    Returns:
        响应体字节

    Raises:
        NetworkError: 网络请求失败
    """
    # 构建完整URL
    if params:
        query_string = urllib.parse.urlencode(params)
        url = f"{url}?{query_string}" if "?" not in url else f"{url}&{query_string}"

    # 处理请求体
    if data is not None and isinstance(data, dict):
        body = urllib.parse.urlencode(data).encode("utf-8")
    elif isinstance(data, str):
        body = data.encode("utf-8")
    elif isinstance(data, bytes):
        body = data
    else:
        body = None

    # 合并请求头
    req_headers = _merge_headers(headers)
    if body and isinstance(body, bytes):
        req_headers["Content-Type"] = "application/x-www-form-urlencoded"

    # 添加Cookie
    if cookies:
        cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items())
        req_headers["Cookie"] = cookie_str

    last_error = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, data=body, headers=req_headers, method=method)

            ctx = _create_ssl_context() if not ssl_verify else None
            response = urllib.request.urlopen(req, timeout=timeout, context=ctx)

            logger.debug(f"请求成功: {method} {url} -> {response.status}")
            return response.read()

        except urllib.error.HTTPError as e:
            status_code = e.code
            body_text = ""
            try:
                body_text = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass

            # 速率限制
            if status_code == 429:
                raise RateLimitError(
                    f"请求过于频繁，请稍后重试",
                    status_code=status_code,
                    url=url,
                )

            # 认证错误
            if status_code in (401, 403):
                raise AuthError(
                    f"认证失败: {body_text[:200]}",
                    status_code=status_code,
                    url=url,
                )

            last_error = NetworkError(
                f"HTTP错误: {body_text[:200]}",
                status_code=status_code,
                url=url,
            )
            logger.warning(f"HTTP {status_code} (尝试 {attempt + 1}/{retries + 1}): {url}")

        except urllib.error.URLError as e:
            last_error = NetworkError(f"URL错误: {e.reason}", url=url)
            logger.warning(f"URL错误 (尝试 {attempt + 1}/{retries + 1}): {url} - {e.reason}")

        except TimeoutError:
            last_error = NetworkError(f"请求超时 ({timeout}s)", url=url)
            logger.warning(f"超时 (尝试 {attempt + 1}/{retries + 1}): {url}")

        except Exception as e:
            last_error = NetworkError(f"未知错误: {e}", url=url)
            logger.warning(f"未知错误 (尝试 {attempt + 1}/{retries + 1}): {url} - {e}")

    raise last_error or NetworkError(f"请求失败: {url}")


def get(
    url: str,
    params: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = DEFAULT_TIMEOUT,
    **kwargs: Any,
) -> bytes:
    """发送GET请求"""
    return request(url, method="GET", params=params, headers=headers, timeout=timeout, **kwargs)


def post(
    url: str,
    data: Optional[Union[Dict[str, Any], str, bytes]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = DEFAULT_TIMEOUT,
    **kwargs: Any,
) -> bytes:
    """发送POST请求"""
    return request(url, method="POST", data=data, headers=headers, timeout=timeout, **kwargs)


def get_json(
    url: str,
    params: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = DEFAULT_TIMEOUT,
    **kwargs: Any,
) -> Any:
    """发送GET请求并解析JSON响应

    Args:
        url: 请求URL
        params: URL查询参数
        headers: 自定义请求头
        timeout: 超时时间

    Returns:
        解析后的JSON对象

    Raises:
        NetworkError: 请求失败或JSON解析失败
    """
    raw = get(url, params=params, headers=headers, timeout=timeout, **kwargs)
    try:
        return json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise NetworkError(f"JSON解析失败: {e}", url=url)


def post_json(
    url: str,
    data: Optional[Union[Dict[str, Any], str, bytes]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = DEFAULT_TIMEOUT,
    **kwargs: Any,
) -> Any:
    """发送POST请求并解析JSON响应"""
    raw = post(url, data=data, headers=headers, timeout=timeout, **kwargs)
    try:
        return json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise NetworkError(f"JSON解析失败: {e}", url=url)


def get_text(
    url: str,
    params: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = DEFAULT_TIMEOUT,
    **kwargs: Any,
) -> str:
    """发送GET请求并返回文本响应"""
    raw = get(url, params=params, headers=headers, timeout=timeout, **kwargs)
    return raw.decode("utf-8", errors="replace")
