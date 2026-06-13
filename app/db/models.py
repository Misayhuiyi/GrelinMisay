"""
============================================================================
ORM 模型定义 - 会话/消息/工具调用/执行日志
============================================================================
使用 SQLAlchemy ORM 定义四张核心表：
  1. sessions      - 会话表（会话元信息）
  2. messages      - 消息表（对话历史中的每条消息）
  3. tool_calls    - 工具调用记录表（每次工具调用的入参/出参/状态）
  4. execution_logs - 任务执行日志表（每轮ReAct循环的详细日志）
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.db.database import Base


def generate_uuid() -> str:
    """生成带前缀的UUID，便于区分不同实体类型"""
    return uuid.uuid4().hex[:16]


# ==================== 会话表 ====================

class Session(Base):
    """会话表 - 记录每次对话会话的元信息"""
    __tablename__ = "sessions"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    title = Column(String(200), default="新会话", comment="会话标题")
    status = Column(String(20), default="active", comment="active | completed | error")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    metadata_json = Column(JSON, default=dict, comment="扩展元数据")

    # 关联消息
    messages = relationship("Message", back_populates="session", order_by="Message.created_at")


# ==================== 消息表 ====================

class Message(Base):
    """消息表 - 记录对话中的每条消息（用户提问 & AI回复）"""
    __tablename__ = "messages"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    session_id = Column(String(32), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False, comment="user | assistant | system | tool")
    content = Column(Text, nullable=False, comment="消息内容")
    token_count = Column(Integer, default=0, comment="Token估算数")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关联
    session = relationship("Session", back_populates="messages")


# ==================== 工具调用记录表 ====================

class ToolCallRecord(Base):
    """工具调用记录表 - 记录每次工具调用的详细信息"""
    __tablename__ = "tool_calls"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    session_id = Column(String(32), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(String(32), nullable=True, comment="关联的消息ID")
    tool_name = Column(String(100), nullable=False, comment="工具名称")
    tool_params = Column(JSON, default=dict, comment="调用参数(JSON)")
    tool_result = Column(Text, default="", comment="调用结果")
    status = Column(String(20), default="pending", comment="pending | success | error")
    duration_ms = Column(Integer, default=0, comment="调用耗时(毫秒)")
    retry_count = Column(Integer, default=0, comment="重试次数")
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================== 任务执行日志表 ====================

class ExecutionLog(Base):
    """执行日志表 - 记录每轮ReAct推理循环的详细执行过程"""
    __tablename__ = "execution_logs"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    session_id = Column(String(32), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    iteration = Column(Integer, nullable=False, comment="ReAct循环轮次(从1开始)")
    thought = Column(Text, default="", comment="思考内容(Thought)")
    action = Column(String(100), default="", comment="行动(Action): 工具名或'final_answer'")
    action_input = Column(JSON, default=dict, comment="行动输入(Action Input)")
    observation = Column(Text, default="", comment="观测结果(Observation)")
    duration_ms = Column(Integer, default=0, comment="本轮耗时(毫秒)")
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================== GrelinMisay 业务模型 ====================

class User(Base):
    """用户表"""
    __tablename__ = "g_users"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    phone = Column(String(20), unique=True, nullable=False, index=True, comment="手机号")
    password_hash = Column(String(128), nullable=False, comment="密码哈希")
    nickname = Column(String(50), nullable=False, comment="昵称")
    avatar = Column(String(500), default="", comment="头像URL")
    bio = Column(String(200), default="", comment="个人简介")
    gender = Column(String(10), default="secret", comment="male|female|secret")
    birthday = Column(DateTime, nullable=True, comment="生日")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Goal(Base):
    """目标表"""
    __tablename__ = "g_goals"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), ForeignKey("g_users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False, comment="目标标题")
    description = Column(Text, default="", comment="目标描述")
    goal_type = Column(String(20), default="personal", comment="personal|team")
    priority = Column(String(10), default="medium", comment="high|medium|low")
    deadline = Column(DateTime, nullable=True, comment="截止时间")
    progress = Column(Float, default=0.0, comment="进度 0-100")
    status = Column(String(20), default="active", comment="active|completed|archived")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    members = relationship("GoalMember", back_populates="goal", cascade="all, delete-orphan")


class GoalMember(Base):
    """目标成员表"""
    __tablename__ = "g_goal_members"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    goal_id = Column(String(32), ForeignKey("g_goals.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(32), ForeignKey("g_users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), default="member", comment="creator|member")
    status = Column(String(20), default="active", comment="active|left")
    joined_at = Column(DateTime, default=datetime.utcnow)

    goal = relationship("Goal", back_populates="members")


class TrainingRecord(Base):
    """训练记录表"""
    __tablename__ = "g_training_records"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), ForeignKey("g_users.id", ondelete="CASCADE"), nullable=False, index=True)
    training_date = Column(DateTime, nullable=False, comment="训练日期")
    body_part = Column(String(50), default="", comment="训练部位")
    duration = Column(Integer, default=0, comment="训练时长(分钟)")
    notes = Column(Text, default="", comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow)

    sets = relationship("TrainingSet", back_populates="record", cascade="all, delete-orphan", order_by="TrainingSet.set_order")


class TrainingSet(Base):
    """训练组详情表"""
    __tablename__ = "g_training_sets"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    record_id = Column(String(32), ForeignKey("g_training_records.id", ondelete="CASCADE"), nullable=False, index=True)
    set_order = Column(Integer, nullable=False, comment="组序号")
    action_name = Column(String(100), nullable=False, comment="动作名称")
    reps = Column(Float, default=0, comment="次数(0表示力竭)")
    weight = Column(Float, default=0.0, comment="重量(kg)")
    rest_seconds = Column(Integer, default=60, comment="组间休息(秒)")
    feeling = Column(String(20), default="normal", comment="hard|normal|easy")
    notes = Column(Text, default="", comment="备注")

    record = relationship("TrainingRecord", back_populates="sets")


class CalendarEvent(Base):
    """日历事件表"""
    __tablename__ = "g_calendar_events"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), ForeignKey("g_users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(20), nullable=False, comment="goal|training|memorial|social")
    title = Column(String(200), nullable=False, comment="事件标题")
    description = Column(Text, default="", comment="事件描述")
    start_time = Column(DateTime, nullable=False, comment="开始时间")
    end_time = Column(DateTime, nullable=True, comment="结束时间")
    source_id = Column(String(32), default="", comment="来源数据ID")
    color = Column(String(20), default="#10B981", comment="卡片颜色")
    created_at = Column(DateTime, default=datetime.utcnow)


class AIChatMessage(Base):
    """AI对话消息表"""
    __tablename__ = "g_ai_chat_messages"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), ForeignKey("g_users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False, comment="user|assistant")
    content = Column(Text, nullable=False, comment="消息内容")
    created_at = Column(DateTime, default=datetime.utcnow)
