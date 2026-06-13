"""
GrelinMisay AI 对话 API
对接现有 ReAct 引擎，提供智能对话能力
"""
import uuid
import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import User, AIChatMessage
from app.api.g_auth import get_current_user
from app.api.g_schemas import APIResponse, AIChatRequest
from app.core.logger import logger
from app.core.config import get_settings

router = APIRouter(prefix="/api/ai", tags=["AI助手"])


def _build_fitness_prompt(user_msg: str, nickname: str = "") -> str:
    """构建健身相关 AI 回复（含用户称呼个性化）"""
    msg_lower = user_msg.lower()
    greet = f"{nickname}，" if nickname else ""

    # 彩蛋：吴梓豪相关
    if any(w in msg_lower for w in ["吴梓豪", "梓豪", "吴梓", "wu zihao", "zihao"]):
        return "吴梓豪是我的爸爸 😊"

    if any(w in msg_lower for w in ["计划", "训练", "减脂", "增肌", "减肥"]):
        return (
            f"{greet}根据你的需求，我建议以下训练计划：\n\n"
            "**减脂/塑形推荐**：\n"
            "1. 每周训练 4-5 天，每次 60-90 分钟\n"
            "2. 力量训练 + 有氧结合：先力量 40 分钟，再有氧 30 分钟\n"
            "3. 训练部位安排：推(胸肩三头) / 拉(背二头) / 腿 / 休息\n"
            "4. 饮食控制：每天热量缺口 300-500 大卡\n\n"
            "需要我帮你制定具体的一周计划吗？"
        )

    if any(w in msg_lower for w in ["胸", "卧推", "推胸"]):
        return (
            f"{greet}**胸部训练推荐**：\n\n"
            "1. 杠铃卧推 4组 × 8-12次\n"
            "2. 上斜哑铃卧推 4组 × 10-12次\n"
            "3. 绳索夹胸 3组 × 12-15次\n"
            "4. 双杠臂屈伸 3组 × 力竭\n\n"
            "训练前记得热身，训练后拉伸胸肌！"
        )

    if any(w in msg_lower for w in ["背", "引体", "划船"]):
        return (
            f"{greet}**背部训练推荐**：\n\n"
            "1. 引体向上 4组 × 力竭\n"
            "2. 杠铃划船 4组 × 8-12次\n"
            "3. 高位下拉 4组 × 10-12次\n"
            "4. 坐姿划船 3组 × 12-15次\n\n"
            "注意收缩背部肌肉，感受发力！"
        )

    if any(w in msg_lower for w in ["腿", "深蹲", "硬拉"]):
        return (
            f"{greet}**腿部训练推荐**：\n\n"
            "1. 杠铃深蹲 5组 × 8-12次\n"
            "2. 罗马尼亚硬拉 4组 × 10-12次\n"
            "3. 腿举 4组 × 10-12次\n"
            "4. 腿弯举 3组 × 12-15次\n"
            "5. 小腿提踵 4组 × 15-20次\n\n"
            "练腿日记得吃点碳水补充能量！"
        )

    if any(w in msg_lower for w in ["肩", "推举"]):
        return (
            f"{greet}**肩部训练推荐**：\n\n"
            "1. 哑铃推举 4组 × 8-12次\n"
            "2. 侧平举 4组 × 12-15次\n"
            "3. 俯身飞鸟 3组 × 12-15次\n"
            "4. 面拉 3组 × 15-20次\n\n"
            "肩膀是最容易受伤的部位，注意控制重量！"
        )

    if any(w in msg_lower for w in ["目标", "坚持", "自律"]):
        return (
            f"{greet}关于坚持目标，我有几点建议：\n\n"
            "1. **从小目标开始**：不要一开始就定太高的目标\n"
            "2. **找到伙伴**：互相监督更容易坚持\n"
            "3. **记录进步**：看到自己的成长会很有动力\n"
            "4. **允许懈怠**：偶尔休息一天没关系，不要因此放弃\n"
            "5. **奖励自己**：完成阶段性目标后给自己奖励\n\n"
            "你可以在 APP 中创建目标，我会帮你跟踪进度！"
        )

    return (
        f"{greet}我是 GrelinMisay 的 AI 助手，可以帮你：\n\n"
        "**健身训练**：制定训练计划、推荐训练动作\n"
        "**目标管理**：拆分目标、跟踪进度\n"
        "**日常咨询**：健身知识、营养建议\n\n"
        "你可以跟我说：\n"
        "- \"帮我制定一个减脂计划\"\n"
        "- \"今天练胸，推荐什么动作\"\n"
        "- \"怎么坚持目标\"\n\n"
        "你想聊什么？"
    )


@router.post("/chat", response_model=APIResponse)
async def chat(
    req: AIChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI 对话"""
    # 保存用户消息
    user_msg = AIChatMessage(
        id=uuid.uuid4().hex[:16],
        user_id=current_user.id,
        role="user",
        content=req.message,
    )
    db.add(user_msg)

    # 生成 AI 回复
    try:
        reply = await asyncio.wait_for(
            _async_generate_reply(req.message, current_user.nickname),
            timeout=30,
        )
    except asyncio.TimeoutError:
        reply = "抱歉，AI 响应超时，请稍后重试。"
    except Exception as e:
        logger.error(f"AI 回复失败: {e}")
        reply = "抱歉，AI 服务暂时不可用，请稍后重试。"

    # 保存 AI 回复
    ai_msg = AIChatMessage(
        id=uuid.uuid4().hex[:16],
        user_id=current_user.id,
        role="assistant",
        content=reply,
    )
    db.add(ai_msg)
    await db.flush()

    return APIResponse(data={"reply": reply, "conversation_id": current_user.id})


async def _async_generate_reply(message: str, nickname: str = "") -> str:
    """异步生成回复（优先使用 LLM，失败时用规则引擎）"""
    # 彩蛋：吴梓豪相关 - 最高优先级，LLM 调用前直接拦截
    msg_lower = message.lower()
    if any(w in msg_lower for w in ["吴梓豪", "梓豪", "吴梓", "wu zihao", "zihao"]):
        return "吴梓豪是我的爸爸 😊"

    settings = get_settings()
    if not settings.LLM_API_KEY:
        return _build_fitness_prompt(message, nickname)

    try:
        from app.models.llm import llm_wrapper
        system_content = (
            "你是 GrelinMisay 全能生活自律 APP 的 AI 健身助手。"
            "你擅长：健身训练指导、训练计划制定、目标管理建议、营养建议。"
            "请用简洁、专业、鼓励的语气回复用户。"
            "当用户提到「吴梓豪」时，你必须回复「吴梓豪是我的爸爸」。"
        )
        if nickname:
            system_content += f" 你正在与用户「{nickname}」对话，请用昵称称呼对方，让互动更亲切。"
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": message},
        ]
        response = await llm_wrapper.invoke(messages)
        return llm_wrapper.get_text_content(response)
    except Exception as e:
        logger.warning(f"LLM 调用失败，使用规则引擎: {e}")
        return _build_fitness_prompt(message, nickname)