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
