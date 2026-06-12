"""
============================================================================
表结构探查工具 - 查看数据库表结构、字段信息
============================================================================
帮助Agent了解可查询的表名、列名和数据类型，指导SQL生成。
"""
from typing import Any, Dict
from sqlalchemy import text, inspect
from app.tools.base import BaseTool, validate_params
from app.db.database import engine, Base
from app.core.logger import logger


class SchemaExplorerTool(BaseTool):
    """表结构探查工具 - 查看数据库Schema信息"""

    @property
    def name(self) -> str:
        return "schema_explorer"

    @property
    def description(self) -> str:
        return (
            "探查数据库表结构信息。可查看所有表名列表，或指定表的详细字段信息（列名、类型、注释）。"
            "适用场景：编写SQL查询前，先了解有哪些表和字段。"
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "要查看的表名。不填则列出所有表名。"
                },
            },
            "required": [],
        }

    @validate_params
    async def execute(self, table_name: str = "") -> str:
        """探查表结构"""
        try:
            async with engine.connect() as conn:
                # 使用 run_sync 来运行同步的 inspect
                def do_inspect(sync_conn):
                    inspector = inspect(sync_conn)
                    tables = inspector.get_table_names()

                    if not table_name:
                        # 返回所有表名列表
                        lines = [f"数据库中共有 {len(tables)} 张表:"]
                        for i, t in enumerate(tables, 1):
                            lines.append(f"  {i}. {t}")
                        return "\n".join(lines)

                    # 查看指定表详情
                    if table_name not in tables:
                        return f"表 '{table_name}' 不存在。可用的表: {', '.join(tables)}"

                    columns = inspector.get_columns(table_name)
                    lines = [f"表名: {table_name}", "-" * 40]
                    for col in columns:
                        nullable = "可空" if col.get("nullable", True) else "非空"
                        pk = " [主键]" if col.get("primary_key") else ""
                        comment = f" -- {col.get('comment', '')}" if col.get("comment") else ""
                        lines.append(
                            f"  {col['name']:20s} {str(col['type']):15s} {nullable}{pk}{comment}"
                        )
                    return "\n".join(lines)

                return await conn.run_sync(do_inspect)

        except Exception as e:
            logger.error(f"[SchemaExplorer] 探查失败: {e}")
            return f"表结构探查失败: {e}"

from app.tools.registry import tool_registry
tool_registry.register(SchemaExplorerTool())
