"""
FastAPI 应用入口
处理生命周期、CORS、全局异常、工具注册
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logger import logger
from app.core.exceptions import AgentAppError
from app.db.database import init_db, close_db
from app.tools.registry import tool_registry
from app.api.router import api_router

# 延迟导入工具模块以触发注册
from app.tools.math.calculator import CalculatorTool  # noqa: F401
from app.tools.math.statistics import StatisticsTool  # noqa: F401
from app.tools.document.search import DocumentSearchTool  # noqa: F401
from app.tools.document.file_reader import FileReaderTool  # noqa: F401
from app.tools.document.web_fetch import WebFetchTool  # noqa: F401
from app.tools.sql.sql_executor import SQLExecutorTool  # noqa: F401
from app.tools.sql.schema_explorer import SchemaExplorerTool  # noqa: F401
from app.tools.sql.data_analyzer import DataAnalyzerTool  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    settings = get_settings()

    # 启动时
    logger.info("=" * 60)
    logger.info("ReAct+CoT AI Agent 启动中...")
    logger.info("模型: %s", settings.LLM_MODEL_NAME)
    logger.info("数据库: %s", settings.db_url)
    logger.info("=" * 60)

    await init_db()
    logger.info("数据库表初始化完成")

    # 注册所有工具
    from app.tools.registry import tool_registry
    count = len(tool_registry.list_tools())
    logger.info("已注册 %d 个内置工具", count)

    if not settings.LLM_API_KEY:
        logger.warning(
            "[WARNING] LLM_API_KEY not configured! "
            "Please edit .env file and set your API Key. "
            "Service starts but chat will be unavailable."
        )

    yield

    # 关闭时
    await close_db()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="ReAct+CoT AI Agent",
    description="基于 ReAct 框架 + CoT 优化的轻量化 AI Agent 智能助手",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router)


# 全局异常处理
@app.exception_handler(AgentAppError)
async def agent_app_error_handler(request, exc: AgentAppError):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc.message)},
    )


@app.exception_handler(Exception)
async def general_error_handler(request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/api/health")
async def health():
    """健康检查端点"""
    settings = get_settings()
    from app.tools.registry import tool_registry
    return {
        "status": "ok",
        "model": settings.LLM_MODEL_NAME,
        "tools_count": len(tool_registry.list_tools()),
        "db_type": settings.DB_TYPE,
    }
