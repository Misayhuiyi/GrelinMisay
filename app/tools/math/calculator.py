"""
============================================================================
基础计算器工具 - 安全的数学表达式求值
============================================================================
支持四则运算、幂运算、括号、常用数学函数，拒绝危险操作。
"""
import math
import re
from typing import Any, Dict
from app.tools.base import BaseTool, validate_params
from app.core.logger import logger


class CalculatorTool(BaseTool):
    """基础计算器工具 - 安全的数学表达式求值"""

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return (
            "安全的数学表达式计算器。支持基本四则运算、幂运算、括号、常用数学函数。"
            "支持函数: abs, round, min, max, pow, sqrt, log, log10, sin, cos, tan, pi, e。"
            "适用场景：数值计算、公式求解、单位换算等。"
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "数学表达式，如 '2 + 3 * 4'、'sqrt(16)'、'pow(2, 10)'"
                },
            },
            "required": ["expression"],
        }

    @validate_params
    async def execute(self, expression: str = "") -> str:
        """执行数学计算"""
        # ---------- 安全白名单 ----------
        safe_names = {
            "abs": abs, "round": round, "min": min, "max": max,
            "pow": pow, "sqrt": math.sqrt, "log": math.log,
            "log10": math.log10, "log2": math.log2,
            "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "pi": math.pi, "e": math.e,
            "ceil": math.ceil, "floor": math.floor,
        }

        try:
            # 安全校验：表达式只能包含允许的字符
            allowed_pattern = r"^[\d\s\+\-\*\/\(\)\.\,\%\_a-zA-Z]+$"
            if not re.match(allowed_pattern, expression):
                return "表达式包含不允许的字符，仅支持数字、运算符、括号和常用数学函数。"

            # 长度限制
            if len(expression) > 500:
                return "表达式过长，最多支持500个字符。"

            # 编译表达式
            code = compile(expression, "<calculator>", "eval")

            # 检查是否使用了未允许的函数/变量
            for name in code.co_names:
                if name not in safe_names:
                    return (
                        f"不允许使用 '{name}'。支持的函数和常量: "
                        f"{', '.join(sorted(safe_names.keys()))}"
                    )

            # 执行求值
            result = eval(code, {"__builtins__": {}}, safe_names)

            # 格式化输出
            if isinstance(result, float):
                # 避免浮点数精度问题
                if abs(result) < 1e-10:
                    result = 0.0
                return f"计算结果: {result:.10g}"
            return f"计算结果: {result}"

        except SyntaxError:
            return f"表达式语法错误: {expression}"
        except ZeroDivisionError:
            return "错误: 除零操作"
        except ValueError as e:
            return f"数值错误: {e}"
        except Exception as e:
            logger.error(f"[Calculator] 计算异常: {e}")
            return f"计算失败: {e}"

from app.tools.registry import tool_registry
tool_registry.register(CalculatorTool())
