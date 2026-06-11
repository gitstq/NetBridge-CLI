"""GitHub插件 - 使用urllib调用GitHub REST API，零依赖

支持搜索仓库、用户、代码，以及读取仓库信息和README。
"""

import json
from typing import Any, Dict, List, Optional

from .base import BasePlugin
from ..core.normalizer import NormalizedResult, Normalizer
from ..utils.network import get_json, get_text, NetworkError
from ..utils.logger import get_logger

logger = get_logger("netbridge.plugin.github")

# GitHub REST API
GITHUB_API = "https://api.github.com"
GITHUB_RAW = "https://raw.githubusercontent.com"


class GitHubPlugin(BasePlugin):
    """GitHub插件

    使用GitHub REST API进行搜索和读取，
    支持仓库、用户、Issue等资源的操作。
    """

    @property
    def name(self) -> str:
        return "github"

    @property
    def description(self) -> str:
        return "GitHub插件，支持仓库搜索、代码读取、Issue查看"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def tier(self) -> int:
        return 0  # 核心插件，零依赖

    @property
    def platform(self) -> str:
        return "github"

    def _get_token(self) -> str:
        """获取GitHub Token（从配置或环境变量）"""
        token = self.get_config_value("token", "")
        if not token:
            import os
            token = os.environ.get("GITHUB_TOKEN", "")
        return token

    def _get_headers(self) -> Dict[str, str]:
        """获取带认证的请求头"""
        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        token = self._get_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def search(self, query: str, limit: int = 10) -> NormalizedResult:
        """搜索GitHub内容

        支持仓库搜索（默认）和代码搜索。
        格式: "keyword" 或 "type:repos keyword" 或 "type:code keyword"

        Args:
            query: 搜索关键词
            limit: 结果数量限制

        Returns:
            标准化搜索结果
        """
        try:
            # 解析搜索类型
            search_type = "repositories"
            search_query = query

            if query.startswith("type:"):
                parts = query.split(None, 1)
                if len(parts) == 2:
                    type_map = {
                        "repos": "repositories",
                        "repo": "repositories",
                        "code": "code",
                        "users": "users",
                        "user": "users",
                        "issues": "issues",
                        "issue": "issues",
                    }
                    search_type = type_map.get(parts[0].replace("type:", ""), "repositories")
                    search_query = parts[1]

            url = f"{GITHUB_API}/search/{search_type}"
            params = {
                "q": search_query,
                "per_page": min(limit, 30),
                "sort": "stars" if search_type == "repositories" else "updated",
            }

            data = get_json(url, params=params, headers=self._get_headers(), timeout=15)
            items = data.get("items", [])

            results = []
            for item in items[:limit]:
                if search_type == "repositories":
                    results.append({
                        "title": item.get("full_name", ""),
                        "url": item.get("html_url", ""),
                        "snippet": item.get("description", "") or "",
                        "author": item.get("owner", {}).get("login", ""),
                        "metadata": {
                            "stars": item.get("stargazers_count", 0),
                            "forks": item.get("forks_count", 0),
                            "language": item.get("language", ""),
                            "updated_at": item.get("updated_at", ""),
                        },
                    })
                elif search_type == "code":
                    results.append({
                        "title": item.get("name", ""),
                        "url": item.get("html_url", ""),
                        "snippet": item.get("text_matches", [{}])[0].get("fragment", "")[:300] if item.get("text_matches") else "",
                        "author": item.get("repository", {}).get("full_name", ""),
                    })
                elif search_type == "users":
                    results.append({
                        "title": item.get("login", ""),
                        "url": item.get("html_url", ""),
                        "snippet": item.get("bio", "") or "",
                        "author": item.get("login", ""),
                        "metadata": {
                            "public_repos": item.get("public_repos", 0),
                            "followers": item.get("followers", 0),
                        },
                    })
                elif search_type == "issues":
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("html_url", ""),
                        "snippet": item.get("body", "")[:300] or "",
                        "author": item.get("user", {}).get("login", ""),
                        "published_at": item.get("created_at", ""),
                        "metadata": {
                            "state": item.get("state", ""),
                            "comments": item.get("comments", 0),
                        },
                    })

            return Normalizer.create_search_result(
                platform=self.platform,
                results=results,
                metadata={"total_count": data.get("total_count", 0)},
            )

        except (NetworkError, Exception) as e:
            logger.warning(f"GitHub搜索失败: {e}")
            return self._make_error("search", f"搜索失败: {e}")

    def read(self, url_or_id: str) -> NormalizedResult:
        """读取GitHub内容

        支持多种格式：
        - 完整URL: https://github.com/user/repo
        - 简写: user/repo
        - README: user/repo/readme

        Args:
            url_or_id: GitHub URL或仓库标识

        Returns:
            标准化读取结果
        """
        try:
            owner, repo, extra = self._parse_github_ref(url_or_id)

            if extra and extra.lower() == "readme":
                return self._read_readme(owner, repo)
            elif extra:
                return self._read_file(owner, repo, extra)
            else:
                return self._read_repo(owner, repo)

        except (NetworkError, Exception) as e:
            logger.warning(f"GitHub读取失败: {e}")
            return self._make_error("read", f"读取失败: {e}")

    def _parse_github_ref(self, ref: str) -> tuple:
        """解析GitHub引用

        Returns:
            (owner, repo, extra_path)
        """
        ref = ref.strip().rstrip("/")

        # 处理完整URL
        if "github.com" in ref:
            parts = ref.split("github.com")[-1].strip("/").split("/")
            parts = [p for p in parts if p]
            owner = parts[0] if len(parts) > 0 else ""
            repo = parts[1] if len(parts) > 1 else ""
            extra = "/".join(parts[2:]) if len(parts) > 2 else ""
            return owner, repo, extra

        # 处理 user/repo 格式
        parts = ref.split("/")
        owner = parts[0] if len(parts) > 0 else ""
        repo = parts[1] if len(parts) > 1 else ""
        extra = "/".join(parts[2:]) if len(parts) > 2 else ""
        return owner, repo, extra

    def _read_repo(self, owner: str, repo: str) -> NormalizedResult:
        """读取仓库信息"""
        url = f"{GITHUB_API}/repos/{owner}/{repo}"
        data = get_json(url, headers=self._get_headers(), timeout=10)

        content_parts = [
            f"# {data.get('full_name', '')}",
            "",
            data.get("description", "") or "无描述",
            "",
            f"- Stars: {data.get('stargazers_count', 0)}",
            f"- Forks: {data.get('forks_count', 0)}",
            f"- Language: {data.get('language', 'N/A')}",
            f"- License: {data.get('license', {}).get('name', 'N/A') if data.get('license') else 'N/A'}",
            f"- Created: {data.get('created_at', '')}",
            f"- Updated: {data.get('updated_at', '')}",
            "",
            f"Topics: {', '.join(data.get('topics', [])) or 'None'}",
        ]

        return Normalizer.create_read_result(
            platform=self.platform,
            title=data.get("full_name", ""),
            content="\n".join(content_parts),
            url=data.get("html_url", ""),
            author=owner,
            published_at=data.get("created_at", ""),
            metadata={
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "open_issues": data.get("open_issues_count", 0),
                "language": data.get("language", ""),
                "default_branch": data.get("default_branch", "main"),
            },
        )

    def _read_readme(self, owner: str, repo: str) -> NormalizedResult:
        """读取仓库README"""
        url = f"{GITHUB_API}/repos/{owner}/{repo}/readme"
        headers = self._get_headers()
        headers["Accept"] = "application/vnd.github.raw+json"
        content = get_text(url, headers=headers, timeout=10)

        return Normalizer.create_read_result(
            platform=self.platform,
            title=f"{owner}/{repo} README",
            content=content,
            url=f"https://github.com/{owner}/{repo}#readme",
            author=owner,
        )

    def _read_file(self, owner: str, repo: str, path: str) -> NormalizedResult:
        """读取仓库中的文件"""
        url = f"{GITHUB_API}/repos/{owner}/{repo}/contents/{path}"
        headers = self._get_headers()
        headers["Accept"] = "application/vnd.github.raw+json"
        content = get_text(url, headers=headers, timeout=10)

        return Normalizer.create_read_result(
            platform=self.platform,
            title=f"{owner}/{repo}/{path}",
            content=content,
            url=f"https://github.com/{owner}/{repo}/blob/main/{path}",
            author=owner,
        )

    def check_health(self) -> Dict[str, Any]:
        """健康检查 - 测试GitHub API连通性"""
        try:
            data = get_json(
                f"{GITHUB_API}/rate_limit",
                headers=self._get_headers(),
                timeout=10,
            )
            remaining = data.get("rate", {}).get("remaining", 0)
            healthy = remaining > 0
            return {
                "healthy": healthy,
                "message": f"GitHub API 可用 (剩余请求: {remaining})",
                "details": {
                    "version": self.version,
                    "tier": self.tier,
                    "authenticated": bool(self._get_token()),
                    "rate_limit_remaining": remaining,
                },
            }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"GitHub API 不可用: {e}",
                "details": {"version": self.version, "tier": self.tier},
            }

    def get_dependencies(self) -> List[str]:
        return []

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "token": {
                "type": "string",
                "description": "GitHub Personal Access Token",
                "default": "",
            },
        }
