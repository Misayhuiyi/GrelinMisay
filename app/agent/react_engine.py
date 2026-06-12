"""
============================================================================
ReAct 推理引擎 - 手写实现 Thought-Action-Observation 循环
============================================================================
核心设计（不使用 LangChain 封装的 Agent）：
  1. 迭代循环：每轮 LLM 调用 → 解析输出 → 执行工具 → 注入观测结果 → 下一轮
  2. CoT Prompt：每次调用 LLM 都注入结构化的 CoT 思维链提示
  3. 校验重试：LLM 输出不合法时自动重试（最多 max_retries 次）
  4. 记忆管理：每轮通过滑动窗口和压缩器管理上下文
  5. 持久化：每步执行结果写入数据库

终止条件：
  - LLM 输出 Final Answer
  - 超过 max_iterations 轮次
  - 遇到不可恢复的错误
"""
import json
import time
import asyncio
from typing import Dict, Any, Optional, Callable
from langchain_core.messages import AIMessage, ToolMessage

from app.core.config import get_settings
from app.core.logger import logger
from app.core.exceptions import (
    AgentError, AgentMaxIterationsError,
)
from app.models.llm import LLMWrapper, llm_wrapper
from app.tools.registry import ToolRegistry, tool_registry
from app.memory.sliding_window import SlidingWindow
from app.memory.compressor import HistoryCompressor
from app.agent.cot_prompt import (
    build_system_prompt,
    wrap_user_message,
    format_observation,
    get_retry_prompt,
)
from app.agent.validator import OutputValidator

settings = get_settings()


class ReActEngine:
    """
    ReAct 推理引擎核心。

    完整执行流程：
      1. 初始化上下文（SlidingWindow + Compressor）
      2. 构建 System Prompt（含CoT模板+工具描述）
      3. 用户消息注入
      4. ReAct循环：
         a. 调用LLM（带工具Schema）
         b. 解析输出（Validator）
         c. 如果 Final Answer → 结束循环
         d. 如果 Tool Call → 执行工具 → 注入Observation → 回到 a
      5. 返回最终结果
    """

    def __init__(
        self,
        llm: LLMWrapper = None,
        registry: ToolRegistry = None,
    ):
        self.llm = llm or llm_wrapper
        self.registry = registry or tool_registry
        self.validator = OutputValidator(self.registry)
        self.max_iterations = settings.REACT_MAX_ITERATIONS
        self.max_retries = settings.REACT_MAX_RETRIES

        # 回调钩子（用于持久化记录）
        self._on_tool_call: Optional[Callable] = None
        self._on_execution_log: Optional[Callable] = None

    # ==================== 主入口 ====================

    async def run(
        self,
        user_message: str,
        conversation_history: list = None,
        on_tool_call: Callable = None,
        on_execution_log: Callable = None,
    ) -> Dict[str, Any]:
        """
        执行 ReAct 推理的完整流程。

        Args:
            user_message: 用户输入消息
            conversation_history: 历史消息列表 [{"role": ..., "content": ...}]
            on_tool_call: 工具调用回调 (tool_name, params, result, status, duration)
            on_execution_log: 执行日志回调 (iteration, thought, action, action_input, observation, duration)

        Returns:
            {"answer": str, "steps": [...], "tool_calls_count": int, "total_duration_ms": int}
        """
        self._on_tool_call = on_tool_call
        self._on_execution_log = on_execution_log

        start_time = time.time()

        # ---------- Step 1: 初始化记忆窗口 ----------
        window = SlidingWindow()

        # 注入 System Prompt（含CoT模板 + 工具描述）
        tools_desc = self.registry.get_prompt_descriptions()
        system_prompt = build_system_prompt(tools_desc)
        window.reset_system(system_prompt)

        # 注入历史对话
        if conversation_history:
            window.add_many(conversation_history)

        # 注入用户消息（CoT引导格式）
        wrapped_msg = wrap_user_message(user_message)
        window.add({"role": "user", "content": wrapped_msg})

        # ---------- Step 2: 初始化压缩器 ----------
        compressor = HistoryCompressor()

        # ---------- Step 3: ReAct 循环 ----------
        reaction_steps = []
        tool_calls_count = 0
        final_answer = ""

        for iteration in range(1, self.max_iterations + 1):
            iter_start = time.time()
            logger.info(f"[ReAct] 第 {iteration} 轮推理开始")
            logger.debug(f"[ReAct] 当前上下文消息数: {len(window)}, Token估算: {window.get_token_estimate()}")

            # 记忆压缩检查
            compressed = compressor.compress(window.messages)
            if compressed is not window.messages:
                # 重建窗口内容
                window.clear()
                window.add_many(compressed)
                logger.info(f"[ReAct] 已压缩记忆, 消息数: {len(window)}")

            # ----- 调用 LLM -----
            tool_schemas = self.registry.get_openai_schemas()
            llm_response, parse_result, retry_count = await self._call_llm_with_retry(
                window, tool_schemas
            )

            if parse_result is None:
                # 无法解析，但已经重试过了，跳过本轮
                logger.error(f"[ReAct] 第 {iteration} 轮输出无法解析，跳过")
                continue

            parse_type = parse_result["type"]
            thought = parse_result.get("thought", "")

            # 追加 assistant 消息到窗口（保留 tool_calls 以便后续 tool 消息配对）
            assistant_content = llm_response.content if llm_response else ""
            assistant_msg = {"role": "assistant", "content": assistant_content}
            if parse_type == "tool_call" and "raw_tool_calls" in parse_result:
                assistant_msg["tool_calls"] = parse_result["raw_tool_calls"]
                # 如果 content 为空，DeepSeek API 要求 content 为 null 或省略
                if not assistant_content:
                    assistant_msg["content"] = None
            window.add(assistant_msg)

            # ----- 检查是否 Final Answer -----
            if parse_type == "final_answer":
                final_answer = parse_result["final_answer"]
                iter_duration = int((time.time() - iter_start) * 1000)

                reaction_steps.append({
                    "iteration": iteration,
                    "thought": thought,
                    "action": "final_answer",
                    "action_input": {},
                    "observation": final_answer,
                    "duration_ms": iter_duration,
                })

                logger.info(f"[ReAct] 第 {iteration} 轮: 最终答案")
                await self._log_step(iteration, thought, "final_answer", {}, final_answer, iter_duration)
                break

            # ----- 工具调用 -----
            if parse_type == "tool_call":
                action = parse_result["action"]
                action_input = parse_result.get("action_input", {})

                # 执行工具
                tool_result = await self.registry.call_tool(action, **action_input)
                observation = (
                    f"成功: {tool_result['result']}"
                    if tool_result["success"]
                    else f"失败: {tool_result['result']}"
                )
                tool_duration = tool_result["duration_ms"]
                tool_calls_count += 1

                # 注入 Observation 到窗口（必须包含 tool_call_id 与 assistant 的 tool_calls 配对）
                obs_content = format_observation(action, action_input, observation)
                tool_msg = {"role": "tool", "content": obs_content}
                if "raw_tool_calls" in parse_result:
                    tc_list = parse_result["raw_tool_calls"]
                    if tc_list and "id" in tc_list[0]:
                        tool_msg["tool_call_id"] = tc_list[0]["id"]
                window.add(tool_msg)

                iter_duration = int((time.time() - iter_start) * 1000)

                reaction_steps.append({
                    "iteration": iteration,
                    "thought": thought,
                    "action": action,
                    "action_input": action_input,
                    "observation": observation,
                    "duration_ms": iter_duration,
                })

                # 持久化记录
                await self._log_step(iteration, thought, action, action_input, observation, iter_duration)
                await self._log_tool_call(action, action_input, observation, tool_result["success"], tool_duration)

                logger.info(
                    f"[ReAct] 第 {iteration} 轮: Action={action}, "
                    f"Success={tool_result['success']}, Duration={iter_duration}ms"
                )

        # ---------- Step 4: 收尾处理 ----------
        total_duration = int((time.time() - start_time) * 1000)

        if not final_answer:
            # 超过最大迭代次数仍未得出最终答案
            final_answer = (
                f"抱歉，我尝试了 {self.max_iterations} 轮推理但未能完成任务。"
                f"已执行了 {tool_calls_count} 次工具调用。"
                f"最后一轮思考: {thought}"
            )
            logger.warning(
                f"[ReAct] 达到最大迭代次数 ({self.max_iterations})，强制终止"
            )

        return {
            "answer": final_answer,
            "steps": reaction_steps,
            "tool_calls_count": tool_calls_count,
            "total_duration_ms": total_duration,
        }

    # ==================== LLM 调用 + 校验重试 ====================

    async def _call_llm_with_retry(
        self, window: SlidingWindow, tool_schemas: list
    ) -> tuple:
        """
        带校验重试的 LLM 调用。
        如果输出格式不合法，追加错误提示后重试（最多 max_retries 次）。
        Returns:
            (AIMessage, parsed_dict, retry_count)
        """
        retry_count = 0

        for attempt in range(1, self.max_retries + 1):
            try:
                messages = window.to_api_format()
                # 调试：打印消息角色序列和是否有 tool_calls
                roles = []
                for i, m in enumerate(messages):
                    role = m.get("role", "?")
                    has_tc = "tc" if m.get("tool_calls") else ""
                    has_tci = f"tci={m.get('tool_call_id','')}" if m.get("tool_call_id") else ""
                    extra = f"[{has_tc}{has_tci}]".strip("[]") or ""
                    roles.append(f"{role}{extra}")
                logger.debug(f"[ReAct] 消息序列: {' → '.join(roles)}")
                response = await self.llm.invoke(messages, tools=tool_schemas)

                # 优先检查 tool_calls（OpenAI 函数调用模式）
                tool_calls = self.llm.extract_tool_calls(response)
                if tool_calls:
                    # LLM 通过 tool_calls 方式请求调用工具
                    tc = tool_calls[0]
                    # 转换 LangChain tool_calls 格式 → OpenAI API 格式
                    # 注意：只保留当前执行的 tool_call，否则 assistant 消息有多个 tool_calls
                    # 但只跟一条 tool 消息会导致 API 报错
                    raw_tool_calls = [{
                        "id": tc.get("id", ""),
                        "type": "function",
                        "function": {
                            "name": tc.get("name", ""),
                            "arguments": json.dumps(tc.get("args", {}), ensure_ascii=False)
                        }
                    }]
                    parsed = {
                        "type": "tool_call",
                        "thought": response.content if isinstance(response.content, str) else "",
                        "action": tc["name"],
                        "action_input": tc["args"],
                        "raw_tool_calls": raw_tool_calls,
                    }
                    return response, parsed, retry_count

                # 否则从文本内容解析
                text_content = self.llm.get_text_content(response)
                valid, parsed, error_msg = self.validator.validate_and_parse(
                    text_content
                )

                if valid:
                    return response, parsed, retry_count

                # 校验失败，准备重试
                retry_count = attempt
                logger.warning(
                    f"[ReAct] 输出校验失败 (attempt={attempt}/{self.max_retries}): {error_msg}"
                )

                # 追加错误提示到消息窗口
                retry_msg = (
                    f"{get_retry_prompt()}\n\n"
                    f"上一次错误: {error_msg}"
                )
                window.add({"role": "user", "content": retry_msg})

            except Exception as e:
                logger.error(f"[ReAct] LLM调用异常 (attempt={attempt}): {e}")
                retry_count = attempt
                if attempt >= self.max_retries:
                    raise AgentError(f"LLM调用失败: {e}")

            # 重试前短暂等待
            await asyncio.sleep(0.5)

        logger.error(f"[ReAct] 达到最大重试次数 ({self.max_retries})，放弃本轮")
        return None, None, retry_count

    # ==================== 持久化回调 ====================

    async def _log_step(
        self, iteration: int, thought: str, action: str,
        action_input: dict, observation: str, duration_ms: int
    ):
        """记录执行日志"""
        if self._on_execution_log:
            try:
                await self._on_execution_log(
                    iteration=iteration,
                    thought=thought,
                    action=action,
                    action_input=action_input,
                    observation=observation,
                    duration_ms=duration_ms,
                )
            except Exception as e:
                logger.error(f"[ReAct] 执行日志记录失败: {e}")

    async def _log_tool_call(
        self, tool_name: str, tool_params: dict,
        tool_result: str, success: bool, duration_ms: int
    ):
        """记录工具调用"""
        if self._on_tool_call:
            try:
                await self._on_tool_call(
                    tool_name=tool_name,
                    tool_params=tool_params,
                    tool_result=tool_result,
                    status="success" if success else "error",
                    duration_ms=duration_ms,
                )
            except Exception as e:
                logger.error(f"[ReAct] 工具调用记录失败: {e}")


# 全局 ReAct 引擎实例
react_engine = ReActEngine()
