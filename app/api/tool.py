"""
============================================================================
工具管理接口 - 工具列表、注册、注销
============================================================================
"""
from fastapi import APIRouter, HTTPException
from app.tools.registry import tool_registry
from app.models.schemas import ToolInfo, ToolListResponse, ErrorResponse

router = APIRouter(prefix="/api/tools", tags=["工具管理"])


@router.get(
    "/list",
    response_model=ToolListResponse,
    summary="获取所有可用工具",
    description="返回当前注册中心中全部工具的列表，包含名称、描述和参数Schema。"
)
async def list_tools():
    """
    获取所有已注册的工具列表。
    Agent 可以通过此接口了解可用的工具能力。
    """
    tools = []
    for tool_name in tool_registry.list_tools():
        tool = tool_registry.get(tool_name)
        tools.append(ToolInfo(
            name=tool.name,
            description=tool.description,
            parameters_schema=tool.parameters_schema,
        ))
    return ToolListResponse(tools=tools)


@router.get(
    "/{tool_name}",
    response_model=ToolInfo,
    summary="获取单个工具详情",
    description="根据工具名称获取工具的详细信息"
)
async def get_tool(tool_name: str):
    """获取指定工具的详情"""
    try:
        tool = tool_registry.get(tool_name)
        return ToolInfo(
            name=tool.name,
            description=tool.description,
            parameters_schema=tool.parameters_schema,
        )
    except Exception:
        raise HTTPException(status_code=404, detail=f"工具 '{tool_name}' 不存在")


@router.get(
    "/{tool_name}/schema",
    summary="获取工具的 OpenAI Schema",
    description="返回工具在 OpenAI 函数调用格式下的 Schema 定义"
)
async def get_tool_schema(tool_name: str):
    """获取工具的 OpenAI Schema"""
    try:
        tool = tool_registry.get(tool_name)
        return tool.to_openai_schema()
    except Exception:
        raise HTTPException(status_code=404, detail=f"工具 '{tool_name}' 不存在")
