"""
GrelinMisay 用户 API
个人信息查询与更新
"""
from fastapi import APIRouter, Depends, HTTPException

from app.db.models import User
from app.api.g_auth import get_current_user
from app.api.g_schemas import APIResponse, UpdateProfileRequest

router = APIRouter(prefix="/api/users", tags=["用户"])


@router.get("/me", response_model=APIResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户个人信息"""
    return APIResponse(data={
        "id": current_user.id,
        "nickname": current_user.nickname,
        "phone": current_user.phone,
        "avatar": current_user.avatar,
        "bio": current_user.bio,
        "gender": current_user.gender,
        "birthday": str(current_user.birthday) if current_user.birthday else None,
    })


@router.put("/me", response_model=APIResponse)
async def update_me(
    req: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
):
    """更新个人信息"""
    if req.nickname is not None:
        current_user.nickname = req.nickname
    if req.avatar is not None:
        current_user.avatar = req.avatar
    if req.bio is not None:
        current_user.bio = req.bio
    if req.gender is not None:
        current_user.gender = req.gender
    if req.birthday is not None:
        from datetime import datetime
        current_user.birthday = datetime.fromisoformat(req.birthday)

    return APIResponse(message="更新成功")