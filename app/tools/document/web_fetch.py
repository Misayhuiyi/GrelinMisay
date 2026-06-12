"""
============================================================================
网页内容抓取工具 - 获取URL对应的网页内容
============================================================================
异步HTTP请求，获取目标URL的文本内容，支持超时控制。
"""
import asyncio
from typing import Any, Dict
import aiohttp
from app.tools.base import BaseTool, validate_params
from app.core.logger import logger

# 允许抓取的域名白名单（安全策略）
_ALLOWED_DOMAINS = {
    "jsonplaceholder.typicode.com",
    "httpbin.org",
    "api.github.com",
}

# 限制抓取内容最大长度
_MAX_CONTENT_LENGTH = 5000


class WebFetchTool(BaseTool):
    """网页内容抓取工具 - 获取URL对应的文本内容"""

    @property
    def name(self) -> str:
        return "web_fetch"

    @property
    def description(self) -> str:
        return (
            "抓取指定URL的网页内容（仅文本类型）。"
            "适用场景：获取API返回数据、抓取公开网页信息。"
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "要抓取的URL地址（完整URL，如 https://example.com/api/data）"
                },
            },
            "required": ["url"],
        }

    @validate_params
    async def execute(self, url: str = "") -> str:
        """执行网页抓取"""
        from urllib.parse import urlparse

        # 解析 URL 以进行安全检查
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # 安全检查：只允许白名单域名
        if domain not in _ALLOWED_DOMAINS:
            return (
                f"出于安全策略限制，不允许抓取域名 '{domain}'。"
                f"当前允许的域名: {', '.join(sorted(_ALLOWED_DOMAINS))}"
            )

        timeout = aiohttp.ClientTimeout(total=10)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return f"请求失败，HTTP状态码: {response.status}"

                    content_type = response.headers.get("Content-Type", "")
                    content = await response.text()

                    # 只处理文本内容
                    if "json" in content_type:
                        # JSON 直接返回
                        if len(content) > _MAX_CONTENT_LENGTH:
                            content = content[:_MAX_CONTENT_LENGTH] + "\n...(内容已截断)"
                        return content
                    elif "html" in content_type or "text" in content_type:
                        # HTML/文本：简单去除标签
                        import re
                        text = re.sub(r"<[^>]+>", "", content)
                        text = re.sub(r"\s+", " ", text).strip()
                        if len(text) > _MAX_CONTENT_LENGTH:
                            text = text[:_MAX_CONTENT_LENGTH] + "\n...(内容已截断)"
                        return text
                    else:
                        return f"不支持的内容类型: {content_type}"

        except asyncio.TimeoutError:
            return "请求超时，目标服务器10秒内未响应。"
        except aiohttp.ClientError as e:
            return f"请求失败: {e}"
        except Exception as e:
            logger.error(f"[WebFetch] 未知错误: {e}")
            return f"抓取过程发生异常: {e}"

from app.tools.registry import tool_registry
tool_registry.register(WebFetchTool())
