"""
============================================================================
输出校验器 + 失败重试机制
============================================================================
对 LLM 输出进行结构化校验：
  1. 格式校验：是否包含 Thought / Action / Final Answer
  2. 工具名校验：调用的工具是否已注册
  3. 参数Schema校验：对照工具的 parameters_schema 验证入参
  4. 最终答案完整性：Final Answer 是否非空

校验失败时自动重试（最多 max_retries 次），每次重试会追加错误提示。
"""
import json
import re
from typing import Dict, Any, Optional, Tuple
from app.core.config import get_settings
from app.core.logger import logger
from app.core.exceptions import ToolNotFoundError
from app.tools.registry import ToolRegistry

settings = get_settings()


class OutputValidator:
    """
    LLM 输出校验器。
    校验 ReAct 格式：提取 Thought/Action/Action Input 或 Final Answer。
    """

    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry

    def validate_and_parse(
        self, llm_output: str
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        校验并解析 LLM 输出。
        Returns:
            (是否有效, 解析结果dict或None, 错误信息)
        解析结果格式:
          {"type": "tool_call", "thought": str, "action": str, "action_input": dict}
          或
          {"type": "final_answer", "thought": str, "final_answer": str}
        """
        output = llm_output.strip()

        # ====== 检查是否包含 Final Answer ======
        if "Final Answer:" in output or "最终答案:" in output:
            return self._parse_final_answer(output)

        # ====== 检查是否包含 Action ======
        if "Action:" in output:
            return self._parse_tool_call(output)

        # ====== 都不是 ======
        return False, None, "输出格式不符合要求：需包含 'Action:' 或 'Final Answer:'"

    def _parse_tool_call(
        self, llm_output: str
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """解析工具调用格式"""
        # 提取 Thought
        thought_match = re.search(r"Thought:\s*(.+?)(?:\n|$)", llm_output, re.IGNORECASE)
        if not thought_match:
            thought_match = re.search(r"思考[：:]\s*(.+?)(?:\n|$)", llm_output)
        thought = thought_match.group(1).strip() if thought_match else ""

        # 提取 Action
        action_match = re.search(r"Action:\s*(\S+)", llm_output)
        if not action_match:
            return False, None, "缺少 'Action:' 字段，请指定要调用的工具名"
        action = action_match.group(1).strip()

        # 校验工具是否存在
        if action not in self.tool_registry.list_tools():
            available = ", ".join(self.tool_registry.list_tools())
            return False, None, (
                f"工具 '{action}' 未注册。可用工具: {available}"
            )

        # 提取 Action Input (JSON)
        action_input = self._extract_json(llm_output, "Action Input")

        # 校验参数 Schema
        tool = self.tool_registry.get(action)
        schema_valid, schema_error = self._validate_params(
            action, action_input, tool.parameters_schema
        )
        if not schema_valid:
            return False, None, schema_error

        return True, {
            "type": "tool_call",
            "thought": thought,
            "action": action,
            "action_input": action_input,
        }, ""

    def _parse_final_answer(
        self, llm_output: str
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """解析最终答案格式"""
        # 提取 Thought
        thought_match = re.search(r"Thought:\s*(.+?)(?:\n|$)", llm_output, re.IGNORECASE)
        thought = thought_match.group(1).strip() if thought_match else ""

        # 提取 Final Answer
        fa_patterns = [
            r"Final Answer:\s*(.+)",
            r"最终答案[：:]\s*(.+)",
        ]
        final_answer = ""
        for pattern in fa_patterns:
            fa_match = re.search(pattern, llm_output, re.DOTALL | re.IGNORECASE)
            if fa_match:
                final_answer = fa_match.group(1).strip()
                break

        if not final_answer:
            return False, None, "缺少 'Final Answer:' 字段，请给出最终回答"

        if len(final_answer) < 5:
            return False, None, "最终答案过短（少于5个字符），请给出完整回答"

        return True, {
            "type": "final_answer",
            "thought": thought,
            "final_answer": final_answer,
        }, ""

    @staticmethod
    def _extract_json(text: str, label: str) -> Dict[str, Any]:
        """
        从文本中提取 JSON 块。
        支持多种格式：
        - Action Input: {"key": "value"}
        - Action Input: ```json\n{...}\n```
        """
        # 先尝试直接匹配 { ... }
        json_match = re.search(rf"{label}[:：]\s*(\{{.+?\}})", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试匹配 markdown code block
        code_match = re.search(
            rf"{label}[:：]\s*```(?:json)?\s*(\{{.+?\}})\s*```",
            text, re.DOTALL
        )
        if code_match:
            try:
                return json.loads(code_match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试从整个文本中提取第一个 JSON 对象
        brace_match = re.search(r"\{[^{}]*\}", text)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        return {}

    def _validate_params(
        self, tool_name: str, params: Dict[str, Any], schema: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """校验工具参数是否匹配 Schema"""
        required = schema.get("required", [])
        properties = schema.get("properties", {})

        for key in required:
            if key not in params or params[key] is None or params[key] == "":
                return False, (
                    f"工具 '{tool_name}' 缺少必填参数 '{key}'。"
                    f"Schema: {json.dumps(schema, ensure_ascii=False)}"
                )

        # 类型粗略检查
        for key, value in params.items():
            if key in properties:
                prop_type = properties[key].get("type", "string")
                if prop_type == "number" and not isinstance(value, (int, float)):
                    return False, (
                        f"工具 '{tool_name}' 参数 '{key}' 类型错误："
                        f"期望 number，实际 {type(value).__name__}"
                    )

        return True, ""

    def needs_retry(self, parse_result: Optional[Dict]) -> bool:
        """判断解析结果是否需要重试"""
        return parse_result is None or parse_result.get("type") is None
