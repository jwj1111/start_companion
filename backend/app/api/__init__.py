"""API 路由注册入口。"""

from fastapi import APIRouter

from app.api.chat import router as chat_router
from app.api.agent import router as agent_router
from app.api.config_api import router as config_router
from app.api.websocket import router as ws_router
from app.api.memory import router as memory_router

router = APIRouter()

router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(agent_router, prefix="/agent", tags=["agent"])
router.include_router(config_router, prefix="/config", tags=["config"])
router.include_router(ws_router, prefix="/ws", tags=["websocket"])
router.include_router(memory_router, prefix="/memory", tags=["memory"])
