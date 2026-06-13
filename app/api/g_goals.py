"""
GrelinMisay 目标 API
个人目标 CRUD + 打卡
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import User, Goal
from app.api.g_auth import get_current_user
from app.api.g_schemas import APIResponse, GoalCreateRequest

router = APIRouter(prefix="/api/goals", tags=["目标"])


@router.get("", response_model=APIResponse)
async def list_goals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取目标列表"""
    result = await db.execute(
        select(Goal)
        .where(Goal.user_id == current_user.id)
        .order_by(Goal.created_at.desc())
    )
    goals = result.scalars().all()
    return APIResponse(data={
        "items": [
            {
                "id": g.id,
                "title": g.title,
                "description": g.description,
                "priority": g.priority,
                "deadline": str(g.deadline) if g.deadline else None,
                "progress": g.progress,
                "status": g.status,
                "created_at": str(g.created_at),
            }
            for g in goals
        ]
    })


@router.post("", response_model=APIResponse)
async def create_goal(
    req: GoalCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建目标"""
    goal = Goal(
        id=uuid.uuid4().hex[:16],
        user_id=current_user.id,
        title=req.title,
        description=req.description,
        priority=req.priority,
        deadline=datetime.fromisoformat(req.deadline) if req.deadline else None,
    )
    db.add(goal)
    await db.flush()
    return APIResponse(data={"id": goal.id}, message="创建成功")


@router.put("/{goal_id}", response_model=APIResponse)
async def update_goal(
    goal_id: str,
    req: GoalCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新目标"""
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id)
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="目标不存在")

    goal.title = req.title
    goal.description = req.description
    goal.priority = req.priority
    if req.deadline:
        goal.deadline = datetime.fromisoformat(req.deadline)
    await db.flush()
    return APIResponse(message="更新成功")


@router.delete("/{goal_id}", response_model=APIResponse)
async def delete_goal(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除目标"""
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id)
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="目标不存在")
    await db.delete(goal)
    await db.flush()
    return APIResponse(message="删除成功")


@router.post("/{goal_id}/checkin", response_model=APIResponse)
async def checkin_goal(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """目标打卡，进度+10%"""
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id)
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="目标不存在")
    if goal.status == "completed":
        raise HTTPException(status_code=400, detail="目标已完成")

    goal.progress = min(100, goal.progress + 10)
    if goal.progress >= 100:
        goal.status = "completed"
    await db.flush()
    return APIResponse(data={"progress": goal.progress}, message="打卡成功")