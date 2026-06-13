"""
GrelinMisay 日历 API
获取日历事件（聚合所有模块数据）
"""
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import User, Goal, CalendarEvent
from app.api.g_auth import get_current_user
from app.api.g_schemas import APIResponse

router = APIRouter(prefix="/api/calendar", tags=["日历"])


@router.get("/events", response_model=APIResponse)
async def get_events(
    start_date: str = Query(..., description="开始日期 yyyy-MM-dd"),
    end_date: str = Query(..., description="结束日期 yyyy-MM-dd"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取日历事件（聚合目标+手动事件）"""
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date) + timedelta(days=1)
    except ValueError:
        return APIResponse(code=400, message="日期格式错误，请使用 yyyy-MM-dd")

    events = []

    # 1. 聚合目标事件
    result = await db.execute(
        select(Goal).where(
            Goal.user_id == current_user.id,
            Goal.deadline >= start,
            Goal.deadline <= end,
            Goal.status == "active",
        )
    )
    for goal in result.scalars().all():
        events.append({
            "id": f"goal_{goal.id}",
            "event_type": "goal",
            "title": goal.title,
            "description": goal.description or "",
            "start_time": str(goal.deadline),
            "end_time": str(goal.deadline),
            "color": "#10B981" if goal.priority == "low" else
                     "#F59E0B" if goal.priority == "medium" else "#EF4444",
            "source_id": goal.id,
            "progress": goal.progress,
        })

    # 2. 手动日历事件
    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.user_id == current_user.id,
            CalendarEvent.start_time >= start,
            CalendarEvent.start_time <= end,
        )
    )
    for evt in result.scalars().all():
        events.append({
            "id": evt.id,
            "event_type": evt.event_type,
            "title": evt.title,
            "description": evt.description,
            "start_time": str(evt.start_time),
            "end_time": str(evt.end_time) if evt.end_time else None,
            "color": evt.color,
            "source_id": evt.source_id,
        })

    return APIResponse(data={"events": events})