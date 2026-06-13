"""
GrelinMisay 统一 Pydantic Schema
定义所有 API 的请求/响应模型
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== 通用响应 ====================

class APIResponse(BaseModel):
    """统一 API 响应格式"""
    code: int = 0
    message: str = "ok"
    data: Optional[dict] = None


# ==================== 认证 ====================

class SendCodeRequest(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", max_length=11)


class LoginRequest(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    password: str = Field(..., min_length=6)


class LoginByCodeRequest(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    code: str = Field(..., min_length=4, max_length=6)


class RegisterRequest(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    password: str = Field(..., min_length=6)
    nickname: str = Field(..., min_length=1, max_length=20)


class AuthResponse(BaseModel):
    token: str
    user_id: str
    nickname: str
    phone: str


# ==================== 用户 ====================

class UserProfileResponse(BaseModel):
    id: str
    nickname: str
    phone: str
    avatar: str
    bio: str
    gender: str
    birthday: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    nickname: Optional[str] = Field(None, max_length=20)
    avatar: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=200)
    gender: Optional[str] = None
    birthday: Optional[str] = None


# ==================== 目标 ====================

class GoalCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    priority: str = "medium"
    deadline: Optional[str] = None


class GoalResponse(BaseModel):
    id: str
    title: str
    description: str
    priority: str
    deadline: Optional[str] = None
    progress: float = 0.0
    status: str = "active"
    created_at: str


# ==================== 训练 ====================

class TrainingSetRequest(BaseModel):
    set_order: int
    action_name: str
    reps: float = 0
    weight: float = 0.0
    rest_seconds: int = 60
    feeling: str = "normal"
    notes: str = ""


class TrainingRecordRequest(BaseModel):
    training_date: str
    body_part: str = ""
    duration: int = 0
    notes: str = ""
    sets: List[TrainingSetRequest] = []


class TrainingRecordResponse(BaseModel):
    id: str
    training_date: str
    body_part: str
    duration: int
    notes: str
    sets: list = []
    created_at: str


# ==================== 日历 ====================

class CalendarEventResponse(BaseModel):
    id: str
    event_type: str
    title: str
    description: str
    start_time: str
    end_time: Optional[str] = None
    color: str


# ==================== AI 对话 ====================

class AIChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class AIChatResponse(BaseModel):
    reply: str
    conversation_id: Optional[str] = None