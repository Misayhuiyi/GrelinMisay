"""
============================================================================
一键启动入口 - python run.py
============================================================================
用法：
  python run.py                # 默认启动
  python run.py --port 9000    # 指定端口
  python run.py --reload       # 开发模式（热重载）
"""
import sys
import uvicorn
from app.core.config import get_settings

settings = get_settings()


def main():
    """启动 FastAPI 服务"""
    # 解析命令行参数
    host = settings.SERVER_HOST
    port = settings.SERVER_PORT
    reload = settings.SERVER_DEBUG

    for arg in sys.argv[1:]:
        if arg.startswith("--port="):
            port = int(arg.split("=")[1])
        elif arg == "--reload":
            reload = True
        elif arg.startswith("--host="):
            host = arg.split("=")[1]

    print("=" * 60)
    print("  ReAct+CoT AI Agent 智能助手")
    print(f"  启动地址: http://{host}:{port}")
    print(f"  Swagger文档: http://{host}:{port}/docs")
    print(f"  ReDoc文档: http://{host}:{port}/redoc")
    print(f"  健康检查: http://{host}:{port}/api/health")
    print("=" * 60)

    # 检查 API Key
    if not settings.LLM_API_KEY:
        print("\n[WARNING] LLM_API_KEY not configured!")
        print("  Please edit .env file and set your API Key.\n")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()
