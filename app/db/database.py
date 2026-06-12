"""
============================================================================
数据库连接管理 - SQLAlchemy 异步引擎 + Session工厂
============================================================================
支持 SQLite（默认）和 PostgreSQL，通过 .env 的 db_type 切换。
提供异步 Session 上下文管理器，自动提交/回滚。
"""
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import get_settings

settings = get_settings()

# ---------- 异步引擎 ----------
# echo=False 关闭SQL日志，生产环境保持静默
engine = create_async_engine(
    settings.db_url,
    echo=False,
    pool_size=5,              # 连接池大小
    max_overflow=10,          # 溢出连接数
    pool_pre_ping=True,       # 每次获取连接前检测有效性
)

# ---------- 异步Session工厂 ----------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,   # 提交后不使对象过期
)


class Base(DeclarativeBase):
    """SQLAlchemy ORM 基类，所有模型继承此基类"""
    pass


async def get_db() -> AsyncSession:
    """
    依赖注入用的数据库 Session 生成器。
    自动处理 commit / rollback / close。
    用法: db = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    首次启动时自动创建所有表。
    在 FastAPI lifespan 事件中调用。
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库连接池"""
    await engine.dispose()
