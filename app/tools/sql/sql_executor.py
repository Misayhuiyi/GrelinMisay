"""
============================================================================
SQL执行器工具 - 在本地SQL数据库中执行 SELECT 查询
============================================================================
安全策略：仅允许 SELECT 语句，禁止 INSERT/UPDATE/DELETE/DROP 等写操作。
"""
from typing import Any, Dict
from sqlalchemy import text
from app.tools.base import BaseTool, validate_params
from app.db.database import AsyncSessionLocal
from app.core.logger import logger


# 安检关键字黑名单
_FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
    "CREATE", "TRUNCATE", "GRANT", "REVOKE", "EXEC",
    "EXECUTE", "MERGE", "REPLACE",
]


class SQLExecutorTool(BaseTool):
    """SQL执行器工具 - 仅支持SELECT只读查询"""

    @property
    def name(self) -> str:
        return "sql_query"

    @property
    def description(self) -> str:
        return (
            "在本地数据库中执行SQL SELECT查询语句。"
            "仅支持只读查询(SELECT)，禁止任何写操作。"
            "适用场景：查询会话数据、统计消息数量、分析对话历史等。"
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "要执行的SQL SELECT查询语句"
                },
            },
            "required": ["query"],
        }

    @validate_params
    async def execute(self, query: str = "") -> str:
        """执行SQL查询"""
        # ---------- 安全检查：只允许SELECT ----------
        upper_query = query.strip().upper()

        # 移除字符串字面量后再检查，避免误报
        import re
        clean_query = re.sub(r"'[^']*'", "", upper_query)
        clean_query = re.sub(r'"[^"]*"', "", clean_query)

        for keyword in _FORBIDDEN_KEYWORDS:
            pattern = r"\b" + keyword + r"\b"
            if re.search(pattern, clean_query):
                return (
                    f"安全检查拒绝：查询中包含禁止的SQL关键字 '{keyword}'。"
                    f"仅允许只读SELECT查询。"
                )

        if not clean_query.strip().startswith("SELECT"):
            return "安全检查拒绝：查询必须以SELECT开头。仅允许只读查询。"

        # ---------- 执行查询 ----------
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text(query))
                rows = result.fetchall()

                if not rows:
                    return "查询结果为空。"

                # 限制返回行数
                max_rows = 50
                if len(rows) > max_rows:
                    rows = rows[:max_rows]
                    truncated_msg = f"\n... (结果已截断，共 {len(rows)} 行，显示前 {max_rows} 行)"
                else:
                    truncated_msg = ""

                # 获取列名
                columns = result.keys()

                # 格式化输出为表格
                lines = [" | ".join(columns)]
                lines.append("-" * len(lines[0]))
                for row in rows:
                    lines.append(" | ".join(str(v) for v in row))

                return f"查询返回 {len(rows)} 行:\n" + "\n".join(lines) + truncated_msg

        except Exception as e:
            logger.error(f"[SQLExecutor] 查询执行失败: {e}")
            return f"SQL查询执行失败: {e}"

from app.tools.registry import tool_registry
tool_registry.register(SQLExecutorTool())
