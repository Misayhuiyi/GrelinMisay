"""
============================================================================
统计计算工具 - 均值、方差、标准差、回归等统计分析
============================================================================
对一组数字进行描述性统计分析。
"""
import math
from typing import Any, Dict, List
from app.tools.base import BaseTool, validate_params


class StatisticsTool(BaseTool):
    """统计计算工具 - 描述性统计分析"""

    @property
    def name(self) -> str:
        return "statistics"

    @property
    def description(self) -> str:
        return (
            "对一组数字进行描述性统计分析。"
            "输出：计数、总和、均值、中位数、最小值、最大值、方差、标准差。"
            "适用场景：数据分析、数值汇总、趋势判断等。"
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "numbers": {
                    "type": "string",
                    "description": "逗号分隔的数字列表，如 '1,2,3,4,5' 或 '1.5,2.7,3.2'"
                },
            },
            "required": ["numbers"],
        }

    @validate_params
    async def execute(self, numbers: str = "") -> str:
        """执行统计分析"""
        # 解析数字列表
        try:
            values = [float(x.strip()) for x in numbers.split(",") if x.strip()]
        except ValueError as e:
            return f"输入包含非数字值: {e}"

        if not values:
            return "请提供至少一个数字。"

        n = len(values)
        if n == 1:
            return f"只有一个数据点: {values[0]}"

        # 基本统计量
        sorted_vals = sorted(values)
        total = sum(values)
        mean = total / n

        # 中位数
        mid = n // 2
        if n % 2 == 0:
            median = (sorted_vals[mid - 1] + sorted_vals[mid]) / 2
        else:
            median = sorted_vals[mid]

        # 方差（样本方差）
        variance = sum((x - mean) ** 2 for x in values) / (n - 1) if n > 1 else 0

        # 标准差
        std_dev = math.sqrt(variance)

        # 最小、最大、极差
        min_val = sorted_vals[0]
        max_val = sorted_vals[-1]
        range_val = max_val - min_val

        return (
            f"统计分析结果 (数据量: {n}):\n"
            f"  计数: {n}\n"
            f"  总和: {total:.4g}\n"
            f"  均值: {mean:.4g}\n"
            f"  中位数: {median:.4g}\n"
            f"  最小值: {min_val:.4g}\n"
            f"  最大值: {max_val:.4g}\n"
            f"  极差: {range_val:.4g}\n"
            f"  样本方差: {variance:.4g}\n"
            f"  标准差: {std_dev:.4g}"
        )

from app.tools.registry import tool_registry
tool_registry.register(StatisticsTool())
