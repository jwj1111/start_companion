"""
TTS（语音合成）服务。

将 AI 生成的文本转为语音。
通过配置可切换多种 Provider：

1. edge_tts    - 微软 Edge TTS（免费，高质量）
2. openai_tts  - OpenAI TTS API（或任何兼容接口，例如司内 API）
3. tencent_tts - 腾讯云 TTS
4. custom_api  - 通用自定义 HTTP API（任意第三方 / 司内接口）

所有 Provider 都通过 config 切换，无需改代码。
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator

from loguru import logger


class BaseTTS(ABC):
    """TTS Provider 的抽象基类。"""

    @abstractmethod
    async def synthesize(self, text: str, voice_id: str = "", speed: float = 1.0) -> bytes:
        """将文本合成为完整音频字节流。"""
        ...

    @abstractmethod
    async def synthesize_stream(
        self, text: str, voice_id: str = "", speed: float = 1.0
    ) -> AsyncGenerator[bytes, None]:
        """流式合成 —— 逐段 yield 音频片段，降低延迟。"""
        ...


# ============================================================
# Provider: Edge TTS（免费）
# ============================================================
class EdgeTTS(BaseTTS):
    """微软 Edge TTS（免费，高质量）。"""

    def __init__(self, default_voice: str = "zh-CN-XiaoxiaoNeural", **kwargs):
        self.default_voice = default_voice

    async def synthesize(self, text: str, voice_id: str = "", speed: float = 1.0) -> bytes:
        import edge_tts

        voice = voice_id or self.default_voice
        rate = f"{int((speed - 1) * 100):+d}%"

        communicate = edge_tts.Communicate(text, voice, rate=rate)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data

    async def synthesize_stream(
        self, text: str, voice_id: str = "", speed: float = 1.0
    ) -> AsyncGenerator[bytes, None]:
        import edge_tts

        voice = voice_id or self.default_voice
        rate = f"{int((speed - 1) * 100):+d}%"

        communicate = edge_tts.Communicate(text, voice, rate=rate)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]


# ============================================================
# Provider: OpenAI 兼容的 TTS API
# 适用于: OpenAI TTS / 司内模型 API / 任何兼容 /v1/audio/speech 的接口
# ============================================================
class OpenAICompatibleTTS(BaseTTS):
    """
    OpenAI 兼容的 TTS API。

    适用于：
    - OpenAI 官方 API
    - 任何遵循 /v1/audio/speech 格式的司内 API
    - 具有 OpenAI 兼容 endpoint 的自行部署 TTS 服务

    配置示例：
        provider: openai_tts
        api_key: "sk-xxx"
        base_url: "https://internal.tencent.com/v1"  # 司内地址
        model: "tts-1"
        default_voice: "alloy"
    """

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "",
        model: str = "tts-1",
        default_voice: str = "alloy",
        **kwargs,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/") if base_url else "https://api.openai.com/v1"
        self.model = model
        self.default_voice = default_voice

    async def synthesize(self, text: str, voice_id: str = "", speed: float = 1.0) -> bytes:
        import httpx

        voice = voice_id or self.default_voice
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "input": text,
            "voice": voice,
            "speed": speed,
            "response_format": "mp3",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.base_url}/audio/speech",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            return resp.content

    async def synthesize_stream(
        self, text: str, voice_id: str = "", speed: float = 1.0
    ) -> AsyncGenerator[bytes, None]:
        import httpx

        voice = voice_id or self.default_voice
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "input": text,
            "voice": voice,
            "speed": speed,
            "response_format": "mp3",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/audio/speech",
                json=payload,
                headers=headers,
            ) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes(chunk_size=4096):
                    yield chunk


# ============================================================
# Provider: 腾讯云 TTS
# ============================================================
class TencentTTS(BaseTTS):
    """腾讯云 TTS Provider。"""

    def __init__(self, secret_id: str = "", secret_key: str = "", voice_type: int = 0, **kwargs):
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.voice_type = voice_type

    async def synthesize(self, text: str, voice_id: str = "", speed: float = 1.0) -> bytes:
        # TODO: 对接腾讯云 TTS API
        raise NotImplementedError("腾讯云 TTS 尚未实现")

    async def synthesize_stream(
        self, text: str, voice_id: str = "", speed: float = 1.0
    ) -> AsyncGenerator[bytes, None]:
        # TODO: 具体实现
        raise NotImplementedError("腾讯云 TTS 流式尚未实现")
        yield b""  # type: ignore


# ============================================================
# Provider: 通用自定义 HTTP API（不兼容 OpenAI 格式的接口）
# 适用于: 任何自定义的 TTS 服务
# ============================================================
class CustomAPITTS(BaseTTS):
    """
    通用的自定义 HTTP API TTS Provider。

    适合任何通过 HTTP endpoint 暴露的 TTS 服务。
    只需在配置里声明 URL、请求头、请求体字段即可适配。

    配置示例：
        provider: custom_api
        base_url: "https://your-tts-service.com/api/synthesize"
        api_key: "your-key"
        extra:
          header_key: "X-Api-Key"       # API key 放在哪个 header 中
          text_field: "text"             # 请求体中文本字段名
          voice_field: "speaker"         # 请求体中音色字段名
          extra_params:                  # 额外固定参数
            format: "wav"
            sample_rate: 24000
    """

    def __init__(
        self,
        base_url: str = "",
        api_key: str = "",
        header_key: str = "Authorization",
        text_field: str = "text",
        voice_field: str = "voice",
        extra_params: dict | None = None,
        default_voice: str = "",
        **kwargs,
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.header_key = header_key
        self.text_field = text_field
        self.voice_field = voice_field
        self.extra_params = extra_params or {}
        self.default_voice = default_voice

    async def synthesize(self, text: str, voice_id: str = "", speed: float = 1.0) -> bytes:
        import httpx

        voice = voice_id or self.default_voice
        headers = {}
        if self.api_key:
            if self.header_key == "Authorization":
                headers["Authorization"] = f"Bearer {self.api_key}"
            else:
                headers[self.header_key] = self.api_key

        payload = {
            self.text_field: text,
            **self.extra_params,
        }
        if voice:
            payload[self.voice_field] = voice

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self.base_url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.content

    async def synthesize_stream(
        self, text: str, voice_id: str = "", speed: float = 1.0
    ) -> AsyncGenerator[bytes, None]:
        import httpx

        voice = voice_id or self.default_voice
        headers = {}
        if self.api_key:
            if self.header_key == "Authorization":
                headers["Authorization"] = f"Bearer {self.api_key}"
            else:
                headers[self.header_key] = self.api_key

        payload = {
            self.text_field: text,
            **self.extra_params,
        }
        if voice:
            payload[self.voice_field] = voice

        async with httpx.AsyncClient(timeout=30) as client:
            async with client.stream("POST", self.base_url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes(chunk_size=4096):
                    yield chunk


# ============================================================
# 工厂方法
# ============================================================
def get_tts_provider(provider: str, **kwargs) -> BaseTTS:
    """
    按名称获取 TTS Provider。

    已支持：
    - "edge_tts": 免费的微软 Edge TTS
    - "openai_tts": OpenAI 兼容的 TTS API（也适用于司内 API）
    - "tencent_tts": 腾讯云 TTS
    - "custom_api": 通用 HTTP API（适配任意自定义接口）
    """
    providers: dict[str, type[BaseTTS]] = {
        "edge_tts": EdgeTTS,
        "openai_tts": OpenAICompatibleTTS,
        "tencent_tts": TencentTTS,
        "custom_api": CustomAPITTS,
    }

    if provider not in providers:
        logger.warning(f"未知的 TTS Provider '{provider}'，回退到 custom_api")
        return CustomAPITTS(**kwargs)

    return providers[provider](**kwargs)
