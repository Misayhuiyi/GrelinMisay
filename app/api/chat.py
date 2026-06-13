"""
============================================================================
对话接口 - 发起ReAct对话的核心API
============================================================================
接收用户消息，驱动 ReAct 引擎执行完整推理，返回最终答案和推理过程。
需要 Bearer Token 鉴权，Agent 会感知当前对话用户身份。
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.models import User
from app.db.repository import (
    SessionRepository, MessageRepository,
    ToolCallRepository, ExecutionLogRepository,
)
from app.agent.react_engine import react_engine
from app.models.schemas import ChatRequest, ChatResponse, ReactionStep
from app.api.g_auth import get_current_user
from app.core.logger import logger

router = APIRouter(prefix="/api/chat", tags=["对话"])


@router.post(
    "/send",
    response_model=ChatResponse,
    summary="发送对话消息",
    description=(
        "向AI Agent发送一条消息，驱动ReAct推理引擎执行完整的"
        "思考-行动-观测循环，返回最终答案和推理过程。"
        "如果未指定session_id，系统会自动创建新会话。"
    )
)
async def chat_send(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    核心对话接口（需要登录）：
    1. 验证 Token 获取当前用户
    2. 创建/获取会话（关联用户）
    3. 加载历史消息
    4. 驱动 ReAct 引擎（注入用户上下文）
    5. 持久化结果
    """
    # ---------- 1. 获取或创建会话 ----------
    if request.session_id:
        session = await SessionRepository.get_by_id(db, request.session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"会话 '{request.session_id}' 不存在"
            )
    else:
        session = await SessionRepository.create(
            db,
            title=f"{current_user.nickname}的对话",
        )
        # 关联用户ID到会话元数据
        session.metadata_json = {"user_id": current_user.id}
        await db.flush()

    session_id = session.id

    # ---------- 2. 加载历史消息 ----------
    history_messages = await MessageRepository.get_by_session(db, session_id)
    conversation_history = [
        {"role": m.role, "content": m.content}
        for m in history_messages
    ]

    # ---------- 3. 保存用户消息 ----------
    await MessageRepository.add(
        db, session_id, "user", request.message,
        token_count=len(request.message)
    )
    await db.flush()

    # ---------- 4. 构建用户上下文 ----------
    user_context = {
        "user_id": current_user.id,
        "nickname": current_user.nickname,
        "phone": current_user.phone,
    }

    # ---------- 5. 持久化回调函数 ----------
    async def on_tool_call(tool_name, tool_params, tool_result, status, duration_ms):
        """工具调用回调：写入数据库"""
        await ToolCallRepository.record(
            db, session_id, tool_name, tool_params, tool_result, status, duration_ms
        )

    async def on_execution_log(iteration, thought, action, action_input, observation, duration_ms):
        """执行日志回调：写入数据库"""
        await ExecutionLogRepository.log(
            db, session_id, iteration, thought, action, action_input, observation, duration_ms
        )

    # ---------- 6. 驱动 ReAct 引擎 ----------
    logger.info(f"[API] 用户 {current_user.nickname}({current_user.id}) 在会话 {session_id} 发送消息: {request.message[:50]}...")
    try:
        result = await react_engine.run(
            user_message=request.message,
            conversation_history=conversation_history,
            on_tool_call=on_tool_call,
            on_execution_log=on_execution_log,
            user_context=user_context,
        )
    except Exception as e:
        logger.error(f"[API] ReAct引擎执行失败: {e}", exc_info=True)
        # 保存错误信息
        error_msg = f"抱歉，处理您的请求时发生了错误: {e}"
        await MessageRepository.add(db, session_id, "assistant", error_msg)
        await SessionRepository.update_status(db, session_id, "error")
        await db.commit()
        raise HTTPException(status_code=500, detail=str(e))

    # ---------- 7. 保存AI回复 ----------
    answer = result["answer"]
    await MessageRepository.add(
        db, session_id, "assistant", answer,
        token_count=len(answer)
    )

    # ---------- 8. 更新会话状态 ----------
    await SessionRepository.update_status(db, session_id, "active")
    await db.commit()

    # ---------- 9. 构建响应 ----------
    return ChatResponse(
        session_id=session_id,
        message=answer,
        reaction_steps=[
            ReactionStep(
                iteration=s["iteration"],
                thought=s["thought"],
                action=s["action"],
                action_input=s["action_input"],
                observation=s["observation"],
                duration_ms=s["duration_ms"],
            )
            for s in result.get("steps", [])
        ],
        tool_calls_count=result.get("tool_calls_count", 0),
        total_duration_ms=result.get("total_duration_ms", 0),
    )
