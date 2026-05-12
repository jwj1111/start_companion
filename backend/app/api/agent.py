"""Agent 管理 API —— AI Agent 的增删改查。"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class AgentInfo(BaseModel):
    """Agent 信息。"""
    agent_id: str
    name: str
    description: str
    preset_id: str
    # 当前用户对该 Agent 的自定义配置 ID
    custom_config_id: str | None = None


@router.get("/list")
async def list_agents():
    """列出所有可用的 Agent（含系统预设与用户创建的）。"""
    # TODO: 扫描 presets/ 和 custom/ 目录
    raise NotImplementedError


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    """获取 Agent 的详细信息（含合并后的配置）。"""
    raise NotImplementedError


@router.post("/{agent_id}/customize")
async def customize_agent(agent_id: str, overrides: dict):
    """保存用户对某个 Agent 的微调（存放在 custom/ 空间中）。"""
    # 注意：用户微调保存在 custom/ 目录，不会修改 presets/ 下的原版预设
    raise NotImplementedError
