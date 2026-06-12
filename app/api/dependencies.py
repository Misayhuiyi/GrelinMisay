"""
============================================================================
FastAPI 依赖注入 - 为路由提供共享组件
============================================================================
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.llm import llm_wrapper
from app.tools.registry import tool_registry
from app.agent.react_engine import react_engine

# 所有依赖通过模块级别的导入即可使用，不再需要复杂的 Depends 链
# FastAPI 路由层直接 import 这些实例
