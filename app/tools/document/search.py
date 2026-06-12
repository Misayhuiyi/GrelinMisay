"""
============================================================================
关键词搜索工具 - 在指定文本/文档库中执行关键词检索
============================================================================
模拟文档检索场景，支持多关键词组合搜索，返回匹配上下文。
"""
from typing import Any, Dict
from app.tools.base import BaseTool, validate_params

# 模拟文档库（实际可接入向量数据库或全文检索引擎）
_SAMPLE_DOCUMENTS = [
    {"title": "Python基础教程", "content": "Python是一种解释型、面向对象的高级编程语言。支持动态类型、垃圾回收。"},
    {"title": "ReAct框架说明", "content": "ReAct（Reasoning + Acting）是一种结合推理与行动的Agent框架，核心循环为Thought-Action-Observation。"},
    {"title": "FastAPI入门", "content": "FastAPI是一个现代、高性能的Web框架，用于构建API，基于Python 3.7+的类型提示。"},
    {"title": "SQL优化指南", "content": "使用索引、避免SELECT *、合理使用JOIN可显著优化SQL查询性能。EXPLAIN语句可查看执行计划。"},
    {"title": "机器学习概述", "content": "机器学习是人工智能的一个分支，包括监督学习、无监督学习、强化学习三大范式。"},
    {"title": "数据库事务管理", "content": "ACID是数据库事务的四大特性：原子性(Atomicity)、一致性(Consistency)、隔离性(Isolation)、持久性(Durability)。"},
]


class DocumentSearchTool(BaseTool):
    """关键词搜索工具 - 在文档库中检索相关内容"""

    @property
    def name(self) -> str:
        return "document_search"

    @property
    def description(self) -> str:
        return (
            "在文档库中按关键词搜索相关内容。"
            "支持多个关键词（空格分隔），返回所有匹配的文档片段。"
            "适用场景：查找技术文档、概念解释、API说明等。"
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "string",
                    "description": "搜索关键词，多个关键词用空格分隔。例如: 'Python 异步 协程'"
                },
            },
            "required": ["keywords"],
        }

    @validate_params
    async def execute(self, keywords: str = "") -> str:
        """执行关键词搜索"""
        kw_list = [kw.strip().lower() for kw in keywords.split() if kw.strip()]
        if not kw_list:
            return "未提供有效搜索关键词。"

        results = []
        for doc in _SAMPLE_DOCUMENTS:
            # 在标题和内容中匹配关键词
            text = (doc["title"] + " " + doc["content"]).lower()
            matched = [kw for kw in kw_list if kw in text]
            if matched:
                results.append(
                    f"[{doc['title']}] (匹配: {', '.join(matched)})\n  {doc['content']}"
                )

        if not results:
            return f"未找到与关键词 '{keywords}' 匹配的文档。"

        return f"搜索到 {len(results)} 条结果:\n" + "\n---\n".join(results)

from app.tools.registry import tool_registry
tool_registry.register(DocumentSearchTool())
