"""
============================================================================
数据访问层(Repository) - 会话/消息/工具调用/执行日志的 CRUD 封装
============================================================================
将数据库操作与业务逻辑解耦，提供统一的异步数据访问接口。
"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Session, Message, ToolCallRecord, ExecutionLog
from app.core.logger import logger


# ==================== 会话 Repository ====================

class SessionRepository:
    """会话数据访问层"""

    @staticmethod
    async def create(db: AsyncSession, title: str = "新会话") -> Session:
        """创建新会话"""
        session = Session(
            id=uuid.uuid4().hex[:16],
            title=title,
            status="active",
        )
        db.add(session)
        await db.flush()
        logger.debug(f"创建会话: {session.id}")
        return session

    @staticmethod
    async def get_by_id(db: AsyncSession, session_id: str) -> Optional[Session]:
        """根据ID获取会话"""
        result = await db.execute(
            select(Session).where(Session.id == session_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_all(
        db: AsyncSession, limit: int = 20, offset: int = 0
    ) -> List[Session]:
        """分页获取会话列表，按更新时间倒序"""
        result = await db.execute(
            select(Session)
            .order_by(Session.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_status(
        db: AsyncSession, session_id: str, status: str
    ) -> None:
        """更新会话状态"""
        session = await SessionRepository.get_by_id(db, session_id)
        if session:
            session.status = status
            session.updated_at = datetime.utcnow()
            await db.flush()

    @staticmethod
    async def delete(db: AsyncSession, session_id: str) -> bool:
        """删除会话（级联删除关联消息和记录）"""
        session = await SessionRepository.get_by_id(db, session_id)
        if session:
            await db.delete(session)
            await db.flush()
            logger.debug(f"删除会话: {session_id}")
            return True
        return False


# ==================== 消息 Repository ====================

class MessageRepository:
    """消息数据访问层"""

    @staticmethod
    async def add(
        db: AsyncSession,
        session_id: str,
        role: str,
        content: str,
        token_count: int = 0,
    ) -> Message:
        """添加一条消息到会话中"""
        msg = Message(
            id=uuid.uuid4().hex[:16],
            session_id=session_id,
            role=role,
            content=content,
            token_count=token_count,
        )
        db.add(msg)
        await db.flush()
        return msg

    @staticmethod
    async def get_by_session(
        db: AsyncSession, session_id: str, limit: int = 50
    ) -> List[Message]:
        """获取指定会话的消息列表（按时间正序）"""
        result = await db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())


# ==================== 工具调用记录 Repository ====================

class ToolCallRepository:
    """工具调用记录数据访问层"""

    @staticmethod
    async def record(
        db: AsyncSession,
        session_id: str,
        tool_name: str,
        tool_params: dict,
        tool_result: str,
        status: str,
        duration_ms: int = 0,
        retry_count: int = 0,
    ) -> ToolCallRecord:
        """记录一次工具调用"""
        record = ToolCallRecord(
            id=uuid.uuid4().hex[:16],
            session_id=session_id,
            tool_name=tool_name,
            tool_params=tool_params,
            tool_result=tool_result,
            status=status,
            duration_ms=duration_ms,
            retry_count=retry_count,
        )
        db.add(record)
        await db.flush()
        return record

    @staticmethod
    async def get_by_session(
        db: AsyncSession, session_id: str
    ) -> List[ToolCallRecord]:
        """获取指定会话的工具调用记录"""
        result = await db.execute(
            select(ToolCallRecord)
            .where(ToolCallRecord.session_id == session_id)
            .order_by(ToolCallRecord.created_at.asc())
        )
        return list(result.scalars().all())


# ==================== 执行日志 Repository ====================

class ExecutionLogRepository:
    """执行日志数据访问层"""

    @staticmethod
    async def log(
        db: AsyncSession,
        session_id: str,
        iteration: int,
        thought: str,
        action: str,
        action_input: dict,
        observation: str,
        duration_ms: int = 0,
    ) -> ExecutionLog:
        """记录一轮ReAct执行日志"""
        log_entry = ExecutionLog(
            id=uuid.uuid4().hex[:16],
            session_id=session_id,
            iteration=iteration,
            thought=thought,
            action=action,
            action_input=action_input,
            observation=observation,
            duration_ms=duration_ms,
        )
        db.add(log_entry)
        await db.flush()
        return log_entry

    @staticmethod
    async def get_by_session(
        db: AsyncSession, session_id: str
    ) -> List[ExecutionLog]:
        """获取指定会话的执行日志"""
        result = await db.execute(
            select(ExecutionLog)
            .where(ExecutionLog.session_id == session_id)
            .order_by(ExecutionLog.iteration.asc())
        )
        return list(result.scalars().all())
