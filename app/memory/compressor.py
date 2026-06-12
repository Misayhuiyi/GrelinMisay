"""
============================================================================
历史关键信息提取压缩模块 - 解决长对话Token超限问题
============================================================================
策略：
  1. 当对话超过阈值时，提取历史中的关键事实/决策/数值。
  2. 将压缩后的摘要注入到 system 消息中，替换冗长的历史消息。
  3. 保留最近几轮的完整对话，确保上下文连贯性。

压缩流程：
  历史消息 → 提取关键信息（用轻量级规则） → 生成摘要 → 替换旧消息
"""
import re
from typing import List, Dict, Optional
from app.core.config import get_settings
from app.core.logger import logger

settings = get_settings()


class HistoryCompressor:
    """
    历史关键信息提取压缩器。
    当对话消息超过 Token 阈值时，对较早历史进行压缩：
    - 提取用户的问题意图
    - 提取AI的最终结论/回答摘要
    - 提取工具调用的关键结果
    - 丢弃中间推理过程
    """

    # 压缩后的摘要最大长度（字符数）
    MAX_SUMMARY_LENGTH = 1000

    def __init__(self, max_tokens: int = None):
        self.max_tokens = max_tokens or settings.MEMORY_MAX_TOKENS

    def should_compress(self, messages: List[Dict[str, str]]) -> bool:
        """
        判断是否需要压缩。
        条件：总Token估算超过 max_tokens，且消息数 > 8。
        """
        if not settings.MEMORY_COMPRESSION_ENABLED:
            return False
        total_chars = sum(len(m.get("content") or "") for m in messages)
        estimated_tokens = int(total_chars * 0.5)
        return estimated_tokens > self.max_tokens and len(messages) > 8

    def compress(
        self, messages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        压缩历史消息。
        返回压缩后的消息列表：
        [system(含摘要)] + [最近N条完整消息]

        保留策略：
        - 保留最近6条消息（约3轮对话）的完整内容
        - 其余历史消息提取关键信息压缩为摘要
        """
        if not self.should_compress(messages):
            return messages

        logger.info(f"[记忆压缩] 开始压缩 {len(messages)} 条消息")

        # 分离系统消息
        system_msgs = [m for m in messages if m.get("role") == "system"]
        other_msgs = [m for m in messages if m.get("role") != "system"]

        # 保留最近6条完整消息
        keep_count = min(6, len(other_msgs))
        recent_msgs = other_msgs[-keep_count:]
        old_msgs = other_msgs[:-keep_count]

        if not old_msgs:
            return messages

        # 提取关键信息摘要
        summary = self._extract_key_info(old_msgs)

        # 构建压缩后的 system 消息
        compressed_system = {
            "role": "system",
            "content": (
                f"[历史对话摘要]\n"
                f"以下是之前对话的关键信息总结（完整对话已省略以节省Token）：\n"
                f"{summary}\n"
                f"[摘要结束] 以下为最近对话内容："
            )
        }

        # 组合：system消息 + 压缩摘要 + 最近消息
        result = system_msgs + [compressed_system] + recent_msgs
        logger.info(
            f"[记忆压缩] 完成: {len(messages)} → {len(result)} 条消息"
        )
        return result

    def _extract_key_info(self, messages: List[Dict[str, str]]) -> str:
        """
        从历史消息中提取关键信息。
        规则驱动（轻量级，不需要调用LLM）：
        - 提取用户明确的问题/指令
        - 提取包含"结论"/"结果"/"最终"等关键词的AI回复
        - 提取工具调用返回的数值/事实
        """
        summary_parts = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content") or ""

            # 截断过长内容
            if len(content) > 300:
                content = content[:300] + "..."

            if role == "user":
                # 用户消息：提取问题意图
                summary_parts.append(f"[用户提问] {content}")

            elif role == "assistant":
                # AI消息：提取结论性内容
                if any(kw in content for kw in ["最终", "结论", "总结", "答案", "结果"]):
                    summary_parts.append(f"[AI结论] {self._truncate(content, 200)}")
                elif "Observation" in content:
                    # 包含观察结果的推理
                    summary_parts.append(f"[AI推理摘要] {self._truncate(content, 150)}")

            elif role == "tool":
                # 工具结果：提取关键数据
                summary_parts.append(f"[工具结果] {self._truncate(content, 200)}")

        # 合并摘要
        if not summary_parts:
            return "（无关键信息可提取）"

        summary = " | ".join(summary_parts[:8])  # 最多保留8条
        return self._truncate(summary, self.MAX_SUMMARY_LENGTH)

    @staticmethod
    def _truncate(text: str, max_len: int) -> str:
        """截断文本，保持语义完整"""
        if len(text) <= max_len:
            return text
        return text[:max_len - 3] + "..."
