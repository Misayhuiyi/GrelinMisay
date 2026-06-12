"""
============================================================================
会话管理接口 - 创建、列表、详情、删除会话
============================================================================
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.repository import (
    SessionRepository, MessageRepository,
    ToolCallRepository, ExecutionLogRepository,
)
from app.models.schemas import (
    SessionCreate, SessionInfo, SessionListResponse,
    SessionDetailResponse, DeleteResponse, ErrorResponse,
)

router = APIRouter(prefix="/api/sessions", tags=["会话管理"])


@router.post(
    "/create",
    response_model=SessionInfo,
    summary="创建新会话",
    description="创建一个新的对话会话，返回会话ID和元信息。"
)
async def create_session(
    body: SessionCreate = SessionCreate(),
    db: AsyncSession = Depends(get_db),
):
    """创建新会话"""
    session = await SessionRepository.create(db, title=body.title)
    await db.commit()
    return SessionInfo(
        id=session.id,
        title=session.title,
        status=session.status,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.get(
    "/list",
    response_model=SessionListResponse,
    summary="获取会话列表",
    description="分页获取所有会话，按更新时间倒序排列。"
)
async def list_sessions(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """获取会话列表"""
    sessions = await SessionRepository.list_all(db, limit=limit, offset=offset)
    return SessionListResponse(
        total=len(sessions),
        sessions=[
            SessionInfo(
                id=s.id, title=s.title, status=s.status,
                created_at=s.created_at, updated_at=s.updated_at,
            )
            for s in sessions
        ]
    )


@router.get(
    "/{session_id}",
    response_model=SessionDetailResponse,
    summary="获取会话详情",
    description="获取指定会话的详细信息，包括消息历史、工具调用记录和执行日志。"
)
async def get_session_detail(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取会话详情"""
    session = await SessionRepository.get_by_id(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"会话 '{session_id}' 不存在")

    messages = await MessageRepository.get_by_session(db, session_id)
    tool_calls = await ToolCallRepository.get_by_session(db, session_id)
    exec_logs = await ExecutionLogRepository.get_by_session(db, session_id)

    return SessionDetailResponse(
        session=SessionInfo(
            id=session.id, title=session.title, status=session.status,
            created_at=session.created_at, updated_at=session.updated_at,
        ),
        messages=[
            {"id": m.id, "role": m.role, "content": m.content,
             "token_count": m.token_count, "created_at": str(m.created_at)}
            for m in messages
        ],
        tool_calls=[
            {"id": t.id, "tool_name": t.tool_name, "tool_params": t.tool_params,
             "tool_result": t.tool_result, "status": t.status,
             "duration_ms": t.duration_ms, "retry_count": t.retry_count,
             "created_at": str(t.created_at)}
            for t in tool_calls
        ],
        execution_logs=[
            {"id": e.id, "iteration": e.iteration, "thought": e.thought,
             "action": e.action, "action_input": e.action_input,
             "observation": e.observation, "duration_ms": e.duration_ms,
             "created_at": str(e.created_at)}
            for e in exec_logs
        ],
    )


@router.delete(
    "/{session_id}",
    response_model=DeleteResponse,
    summary="删除会话",
    description="删除指定会话及其所有关联的消息、工具调用记录和执行日志。"
)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除会话"""
    success = await SessionRepository.delete(db, session_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"会话 '{session_id}' 不存在")
    await db.commit()
    return DeleteResponse(
        success=True,
        session_id=session_id,
        message="会话已删除"
    )
