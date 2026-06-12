"""
异常层次结构
定义 5 级异常体系：AgentAppError → AgentError / ToolError / LLMError / APIError
"""


class AgentAppError(Exception):
    """应用顶层异常基类"""
    def __init__(self, message: str = "Application error"):
        self.message = message
        super().__init__(message)


# ========== Agent 层异常 ==========

class AgentError(AgentAppError):
    """Agent 引擎运行时错误"""
    pass


class AgentMaxIterationsError(AgentError):
    """Agent 达到最大迭代次数"""
    pass


class AgentOutputInvalidError(AgentError):
    """Agent 输出格式无效"""
    pass


# ========== 工具层异常 ==========

class ToolError(AgentAppError):
    """工具执行错误"""
    pass


class ToolNotFoundError(ToolError):
    """工具未注册"""
    pass


class ToolParamError(ToolError):
    """工具参数错误"""
    pass


class ToolExecutionError(ToolError):
    """工具执行失败"""
    pass


# ========== LLM 层异常 ==========

class LLMError(AgentAppError):
    """LLM 调用错误"""
    pass


class LLMTimeoutError(LLMError):
    """LLM 请求超时"""
    pass


class LLMAuthError(LLMError):
    """LLM 认证错误 (401)"""
    pass


class LLMRateLimitError(LLMError):
    """LLM 速率限制错误 (429)"""
    pass


# ========== API 层异常 ==========

class APIError(AgentAppError):
    """API 层错误"""
    pass


class SessionNotFoundError(APIError):
    """会话未找到"""
    pass


class SessionCreateError(APIError):
    """会话创建失败"""
    pass
