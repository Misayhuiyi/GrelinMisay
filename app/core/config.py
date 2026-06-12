"""
应用配置模块
使用 pydantic-settings 加载环境变量，提供类型安全的配置访问
"""
from functools import lru_cache
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """应用配置类，所有配置项从 .env 文件加载"""

    # ========== LLM 配置 ==========
    LLM_API_KEY: str = ""
    LLM_API_BASE: str = "https://api.deepseek.com/v1"
    LLM_MODEL_NAME: str = "deepseek-chat"
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 4096
    LLM_REQUEST_TIMEOUT: int = 60
    LLM_MAX_RETRIES: int = 3
    LLM_RETRY_DELAY: int = 2

    # ========== ReAct 推理配置 ==========
    REACT_MAX_ITERATIONS: int = 10
    REACT_OUTPUT_VALIDATION: bool = True
    REACT_MAX_RETRIES: int = 3

    # ========== 记忆管理配置 ==========
    MEMORY_WINDOW_SIZE: int = 12
    MEMORY_COMPRESSION_ENABLED: bool = True
    MEMORY_MAX_TOKENS: int = 8000

    # ========== 数据库配置 ==========
    DB_TYPE: str = "sqlite"
    DB_PATH: str = "./data/agent.db"

    # ========== 服务配置 ==========
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    SERVER_DEBUG: bool = False

    # ========== 日志配置 ==========
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"
    LOG_MAX_BYTES: int = 10485760
    LOG_BACKUP_COUNT: int = 5

    # ========== 项目根目录 ==========
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @property
    def db_url(self) -> str:
        """获取数据库连接 URL"""
        if self.DB_TYPE == "sqlite":
            db_path = self.BASE_DIR / self.DB_PATH
            db_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite+aiosqlite:///{db_path}"
        raise ValueError(f"Unsupported database type: {self.DB_TYPE}")


@lru_cache
def get_settings() -> Settings:
    """获取配置单例（缓存）"""
    return Settings()
