"""
GrelinMisay 训练 API
训练记录 CRUD + 动作列表
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.db.models import User, TrainingRecord, TrainingSet
from app.api.g_auth import get_current_user
from app.api.g_schemas import APIResponse, TrainingRecordRequest

router = APIRouter(prefix="/api/training", tags=["训练"])

# 预置训练动作库
ACTIONS = {
    "胸部": ["杠铃卧推", "哑铃卧推", "上斜卧推", "哑铃飞鸟", "绳索夹胸", "俯卧撑", "双杠臂屈伸"],
    "背部": ["引体向上", "杠铃划船", "哑铃划船", "高位下拉", "坐姿划船", "硬拉"],
    "肩部": ["杠铃推举", "哑铃推举", "侧平举", "前平举", "俯身飞鸟", "面拉"],
    "手臂": ["杠铃弯举", "哑铃弯举", "锤式弯举", "三头下压", "窄距卧推", "臂屈伸"],
    "腿臀": ["深蹲", "腿举", "腿弯举", "腿屈伸", "罗马尼亚硬拉", "臀推", "弓步蹲"],
    "核心": ["卷腹", "平板支撑", "悬垂举腿", "俄罗斯转体", "仰卧抬腿"],
    "有氧": ["跑步", "椭圆机", "动感单车", "划船机", "跳绳", "快走"],
}


@router.get("/actions", response_model=APIResponse)
async def get_actions():
    """获取训练动作分类列表"""
    return APIResponse(data={"actions": ACTIONS})


@router.get("/records", response_model=APIResponse)
async def list_records(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取训练记录列表"""
    result = await db.execute(
        select(TrainingRecord)
        .where(TrainingRecord.user_id == current_user.id)
        .options(selectinload(TrainingRecord.sets))
        .order_by(TrainingRecord.training_date.desc())
        .limit(30)
    )
    records = result.scalars().all()
    return APIResponse(data={
        "items": [
            {
                "id": r.id,
                "training_date": str(r.training_date),
                "body_part": r.body_part,
                "duration": r.duration,
                "notes": r.notes,
                "sets": [
                    {
                        "set_order": s.set_order,
                        "action_name": s.action_name,
                        "reps": s.reps,
                        "weight": s.weight,
                        "rest_seconds": s.rest_seconds,
                        "feeling": s.feeling,
                        "notes": s.notes,
                    }
                    for s in r.sets
                ],
                "created_at": str(r.created_at),
            }
            for r in records
        ]
    })


@router.post("/records", response_model=APIResponse)
async def create_record(
    req: TrainingRecordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建训练记录"""
    record = TrainingRecord(
        id=uuid.uuid4().hex[:16],
        user_id=current_user.id,
        training_date=datetime.fromisoformat(req.training_date),
        body_part=req.body_part,
        duration=req.duration,
        notes=req.notes,
    )
    db.add(record)
    await db.flush()

    for s in req.sets:
        ts = TrainingSet(
            id=uuid.uuid4().hex[:16],
            record_id=record.id,
            set_order=s.set_order,
            action_name=s.action_name,
            reps=s.reps,
            weight=s.weight,
            rest_seconds=s.rest_seconds,
            feeling=s.feeling,
            notes=s.notes,
        )
        db.add(ts)
    await db.flush()
    return APIResponse(data={"id": record.id}, message="训练记录保存成功")