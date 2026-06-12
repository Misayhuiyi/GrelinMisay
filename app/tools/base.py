"""
============================================================================
工具抽象基类 - 统一工具接口定义
============================================================================
所有工具必须继承 BaseTool 并实现以下接口：
  - name: 工具唯一标识
  - description: 工具功能描述（喂给LLM）
  - parameters_schema: 参数JSON Schema
  - execute: 核心执行方法
内置参数校验装饰器 @validate_params，自动校验并兜底。
"""
import time
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Callable
from functools import wraps
from app.core.logger import logger
from app.core.exceptions import ToolParamError, ToolExecutionError


def validate_params(func: Callable) -> Callable:
    """
    参数校验装饰器：自动校验工具入参是否匹配 parameters_schema。
    校验失败抛出 ToolParamError，被上层兜底捕获。
    """
    @wraps(func)
    async def wrapper(self: "BaseTool", **kwargs) -> str:
        # Step 1: 参数存在性检查
        required = self.parameters_schema.get("required", [])
        for key in required:
            if key not in kwargs or kwargs[key] is None:
                raise ToolParamError(
                    tool_name=self.name,
                    param_errors=f"缺少必填参数: {key}"
                )

        # Step 2: 参数类型粗略检查
        properties = self.parameters_schema.get("properties", {})
        for key, value in kwargs.items():
            if key in properties:
                expected_type = properties[key].get("type", "string")
                if expected_type == "number" and not isinstance(value, (int, float)):
                    raise ToolParamError(
                        tool_name=self.name,
                        param_errors=f"参数 {key} 应为数字类型，实际为 {type(value).__name__}"
                    )

        logger.debug(f"[工具] {self.name} 参数校验通过: {kwargs}")
        return await func(self, **kwargs)
    return wrapper


class BaseTool(ABC):
    """
    工具抽象基类。
    子类必须提供: name, description, parameters_schema, execute()
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """工具唯一标识名"""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """工具功能描述，会注入到LLM Prompt中"""
        ...

    @property
    @abstractmethod
    def parameters_schema(self) -> Dict[str, Any]:
        """
        参数 JSON Schema 定义，格式：
        {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "说明"}
            },
            "required": ["key"]
        }
        """
        ...

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """核心执行方法，返回执行结果字符串"""
        ...

    async def safe_execute(self, **kwargs) -> Dict[str, Any]:
        """
        带异常兜底的执行方法，上层调用此方法而非直接 execute。
        返回: {"success": bool, "result": str, "duration_ms": int}
        """
        start = time.time()
        try:
            result = await self.execute(**kwargs)
            duration_ms = int((time.time() - start) * 1000)
            logger.info(f"[工具] {self.name} 执行成功, 耗时 {duration_ms}ms")
            return {"success": True, "result": result, "duration_ms": duration_ms}
        except ToolParamError as e:
            duration_ms = int((time.time() - start) * 1000)
            logger.warning(f"[工具] {self.name} 参数错误: {e.message}")
            return {"success": False, "result": str(e.to_dict()), "duration_ms": duration_ms}
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            logger.error(f"[工具] {self.name} 执行异常: {e}", exc_info=True)
            return {"success": False, "result": f"工具执行异常: {str(e)}", "duration_ms": duration_ms}

    def to_openai_schema(self) -> Dict[str, Any]:
        """
        将工具转换为 OpenAI 兼容的函数调用 Schema。
        用于注入到 LLM 的 tools 参数中。
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema,
            }
        }

    def to_prompt_description(self) -> str:
        """将工具转换为纯文本描述，用于纯Prompt模式"""
        return f"- {self.name}: {self.description}"
