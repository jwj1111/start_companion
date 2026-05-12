"""聊天 API —— 基于文本的对话接口。"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter()


class ChatRequest(BaseModel):
    """聊天请求体。"""
    agent_id: str
    message: str
    session_id: str | None = None
    # 用户微调参数（可选覆盖预设）
    user_overrides: dict | None = None


class ChatResponse(BaseModel):
    """聊天响应体。"""
    reply: str
    session_id: str
    emotion: str | None = None
    action: str | None = None  # 触发 Live2D 表情 / 动作的标记


@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """发送一条文本消息，获取 AI 回复。"""
    # TODO: 路由到 LangGraph 编排器
    # 1. 加载 Agent 配置（预设 + 用户微调）
    # 2. 调用 LangGraph 图执行
    # 3. 返回带有情感 / 动作元数据的回复
    raise NotImplementedError("需要对接 LangGraph 编排器")


@router.get("/history/{session_id}")
async def get_history(session_id: str, limit: int = 50):
    """获取某个会话的聊天历史。"""
    # TODO: 从记忆层查询
    raise NotImplementedError
