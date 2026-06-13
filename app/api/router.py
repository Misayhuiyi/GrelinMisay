"""
============================================================================
路由汇总 - 注册所有API子路由
============================================================================
"""
from fastapi import APIRouter
from app.api.chat import router as chat_router
from app.api.session import router as session_router
from app.api.tool import router as tool_router
from app.api.g_auth import router as g_auth_router
from app.api.g_users import router as g_users_router
from app.api.g_goals import router as g_goals_router
from app.api.g_training import router as g_training_router
from app.api.g_calendar import router as g_calendar_router
from app.api.g_ai import router as g_ai_router

# 创建主路由聚合器
api_router = APIRouter()

# 注册原有模块子路由
api_router.include_router(chat_router)
api_router.include_router(session_router)
api_router.include_router(tool_router)

# 注册 GrelinMisay 业务子路由
api_router.include_router(g_auth_router)
api_router.include_router(g_users_router)
api_router.include_router(g_goals_router)
api_router.include_router(g_training_router)
api_router.include_router(g_calendar_router)
api_router.include_router(g_ai_router)
