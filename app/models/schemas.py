"""
============================================================================
Pydantic 请求/响应数据模型 - API接口的数据契约
============================================================================
定义所有API接口的请求体和响应体的数据结构。
"""
from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field


# ==================== 对话相关 ====================

class ChatRequest(BaseModel):
    """对话请求"""
    session_id: Optional[str] = Field(None, description="会话ID，为空则创建新会话")
    message: str = Field(..., min_length=1, max_length=10000, description="用户消息")
    stream: bool = Field(False, description="是否流式返回（暂不支持）")


class ReactionStep(BaseModel):
    """单轮ReAct推理步骤"""
    iteration: int
    thought: str
    action: str
    action_input: Dict[str, Any] = {}
    observation: str
    duration_ms: int


class ChatResponse(BaseModel):
    """对话响应"""
    session_id: str
    message: str                          # 最终回复
    reaction_steps: List[ReactionStep] = []  # ReAct推理过程
    tool_calls_count: int = 0
    total_duration_ms: int = 0


# ==================== 会话相关 ====================

class SessionCreate(BaseModel):
    """创建会话请求"""
    title: str = Field("新会话", max_length=200)


class SessionInfo(BaseModel):
    """会话信息"""
    id: str
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    metadata_json: dict = {}

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """会话列表响应"""
    total: int
    sessions: List[SessionInfo]


class SessionDetailResponse(BaseModel):
    """会话详情（含消息历史）"""
    session: SessionInfo
    messages: List[Dict[str, Any]] = []
    tool_calls: List[Dict[str, Any]] = []
    execution_logs: List[Dict[str, Any]] = []


# ==================== 消息相关 ====================

class MessageInfo(BaseModel):
    """消息信息"""
    id: str
    role: str
    content: str
    token_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 工具相关 ====================

class ToolInfo(BaseModel):
    """工具信息"""
    name: str
    description: str
    parameters_schema: Dict[str, Any]


class ToolListResponse(BaseModel):
    """工具列表响应"""
    tools: List[ToolInfo]


class ToolCallInfo(BaseModel):
    """工具调用记录"""
    id: str
    tool_name: str
    tool_params: dict
    tool_result: str
    status: str
    duration_ms: int
    retry_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 通用响应 ====================

class ErrorResponse(BaseModel):
    """统一错误响应"""
    error_code: str
    message: str
    detail: str = ""


class HealthResponse(BaseModel):
    """健康检查"""
    status: str = "ok"
    version: str = "1.0.0"
    model: str = ""
    tools_count: int = 0


class DeleteResponse(BaseModel):
    """删除响应"""
    success: bool
    session_id: str
    message: str
