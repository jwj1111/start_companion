"""
记忆卡片 API —— 让用户可以审核、编辑、手动管理自己的记忆。

端点清单：
- GET    /memory/cards                列出卡片（按 status 过滤，分页）
- GET    /memory/cards/{id}           获取单张卡片
- POST   /memory/cards                手动添加一张卡片（直接 ACTIVE）
- PATCH  /memory/cards/{id}           编辑卡片内容 / 状态 / 标签
- DELETE /memory/cards/{id}           删除一张卡片
- POST   /memory/cards/{id}/approve   审核通过（pending → active）
- POST   /memory/cards/{id}/reject    审核拒绝（pending → rejected）
- POST   /memory/cards/{id}/archive   归档（active → archived）

所有端点均强制按 user_id 隔离。
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel

from memory.schema import MemoryCardStatus

router = APIRouter()


# === Pydantic 请求 / 响应 模型 ===

class MemoryCardCreate(BaseModel):
    """手动创建卡片请求体。"""
    agent_id: str
    content: str
    tags: list[str] = []


class MemoryCardUpdate(BaseModel):
    """编辑卡片请求体（所有字段可选）。"""
    content: str | None = None
    tags: list[str] | None = None
    status: MemoryCardStatus | None = None


class MemoryCardResponse(BaseModel):
    """卡片响应体（序列化 MemoryCard）。"""
    id: str
    user_id: str
    agent_id: str
    content: str
    tags: list[str]
    status: str
    source: str
    user_edited: bool
    editable: bool
    created_at: str
    updated_at: str
    recall_count: int


# === 路由 ===

@router.get("/cards", response_model=list[MemoryCardResponse])
async def list_cards(
    user_id: str,                               # TODO: 从鉴权中取，不要让前端传
    agent_id: str | None = None,
    status: MemoryCardStatus | None = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """列出当前用户的记忆卡片，支持按状态 / Agent 过滤。"""
    # TODO: 调用 MemoryManager.long_term.list_cards() 并序列化
    raise NotImplementedError


@router.get("/cards/{card_id}", response_model=MemoryCardResponse)
async def get_card(card_id: str, user_id: str):
    """获取单张卡片。"""
    # TODO: 调用 long_term.get_card(user_id, card_id)
    raise NotImplementedError


@router.post("/cards", response_model=MemoryCardResponse)
async def create_card(request: MemoryCardCreate, user_id: str):
    """用户手动添加一张卡片（直接 ACTIVE）。"""
    # TODO: 构造 MemoryCard(status=ACTIVE, source=USER_MANUAL)
    # 调用 manager.add_manual_card(card)
    raise NotImplementedError


@router.patch("/cards/{card_id}", response_model=MemoryCardResponse)
async def update_card(card_id: str, request: MemoryCardUpdate, user_id: str):
    """编辑卡片内容 / 状态 / 标签。若修改 content 会重新 embed。"""
    # TODO: 调用 long_term.update_card(user_id, card_id, updates, mark_user_edited=True)
    raise NotImplementedError


@router.delete("/cards/{card_id}")
async def delete_card(card_id: str, user_id: str):
    """彻底删除一张卡片（向量库 + 关系库同步删除）。"""
    # TODO: 调用 long_term.delete_card(user_id, card_id)
    raise NotImplementedError


# === 审核流程 ===

@router.post("/cards/{card_id}/approve", response_model=MemoryCardResponse)
async def approve_card(card_id: str, user_id: str):
    """审核通过：pending → active。"""
    # TODO: long_term.change_status(user_id, card_id, MemoryCardStatus.ACTIVE)
    raise NotImplementedError


@router.post("/cards/{card_id}/reject", response_model=MemoryCardResponse)
async def reject_card(card_id: str, user_id: str):
    """审核拒绝：pending → rejected。"""
    # TODO: long_term.change_status(user_id, card_id, MemoryCardStatus.REJECTED)
    raise NotImplementedError


@router.post("/cards/{card_id}/archive", response_model=MemoryCardResponse)
async def archive_card(card_id: str, user_id: str):
    """归档：active → archived。"""
    # TODO: long_term.change_status(user_id, card_id, MemoryCardStatus.ARCHIVED)
    raise NotImplementedError
