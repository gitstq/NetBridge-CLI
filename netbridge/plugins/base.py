"""插件基类模块 - 定义所有插件的抽象接口

所有平台插件必须继承BasePlugin并实现其抽象方法。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..core.normalizer import NormalizedResult, Normalizer
from ..utils.logger import get_logger

logger = get_logger("netbridge.plugin")


class BasePlugin(ABC):
    """插件抽象基类

    所有平台插件必须继承此类并实现以下方法：
    - search(query, limit): 搜索内容
    - read(url_or_id): 读取内容
    - check_health(): 健康检查

    属性：
    - name: 插件名称
    - description: 插件描述
    - version: 插件版本
    - tier: 插件层级 (0=核心零依赖, 1=扩展可选依赖, 2=实验性)
    - platform: 平台标识
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化插件

        Args:
            config: 插件配置字典
        """
        self._config = config or {}

    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """插件描述"""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """插件版本"""
        ...

    @property
    @abstractmethod
    def tier(self) -> int:
        """插件层级

        0: 核心插件，零依赖
        1: 扩展插件，可选依赖
        2: 实验性插件
        """
        ...

    @property
    @abstractmethod
    def platform(self) -> str:
        """平台标识"""
        ...

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> NormalizedResult:
        """搜索内容

        Args:
            query: 搜索关键词
            limit: 结果数量限制

        Returns:
            标准化搜索结果
        """
        ...

    @abstractmethod
    def read(self, url_or_id: str) -> NormalizedResult:
        """读取内容

        Args:
            url_or_id: URL或内容ID

        Returns:
            标准化读取结果
        """
        ...

    def check_health(self) -> Dict[str, Any]:
        """健康检查

        Returns:
            健康状态字典，包含 healthy(bool) 和 message(str)
        """
        return {
            "healthy": True,
            "message": f"{self.name} 插件就绪",
            "details": {
                "version": self.version,
                "tier": self.tier,
            },
        }

    def install_deps(self) -> str:
        """安装插件依赖

        Returns:
            安装结果信息
        """
        deps = self.get_dependencies()
        if not deps:
            return "无需额外依赖"

        import subprocess
        import sys

        pip_args = [sys.executable, "-m", "pip", "install"] + deps
        try:
            subprocess.run(pip_args, check=True, capture_output=True, text=True)
            return f"已安装依赖: {', '.join(deps)}"
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"依赖安装失败: {e.stderr}")

    def get_dependencies(self) -> List[str]:
        """获取插件依赖列表

        Returns:
            pip包名列表
        """
        return []

    def get_config_schema(self) -> Dict[str, Any]:
        """获取配置模板

        Returns:
            配置字段描述字典
        """
        return {}

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取插件配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        return self._config.get(key, default)

    def _make_error(self, action: str, error: str) -> NormalizedResult:
        """创建错误结果（便捷方法）

        Args:
            action: 操作类型
            error: 错误信息

        Returns:
            标准化错误结果
        """
        return Normalizer.create_error_result(
            platform=self.platform,
            action=action,
            error=error,
        )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name!r}, tier={self.tier})>"
