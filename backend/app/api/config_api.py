"""配置管理 API —— 模型与外部服务的配置。"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/models")
async def list_models():
    """列出所有已配置的模型 Provider 及其模型。"""
    raise NotImplementedError


@router.put("/models/{provider_id}")
async def update_model_config(provider_id: str, config: dict):
    """更新某个模型 Provider 的配置（API Key、endpoint 等）。"""
    raise NotImplementedError


@router.get("/services")
async def list_services():
    """列出所有外部服务配置（TTS、ASR、视觉 等）。"""
    raise NotImplementedError
