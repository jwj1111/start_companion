"""WebSocket API —— 实时语音与流式通信。"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

router = APIRouter()


@router.websocket("/voice/{session_id}")
async def voice_stream(websocket: WebSocket, session_id: str):
    """
    实时语音交互的 WebSocket 通道。

    协议说明：
    - 客户端发送：音频帧（二进制） 或 控制消息（JSON）
    - 服务端发送：TTS 音频帧（二进制） 或 文本回复（JSON）

    JSON 消息格式：
    {
        "type": "control" | "text" | "state",
        "data": {...}
    }
    """
    await websocket.accept()
    logger.info(f"语音 WebSocket 已连接: session={session_id}")

    try:
        while True:
            # TODO: 实现语音流水线
            # 1. 接收音频帧 / 文本
            # 2. 若是音频则 ASR -> 文本
            # 3. 路由至 LangGraph
            # 4. TTS -> 音频流，回传前端
            data = await websocket.receive()
            # 处理...
    except WebSocketDisconnect:
        logger.info(f"语音 WebSocket 已断开: session={session_id}")


@router.websocket("/events/{session_id}")
async def event_stream(websocket: WebSocket, session_id: str):
    """
    实时事件通道（截图数据、游戏状态、Agent 动作指令等）。

    用途：
    - 接收前端上传的截图数据
    - 向前端推送 Agent 状态变化
    - 触发 Live2D 动作
    """
    await websocket.accept()
    logger.info(f"事件 WebSocket 已连接: session={session_id}")

    try:
        while True:
            data = await websocket.receive_json()
            # TODO: 处理事件
    except WebSocketDisconnect:
        logger.info(f"事件 WebSocket 已断开: session={session_id}")
