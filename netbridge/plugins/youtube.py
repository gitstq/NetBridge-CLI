"""YouTube插件 - 使用yt-dlp提取视频信息和字幕

可选依赖：yt-dlp
"""

import json
import subprocess
import sys
from typing import Any, Dict, List, Optional

from .base import BasePlugin
from ..core.normalizer import NormalizedResult, Normalizer
from ..utils.logger import get_logger

logger = get_logger("netbridge.plugin.youtube")


class YouTubePlugin(BasePlugin):
    """YouTube视频插件

    使用yt-dlp提取视频信息、字幕和元数据。
    """

    @property
    def name(self) -> str:
        return "youtube"

    @property
    def description(self) -> str:
        return "YouTube视频插件，支持视频信息提取和字幕获取"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def tier(self) -> int:
        return 1  # 扩展插件，可选依赖

    @property
    def platform(self) -> str:
        return "youtube"

    def _run_yt_dlp(self, args: List[str]) -> str:
        """运行yt-dlp命令并返回输出"""
        try:
            import yt_dlp
        except ImportError:
            raise RuntimeError(
                "需要安装yt-dlp依赖，请运行: pip install yt-dlp"
            )

        cmd = [sys.executable, "-m", "yt_dlp"] + args
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            raise RuntimeError(f"yt-dlp执行失败: {result.stderr}")
        return result.stdout

    def _extract_info(self, url: str) -> Dict[str, Any]:
        """使用yt-dlp提取视频信息"""
        try:
            import yt_dlp
        except ImportError:
            raise RuntimeError("需要安装yt-dlp依赖")

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "skip_download": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info

    def _parse_video_id(self, url_or_id: str) -> str:
        """解析视频ID"""
        url_or_id = url_or_id.strip()

        # 纯ID（11位字母数字）
        if len(url_or_id) == 11 and url_or_id.isalnum():
            return url_or_id

        # 从URL提取ID
        import re
        patterns = [
            r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
            r"youtube\.com/shorts/([a-zA-Z0-9_-]{11})",
        ]
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)

        return url_or_id

    def search(self, query: str, limit: int = 10) -> NormalizedResult:
        """搜索YouTube视频

        Args:
            query: 搜索关键词
            limit: 结果数量限制

        Returns:
            标准化搜索结果
        """
        try:
            info = self._extract_info(f"ytsearch{limit}:{query}")

            results = []
            entries = info.get("entries", [])
            for entry in entries:
                if entry is None:
                    continue
                results.append({
                    "title": entry.get("title", ""),
                    "url": entry.get("webpage_url", entry.get("url", "")),
                    "snippet": entry.get("description", "")[:300],
                    "author": entry.get("uploader", entry.get("channel", "")),
                    "published_at": entry.get("upload_date", ""),
                    "metadata": {
                        "duration": entry.get("duration", 0),
                        "view_count": entry.get("view_count", 0),
                        "thumbnail": entry.get("thumbnail", ""),
                    },
                })

            return Normalizer.create_search_result(
                platform=self.platform,
                results=results,
            )

        except RuntimeError as e:
            return self._make_error("search", str(e))
        except Exception as e:
            logger.warning(f"YouTube搜索失败: {e}")
            return self._make_error("search", f"搜索失败: {e}")

    def read(self, url_or_id: str) -> NormalizedResult:
        """读取YouTube视频信息

        Args:
            url_or_id: 视频URL或ID

        Returns:
            标准化读取结果
        """
        try:
            video_id = self._parse_video_id(url_or_id)
            url = f"https://www.youtube.com/watch?v={video_id}"

            info = self._extract_info(url)

            # 构建内容
            content_parts = [
                f"# {info.get('title', '')}",
                "",
                f"**频道**: {info.get('uploader', '未知')}",
                f"**时长**: {self._format_duration(info.get('duration', 0))}",
                f"**观看次数**: {info.get('view_count', 0):,}",
                f"**点赞数**: {info.get('like_count', 0):,}",
                f"**发布日期**: {info.get('upload_date', '')}",
                "",
                "## 描述",
                info.get("description", "无描述"),
            ]

            # 尝试获取字幕
            subtitles = info.get("subtitles", {})
            auto_subs = info.get("automatic_captions", {})
            all_subs = {**subtitles, **auto_subs}

            if all_subs:
                content_parts.append("\n## 字幕")
                # 优先中文，其次英文
                for lang in ["zh-Hans", "zh", "zh-CN", "en", "en-US"]:
                    if lang in all_subs:
                        sub_list = all_subs[lang]
                        if sub_list:
                            sub_url = sub_list[0].get("url", "")
                            if sub_url:
                                try:
                                    from ..utils.network import get_text
                                    sub_content = get_text(sub_url, timeout=15)
                                    # 解析SRT/VTT字幕
                                    sub_text = self._parse_subtitle(sub_content)
                                    if sub_text:
                                        content_parts.append(f"\n### 字幕 ({lang})")
                                        content_parts.append(sub_text[:5000])
                                except Exception:
                                    pass
                            break

            return Normalizer.create_read_result(
                platform=self.platform,
                title=info.get("title", ""),
                content="\n".join(content_parts),
                url=url,
                author=info.get("uploader", ""),
                published_at=info.get("upload_date", ""),
                metadata={
                    "video_id": video_id,
                    "duration": info.get("duration", 0),
                    "view_count": info.get("view_count", 0),
                    "like_count": info.get("like_count", 0),
                    "categories": info.get("categories", []),
                    "tags": info.get("tags", []),
                },
            )

        except RuntimeError as e:
            return self._make_error("read", str(e))
        except Exception as e:
            logger.warning(f"YouTube读取失败: {e}")
            return self._make_error("read", f"读取失败: {e}")

    def _format_duration(self, seconds: int) -> str:
        """格式化时长"""
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    def _parse_subtitle(self, content: str) -> str:
        """解析字幕文本（SRT/VTT格式）"""
        lines = content.strip().split("\n")
        text_lines = []
        for line in lines:
            line = line.strip()
            # 跳过序号和时间戳行
            if line.isdigit():
                continue
            if "-->" in line:
                continue
            if line and not line.startswith(("WEBVTT", "Kind:", "Language:")):
                # 清理HTML标签
                import re
                clean = re.sub(r"<[^>]+>", "", line)
                if clean.strip():
                    text_lines.append(clean.strip())
        return " ".join(text_lines)

    def check_health(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            import yt_dlp
            return {
                "healthy": True,
                "message": f"yt-dlp 已安装 (版本: {yt_dlp.version.__version__})",
                "details": {
                    "version": self.version,
                    "tier": self.tier,
                    "yt_dlp_version": yt_dlp.version.__version__,
                },
            }
        except ImportError:
            return {
                "healthy": False,
                "message": "yt-dlp 未安装，请运行: pip install yt-dlp",
                "details": {"version": self.version, "tier": self.tier},
            }

    def get_dependencies(self) -> List[str]:
        return ["yt-dlp"]

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "subtitle_lang": {
                "type": "string",
                "description": "首选字幕语言",
                "default": "zh-Hans",
            },
        }
