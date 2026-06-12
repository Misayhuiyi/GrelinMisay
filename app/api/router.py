"""
============================================================================
路由汇总 - 注册所有API子路由
============================================================================
"""
from fastapi import APIRouter
from app.api.chat import router as chat_router
from app.api.session import router as session_router
from app.api.tool import router as tool_router

# 创建主路由聚合器
api_router = APIRouter()

# 注册各模块子路由
api_router.include_router(chat_router)
api_router.include_router(session_router)
api_router.include_router(tool_router)
