"""
GrelinMisay 认证 API
手机号登录/注册/验证码
"""
import hashlib
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import User
from app.api.g_schemas import (
    SendCodeRequest, LoginRequest, RegisterRequest,
    AuthResponse, APIResponse,
)
from app.core.logger import logger

router = APIRouter(prefix="/api/auth", tags=["认证"])

# 简易验证码存储（生产环境应使用 Redis）
_verify_codes = {}


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _generate_token() -> str:
    return uuid.uuid4().hex + uuid.uuid4().hex


# 简易 Token 存储（生产环境应使用 JWT+Redis）
_token_store = {}


async def get_current_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录或 Token 已过期")
    token = authorization[7:]
    user_id = _token_store.get(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


@router.post("/send_code", response_model=APIResponse)
async def send_code(req: SendCodeRequest):
    """发送验证码（模拟）"""
    code = "123456"
    _verify_codes[req.phone] = {
        "code": code,
        "expires": datetime.utcnow() + timedelta(minutes=5),
    }
    logger.info(f"验证码已发送到 {req.phone}: {code}")
    return APIResponse(data={"code": code, "message": "验证码已发送（模拟）"})


@router.post("/register", response_model=APIResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """注册账号"""
    # 检查手机号是否已注册
    result = await db.execute(select(User).where(User.phone == req.phone))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该手机号已注册")

    user = User(
        id=uuid.uuid4().hex[:16],
        phone=req.phone,
        password_hash=_hash_password(req.password),
        nickname=req.nickname,
    )
    db.add(user)
    await db.flush()

    token = _generate_token()
    _token_store[token] = user.id

    logger.info(f"新用户注册: {req.phone} ({user.id})")
    return APIResponse(data={
        "token": token,
        "user_id": user.id,
        "nickname": user.nickname,
        "phone": user.phone,
    })


@router.post("/login", response_model=APIResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """手机号+密码登录"""
    result = await db.execute(select(User).where(User.phone == req.phone))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="手机号未注册")
    if user.password_hash != _hash_password(req.password):
        raise HTTPException(status_code=400, detail="密码错误")

    token = _generate_token()
    _token_store[token] = user.id

    logger.info(f"用户登录: {req.phone}")
    return APIResponse(data={
        "token": token,
        "user_id": user.id,
        "nickname": user.nickname,
        "phone": user.phone,
    })