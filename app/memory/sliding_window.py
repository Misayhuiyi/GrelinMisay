"""
============================================================================
滑动窗口策略 - 控制上下文中保留的消息数量
============================================================================
双窗口策略：
  1. 近距窗口：保留最近 N 轮完整消息（用户+AI+工具结果）
  2. 系统消息：始终保留（System Prompt、工具描述等）

当消息数超过窗口限制时，自动丢弃最早的消息，确保Token不超限。
"""
from typing import List, Dict
from app.core.config import get_settings

settings = get_settings()


class SlidingWindow:
    """
    滑动窗口管理器。
    - 维护消息列表，自动裁剪到指定大小。
    - 系统消息（role='system'）始终保留，只裁剪 user/assistant/tool 消息。
    """

    def __init__(self, window_size: int = None):
        """
        初始化滑动窗口。
        Args:
            window_size: 窗口大小（保留的最近消息数），默认从配置读取
        """
        self.window_size = window_size or settings.MEMORY_WINDOW_SIZE
        self._messages: List[Dict[str, str]] = []

    @property
    def messages(self) -> List[Dict[str, str]]:
        """获取当前窗口内的所有消息"""
        return self._messages

    def add(self, message: Dict[str, str]) -> None:
        """添加一条新消息"""
        self._messages.append(message)
        self._trim()

    def add_many(self, messages: List[Dict[str, str]]) -> None:
        """批量添加消息"""
        self._messages.extend(messages)
        self._trim()

    def _trim(self) -> None:
        """
        裁剪消息，使非系统消息数量不超过 window_size。
        系统消息永久保留，不受窗口限制。
        """
        system_msgs = [m for m in self._messages if m.get("role") == "system"]
        other_msgs = [m for m in self._messages if m.get("role") != "system"]

        # 裁剪：只保留最近的 window_size 条非系统消息
        if len(other_msgs) > self.window_size:
            other_msgs = other_msgs[-self.window_size:]

        # 重组：系统消息在前
        self._messages = system_msgs + other_msgs

    def get_token_estimate(self) -> int:
        """
        估算当前窗口的 Token 总量。
        简单估算：每字符约 0.5 Token（中英文混合估算）。
        """
        total_chars = sum(len(m.get("content") or "") for m in self._messages)
        return int(total_chars * 0.5)

    def clear(self) -> None:
        """清空所有消息"""
        self._messages = []

    def reset_system(self, system_prompt: str) -> None:
        """重置系统提示词（移除旧的，设置新的）"""
        self._messages = [m for m in self._messages if m.get("role") != "system"]
        if system_prompt:
            self._messages.insert(0, {"role": "system", "content": system_prompt})

    def to_api_format(self) -> List[Dict[str, str]]:
        """转换为 LLM API 兼容的消息格式，保留所有字段（包括 tool_calls, tool_call_id 等）"""
        return [dict(m) for m in self._messages]

    def __len__(self) -> int:
        return len(self._messages)
