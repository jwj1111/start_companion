"""START Companion —— 主程序入口。"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config.settings import get_settings
from app.api import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动与关闭逻辑。"""
    settings = get_settings()
    logger.info(f"START Companion 启动中... (env={settings.environment})")

    # TODO: 启动时初始化各项服务
    # - 记忆层连接
    # - 向量数据库连接
    # - 模型 Provider 预热

    yield

    # TODO: 关闭时清理资源
    logger.info("START Companion 正在关闭...")


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用。"""
    settings = get_settings()

    app = FastAPI(
        title="START Companion",
        description="面向腾讯 START 云游戏的 START 情感陪伴 Agent",
        version="0.1.0",
        lifespan=lifespan,
    )

    # 跨域
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册 API 路由
    app.include_router(api_router, prefix="/api")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
