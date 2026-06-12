"""
LLM 包装器
封装 LangChain ChatOpenAI，提供重试、超时、错误分类功能
"""
import asyncio
import json
from typing import List, Dict, Optional, Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
    AIMessage,
    ToolMessage,
)

from app.core.config import get_settings
from app.core.exceptions import (
    LLMTimeoutError,
    LLMAuthError,
    LLMRateLimitError,
    LLMError,
)
from app.core.logger import logger


class LLMWrapper:
    """LLM 调用包装器，处理重试、超时、错误分类和消息格式转换"""

    def __init__(self):
        settings = get_settings()
        self._settings = settings
        self.model = ChatOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_API_BASE,
            model=settings.LLM_MODEL_NAME,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
        )
        self.request_timeout = settings.LLM_REQUEST_TIMEOUT
        self.max_retries = settings.LLM_MAX_RETRIES
        self.retry_delay = settings.LLM_RETRY_DELAY

    async def invoke(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict]] = None,
    ) -> AIMessage:
        """调用 LLM，带重试逻辑"""
        langchain_msgs = self._convert_messages(messages)
        invoke_kwargs = {"input": langchain_msgs}
        if tools:
            invoke_kwargs["tools"] = tools

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = await asyncio.wait_for(
                    self.model.ainvoke(**invoke_kwargs),
                    timeout=self.request_timeout,
                )
                return response
            except asyncio.TimeoutError:
                last_error = LLMTimeoutError("LLM 请求超时")
            except Exception as e:
                error_str = str(e)
                if "401" in error_str or "Unauthorized" in error_str:
                    last_error = LLMAuthError(f"LLM 认证失败: {e}")
                elif "429" in error_str or "Rate limit" in error_str:
                    last_error = LLMRateLimitError(f"LLM 速率限制: {e}")
                else:
                    last_error = e
            except BaseException:
                pass

            if attempt < self.max_retries:
                logger.warning(
                    "LLM调用失败 (attempt=%d/%d): %s",
                    attempt,
                    self.max_retries,
                    last_error,
                )
                await asyncio.sleep(self.retry_delay * attempt)

        # 如果所有重试都失败，根据错误类型抛出
        if isinstance(last_error, (LLMTimeoutError, LLMAuthError, LLMRateLimitError)):
            raise last_error
        raise LLMError(f"LLM调用失败，已重试{self.max_retries}次")

    @staticmethod
    def _convert_messages(messages: List[Dict[str, Any]]) -> List[BaseMessage]:
        """将字典格式消息转为 LangChain 消息对象"""
        role_map = {
            "system": SystemMessage,
            "user": HumanMessage,
            "assistant": AIMessage,
            "tool": ToolMessage,
        }
        converted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content") or ""
            msg_cls = role_map.get(role, HumanMessage)
            if role == "tool":
                converted.append(ToolMessage(
                    content=content,
                    tool_call_id=msg.get("tool_call_id", "unknown"),
                ))
            elif role == "assistant" and msg.get("tool_calls"):
                lc_tool_calls = []
                for tc in msg["tool_calls"]:
                    fn = tc.get("function", {})
                    lc_tool_calls.append({
                        "id": tc.get("id", ""),
                        "name": fn.get("name", ""),
                        "args": (
                            json.loads(fn["arguments"])
                            if isinstance(fn.get("arguments"), str)
                            else fn.get("arguments", {})
                        ),
                        "type": "tool_call",
                    })
                converted.append(AIMessage(content=content, tool_calls=lc_tool_calls))
            else:
                converted.append(msg_cls(content=content))
        return converted

    @staticmethod
    def extract_tool_calls(response: AIMessage) -> List[Dict[str, Any]]:
        """从 AIMessage 中提取 tool_calls 列表"""
        tool_calls = response.tool_calls or []
        return [
            {
                "name": tc.get("name", ""),
                "args": tc.get("args", {}),
                "id": tc.get("id", ""),
            }
            for tc in tool_calls
        ]

    @staticmethod
    def get_text_content(response: AIMessage) -> str:
        """获取 AIMessage 的文本内容"""
        content = response.content
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = [
                p.get("text", "")
                for p in content
                if isinstance(p, dict) and p.get("type") == "text"
            ]
            return "".join(parts)
        return ""


# 全局单例
llm_wrapper = LLMWrapper()
