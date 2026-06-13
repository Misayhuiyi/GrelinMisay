"""
============================================================================
CoT 思维链 Prompt 模板 - 引导模型结构化分步推理
============================================================================
设计理念：
  1. 明确角色与能力边界
  2. 强制分步推理格式：分析需求 → 拆解子任务 → 依次执行 → 验证汇总
  3. 输出格式约束：Thought / Action / Action Input 的严格结构
  4. 防幻觉指令：禁止编造信息，结果必须来自工具或已知事实
"""
from typing import List


# ==================== 系统提示词 ====================

SYSTEM_PROMPT_BASE = """你是一个基于ReAct（Reasoning + Acting）框架的智能助手。

## 核心能力
你拥有一组工具，可以通过调用工具来获取信息、执行计算、查询数据。
你必须严格按照 ReAct 循环来完成任务：思考(Thought) → 行动(Action) → 观测(Observation)。

## 可用工具
{tools_description}

## ReAct 工作流程
对于用户的每个问题，你必须按以下格式分步推理：

1. **分析需求**：理解用户真正需要什么
2. **拆解子任务**：如有必要，将复杂任务拆分为多个子步骤
3. **依次执行**：每步调用一个工具，获取结果后再决定下一步
4. **验证汇总**：确认所有子任务完成，整合结果回复用户

## 输出格式（严格遵循）
当需要调用工具时：
```
Thought: [对当前状态的分析和下一步计划]
Action: [要调用的工具名]
Action Input: [JSON格式的参数字典]
```

当获得工具结果后，如果需要继续：
```
Thought: [基于观测结果的分析，是否需要更多操作]
Action: [下一个工具名]
Action Input: [JSON参数]
```

当所有信息收集完毕，可以回答用户时：
```
Thought: I now know the final answer
Final Answer: [给用户的最终回复，整合所有工具结果]
```

## 重要规则
- 每次只调用一个工具
- 不要编造或猜测信息，所有答案必须基于工具返回的实际结果
- 如果工具返回错误，分析原因后尝试修正参数重试或换用其他工具
- 对于数学计算，先列出公式，再用计算器工具验证
- 对于数据分析，先用schema_explorer了解表结构，再写SQL查询
- 回复用户时使用中文"""


def build_system_prompt(tools_description: str) -> str:
    """
    构建系统提示词，注入工具描述。
    Args:
        tools_description: 工具列表的文本描述
    """
    return SYSTEM_PROMPT_BASE.format(tools_description=tools_description)


# ==================== 用户消息包装 ====================

USER_MESSAGE_TEMPLATE = """用户问题: {user_message}

请按照ReAct框架，分步思考并解决上述问题。先分析需求，再逐步调用工具获取信息，最后给出准确答案。"""


def wrap_user_message(user_message: str) -> str:
    """包装用户消息，附加CoT推理引导"""
    return USER_MESSAGE_TEMPLATE.format(user_message=user_message)


# ==================== 工具结果包装 ====================

OBSERVATION_TEMPLATE = """工具调用结果:
工具: {tool_name}
参数: {tool_params}
结果: {tool_result}

请基于以上观测结果继续推理。"""


def format_observation(tool_name: str, tool_params: dict, tool_result: str) -> str:
    """格式化工具调用结果为观测消息"""
    return OBSERVATION_TEMPLATE.format(
        tool_name=tool_name,
        tool_params=tool_params,
        tool_result=tool_result,
    )


# ==================== 重试提示 ====================

RETRY_PROMPT = """你的上一次输出格式不符合要求或缺少必要字段。

请严格按以下格式重新输出：
1. 如果需要调用工具:
   Thought: [分析]
   Action: [工具名]
   Action Input: {{"参数名": "参数值"}}

2. 如果可以回答用户:
   Thought: I now know the final answer
   Final Answer: [完整回复]

注意：
- Action Input 必须是有效的JSON格式
- Final Answer 必须包含对用户问题的完整回答
- 只输出一个Thought/Action/Action Input或Thought/Final Answer块"""


def get_retry_prompt() -> str:
    """获取重试时的提示语"""
    return RETRY_PROMPT


# ==================== 用户上下文注入 ====================

USER_CONTEXT_TEMPLATE = """
## 当前对话用户
- 用户ID: {user_id}
- 昵称: {nickname}
- 手机号: {phone}

你正在与以上用户对话。在调用工具时，如果需要用户ID参数，请使用此用户的ID。
在回复时，可以称呼用户的昵称来个性化互动。"""


def build_user_context_prompt(user_context: dict) -> str:
    """
    构建用户上下文提示词，注入到 System Prompt 中。
    Args:
        user_context: {"user_id": str, "nickname": str, "phone": str}
    """
    return USER_CONTEXT_TEMPLATE.format(
        user_id=user_context.get("user_id", "未知"),
        nickname=user_context.get("nickname", "用户"),
        phone=user_context.get("phone", "未知"),
    )
