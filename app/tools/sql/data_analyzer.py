"""
============================================================================
数据统计分析工具 - 对查询结果进行统计分析
============================================================================
提供 COUNT / SUM / AVG / MIN / MAX / GROUP BY 等统计查询能力。
基于SQLExecutorTool执行，加上结果解释。
"""
from typing import Any, Dict
from app.tools.base import BaseTool, validate_params
from app.db.database import AsyncSessionLocal
from sqlalchemy import text
from app.core.logger import logger


class DataAnalyzerTool(BaseTool):
    """数据统计分析工具 - 执行统计查询并解释结果"""

    @property
    def name(self) -> str:
        return "data_analyzer"

    @property
    def description(self) -> str:
        return (
            "对数据库中的数据进行统计分析（COUNT、SUM、AVG、MIN、MAX、GROUP BY）。"
            "适用于需要对查询结果进行汇总统计的场景。"
            "输入统计分析问题描述（自然语言），输出统计结果。"
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "stat_query": {
                    "type": "string",
                    "description": (
                        "统计分析查询（SELECT语句，需包含聚合函数）。"
                        "例如: 'SELECT COUNT(*) as total FROM messages'"
                    )
                },
            },
            "required": ["stat_query"],
        }

    @validate_params
    async def execute(self, stat_query: str = "") -> str:
        """执行统计分析"""
        upper_query = stat_query.strip().upper()
        if not upper_query.startswith("SELECT"):
            return "统计分析查询必须以SELECT开头。"

        # 聚合函数检查（至少包含一个）
        agg_funcs = ["COUNT", "SUM", "AVG", "MIN", "MAX", "GROUP BY"]
        has_agg = any(func in upper_query for func in agg_funcs)
        if not has_agg:
            return (
                "查询未包含聚合函数。支持的统计操作: "
                f"{', '.join(agg_funcs)}"
            )

        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text(stat_query))
                rows = result.fetchall()
                columns = result.keys()

                if not rows:
                    return "统计结果为空。"

                # 格式化为可读结果
                lines = ["统计分析结果:", "-" * 30]
                for row in rows:
                    item = ", ".join(
                        f"{col} = {val}" for col, val in zip(columns, row)
                    )
                    lines.append(f"  {item}")

                return "\n".join(lines)

        except Exception as e:
            logger.error(f"[DataAnalyzer] 分析失败: {e}")
            return f"统计分析执行失败: {e}"

from app.tools.registry import tool_registry
tool_registry.register(DataAnalyzerTool())
