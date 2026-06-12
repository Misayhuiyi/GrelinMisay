"""
============================================================================
工具注册中心 - 动态注册、发现、调用工具
============================================================================
全局单例，维护工具名 → BaseTool实例的映射。
支持运行时动态注册，为 ReAct 引擎提供工具发现和调度能力。
"""
from typing import Dict, Optional, List, Any
from app.tools.base import BaseTool
from app.core.exceptions import ToolNotFoundError
from app.core.logger import logger


class ToolRegistry:
    """
    工具注册中心（单例模式）。
    - register(): 注册工具
    - call(): 按名调用工具
    - get_schemas(): 获取所有工具的 OpenAI Schema
    - get_descriptions(): 获取所有工具的文本描述
    """

    _instance: Optional["ToolRegistry"] = None

    def __new__(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools: Dict[str, BaseTool] = {}
        return cls._instance

    def register(self, tool: BaseTool) -> None:
        """注册一个工具实例"""
        if tool.name in self._tools:
            logger.warning(f"工具 '{tool.name}' 已存在，将被覆盖")
        self._tools[tool.name] = tool
        logger.info(f"[注册中心] 注册工具: {tool.name}")

    def register_many(self, tools: List[BaseTool]) -> None:
        """批量注册工具"""
        for tool in tools:
            self.register(tool)

    def unregister(self, tool_name: str) -> bool:
        """注销工具"""
        if tool_name in self._tools:
            del self._tools[tool_name]
            logger.info(f"[注册中心] 注销工具: {tool_name}")
            return True
        return False

    def get(self, tool_name: str) -> BaseTool:
        """获取已注册的工具实例"""
        if tool_name not in self._tools:
            raise ToolNotFoundError(tool_name)
        return self._tools[tool_name]

    def list_tools(self) -> List[str]:
        """列出所有已注册的工具名"""
        return list(self._tools.keys())

    def get_openai_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具的 OpenAI 兼容 Schema 列表"""
        return [tool.to_openai_schema() for tool in self._tools.values()]

    def get_prompt_descriptions(self) -> str:
        """获取所有工具的文本描述，用于 CoT Prompt 注入"""
        lines = []
        for tool in self._tools.values():
            lines.append(tool.to_prompt_description())
        return "\n".join(lines)

    async def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        按名调用工具（带异常兜底）。
        返回: {"success": bool, "result": str, "duration_ms": int}
        """
        tool = self.get(tool_name)  # 可能抛出 ToolNotFoundError
        logger.info(f"[注册中心] 调用工具: {tool_name}, 参数: {kwargs}")
        result = await tool.safe_execute(**kwargs)
        return result


# 全局唯一的工具注册中心实例
tool_registry = ToolRegistry()
