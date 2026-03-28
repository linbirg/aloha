"""WebTool - 网页访问工具

提供安全的 HTTP 请求功能，支持域名白名单限制。
"""

import aiohttp
import asyncio
from urllib.parse import urlparse
from aloha.agent.tools import BaseTool, ToolResult


class WebTool(BaseTool):
    """网页访问工具

    支持 GET/POST 请求，可配置域名白名单。
    """

    def __init__(self, allowed_domains: list[str] | None = None, rate_limit: int = 10):
        super().__init__(
            name="web",
            description="访问网页并获取内容",
        )
        self.allowed_domains = allowed_domains or ["*"]
        self.rate_limit = rate_limit
        self._session: aiohttp.ClientSession | None = None
        self._request_count = 0
        self._last_reset: float | None = None

    def _get_last_reset(self) -> float:
        """延迟初始化 _last_reset"""
        if self._last_reset is None:
            self._last_reset = asyncio.get_event_loop().time()
        return self._last_reset

    def _set_last_reset(self, value: float):
        self._last_reset = value

    async def execute(self, url: str, method: str = "GET", data: str = "") -> ToolResult:
        """执行 HTTP 请求"""
        # 速率限制检查
        if not self._check_rate_limit():
            return ToolResult(
                success=False,
                content="",
                error=f"Rate limit exceeded: {self.rate_limit} requests per minute",
            )

        # URL 验证
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return ToolResult(success=False, content="", error="Invalid URL")

        # 域名检查
        if not self._is_domain_allowed(parsed.netloc):
            return ToolResult(
                success=False,
                content="",
                error=f"Domain not allowed: {parsed.netloc}",
            )

        try:
            if self._session is None:
                timeout = aiohttp.ClientTimeout(total=30)
                self._session = aiohttp.ClientSession(timeout=timeout)

            headers = {"User-Agent": "Aloha/1.0"}

            async with self._session.request(
                method, url, data=data if data else None, headers=headers
            ) as resp:
                content = await resp.text()

                # 限制返回内容长度
                if len(content) > 10000:
                    content = content[:10000] + "\n... (truncated)"

                result_content = f"Status: {resp.status}\nContent-Type: {resp.headers.get('Content-Type', 'unknown')}\n\n{content}"

                self._request_count += 1

                return ToolResult(
                    success=resp.status < 400,
                    content=result_content,
                    error=None if resp.status < 400 else f"HTTP {resp.status}",
                )

        except asyncio.TimeoutError:
            return ToolResult(success=False, content="", error="Request timed out")
        except aiohttp.ClientError as e:
            return ToolResult(success=False, content="", error=f"Client error: {str(e)}")
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))

    def _check_rate_limit(self) -> bool:
        """检查速率限制"""
        current_time = asyncio.get_event_loop().time()
        last_reset = self._get_last_reset()
        elapsed = current_time - last_reset

        # 每分钟重置计数器
        if elapsed > 60:
            self._request_count = 0
            self._set_last_reset(current_time)

        return self._request_count < self.rate_limit

    def _is_domain_allowed(self, domain: str) -> bool:
        """检查域名是否允许"""
        if "*" in self.allowed_domains:
            return True

        for allowed in self.allowed_domains:
            if domain == allowed or domain.endswith(f".{allowed}"):
                return True

        return False

    async def close(self):
        """关闭 session"""
        if self._session:
            await self._session.close()
            self._session = None

    def _get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "要访问的 URL",
                },
                "method": {
                    "type": "string",
                    "description": "HTTP 方法",
                    "enum": ["GET", "POST"],
                    "default": "GET",
                },
                "data": {
                    "type": "string",
                    "description": "POST 请求数据",
                },
            },
            "required": ["url"],
        }