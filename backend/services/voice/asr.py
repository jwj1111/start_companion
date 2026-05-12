"""
ASR（语音识别）服务。

将用户语音转写为文本。
通过配置可切换多种 Provider：

1. whisper_api    - OpenAI Whisper API（或任何兼容 /v1/audio/transcriptions 的接口）
2. whisper_local  - 本地 Whisper 模型（faster-whisper / transformers）
3. tencent_asr    - 腾讯云 ASR
4. custom_api     - 通用自定义 HTTP API

所有 Provider 都通过 config 切换，无需改代码。
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator
from io import BytesIO

from loguru import logger


class BaseASR(ABC):
    """ASR Provider 的抽象基类。"""

    @abstractmethod
    async def transcribe(self, audio_data: bytes, language: str = "zh") -> str:
        """将完整音频字节流转写为文本。"""
        ...

    @abstractmethod
    async def transcribe_stream(
        self, audio_stream: AsyncGenerator[bytes, None], language: str = "zh"
    ) -> AsyncGenerator[str, None]:
        """流式转写 —— 按片段 yield 出部分识别结果。"""
        ...


# ============================================================
# Provider: OpenAI 兼容的 Whisper API
# 适用于: OpenAI 官方 API / 司内 API / 任何兼容 /v1/audio/transcriptions 的服务
# ============================================================
class WhisperAPIASR(BaseASR):
    """
    OpenAI 兼容的 Whisper API。

    适用于：
    - OpenAI 官方 API
    - 任何兼容 /v1/audio/transcriptions 格式的司内或第三方 API
    - 自行部署的 whisper 服务（如 faster-whisper-server）

    配置示例：
        provider: whisper_api
        api_key: "sk-xxx"
        base_url: "https://internal.tencent.com/v1"
        model: "whisper-1"
    """

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "",
        model: str = "whisper-1",
        **kwargs,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/") if base_url else "https://api.openai.com/v1"
        self.model = model

    async def transcribe(self, audio_data: bytes, language: str = "zh") -> str:
        import httpx

        headers = {"Authorization": f"Bearer {self.api_key}"}
        files = {"file": ("audio.wav", BytesIO(audio_data), "audio/wav")}
        data = {"model": self.model, "language": language}

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.base_url}/audio/transcriptions",
                headers=headers,
                files=files,
                data=data,
            )
            resp.raise_for_status()
            result = resp.json()
            return result.get("text", "")

    async def transcribe_stream(
        self, audio_stream: AsyncGenerator[bytes, None], language: str = "zh"
    ) -> AsyncGenerator[str, None]:
        # Whisper API 原生不支持流式，这里先收完整音频再一次性转写
        chunks = []
        async for chunk in audio_stream:
            chunks.append(chunk)
        full_audio = b"".join(chunks)
        text = await self.transcribe(full_audio, language)
        yield text


# ============================================================
# Provider: 本地 Whisper 模型
# 适用于: 本地运行 faster-whisper / HuggingFace whisper 模型
# ============================================================
class WhisperLocalASR(BaseASR):
    """
    基于 faster-whisper 的本地 Whisper 模型。

    完全在本地运行，不产生任何 API 调用。
    支持 HuggingFace 上的任意 Whisper 模型或本地路径。

    配置示例：
        provider: whisper_local
        model: "large-v3"           # 或 HuggingFace model ID / 本地路径
        base_url: "cuda"            # 设备: cuda / cpu
    """

    def __init__(
        self,
        model: str = "large-v3",
        base_url: str = "cuda",  # 复用 base_url 字段作为 device
        **kwargs,
    ):
        self.model_name = model
        self.device = base_url or "cuda"
        self._model = None

    def _get_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel

            compute_type = "float16" if self.device == "cuda" else "int8"
            self._model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=compute_type,
            )
            logger.info(
                f"已加载本地 Whisper 模型: {self.model_name}，设备: {self.device}"
            )
        return self._model

    async def transcribe(self, audio_data: bytes, language: str = "zh") -> str:
        import asyncio
        import tempfile
        import os

        # faster-whisper 需要文件路径，先写入临时文件
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_data)
            tmp_path = f.name

        try:
            model = self._get_model()
            # 同步推理丢到线程池中执行，避免阻塞事件循环
            segments, _ = await asyncio.to_thread(
                model.transcribe, tmp_path, language=language
            )
            text = "".join(seg.text for seg in segments)
            return text.strip()
        finally:
            os.unlink(tmp_path)

    async def transcribe_stream(
        self, audio_stream: AsyncGenerator[bytes, None], language: str = "zh"
    ) -> AsyncGenerator[str, None]:
        chunks = []
        async for chunk in audio_stream:
            chunks.append(chunk)
        full_audio = b"".join(chunks)
        text = await self.transcribe(full_audio, language)
        yield text


# ============================================================
# Provider: 腾讯云 ASR
# ============================================================
class TencentASR(BaseASR):
    """腾讯云 ASR Provider。"""

    def __init__(self, secret_id: str = "", secret_key: str = "", **kwargs):
        self.secret_id = secret_id
        self.secret_key = secret_key

    async def transcribe(self, audio_data: bytes, language: str = "zh") -> str:
        # TODO: 对接腾讯云 ASR API
        raise NotImplementedError("腾讯云 ASR 尚未实现")

    async def transcribe_stream(
        self, audio_stream: AsyncGenerator[bytes, None], language: str = "zh"
    ) -> AsyncGenerator[str, None]:
        raise NotImplementedError("腾讯云 ASR 流式尚未实现")
        yield ""  # type: ignore


# ============================================================
# Provider: 通用自定义 HTTP API
# 适用于: 任何自定义的 ASR 接口
# ============================================================
class CustomAPIASR(BaseASR):
    """
    通用的自定义 HTTP API ASR Provider。

    配置示例：
        provider: custom_api
        base_url: "https://your-asr-service.com/api/transcribe"
        api_key: "your-key"
        extra:
          header_key: "X-Api-Key"
          audio_field: "audio"
          language_field: "lang"
    """

    def __init__(
        self,
        base_url: str = "",
        api_key: str = "",
        header_key: str = "Authorization",
        audio_field: str = "audio",
        language_field: str = "language",
        **kwargs,
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.header_key = header_key
        self.audio_field = audio_field
        self.language_field = language_field

    async def transcribe(self, audio_data: bytes, language: str = "zh") -> str:
        import httpx

        headers = {}
        if self.api_key:
            if self.header_key == "Authorization":
                headers["Authorization"] = f"Bearer {self.api_key}"
            else:
                headers[self.header_key] = self.api_key

        files = {self.audio_field: ("audio.wav", BytesIO(audio_data), "audio/wav")}
        data = {self.language_field: language}

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(self.base_url, headers=headers, files=files, data=data)
            resp.raise_for_status()
            result = resp.json()
            # 尝试常见的响应字段名
            return result.get("text", result.get("result", result.get("transcript", "")))

    async def transcribe_stream(
        self, audio_stream: AsyncGenerator[bytes, None], language: str = "zh"
    ) -> AsyncGenerator[str, None]:
        chunks = []
        async for chunk in audio_stream:
            chunks.append(chunk)
        full_audio = b"".join(chunks)
        text = await self.transcribe(full_audio, language)
        yield text


# ============================================================
# 工厂方法
# ============================================================
def get_asr_provider(provider: str, **kwargs) -> BaseASR:
    """
    按名称获取 ASR Provider。

    已支持：
    - "whisper_api": OpenAI 兼容的 Whisper API（也适用于司内 API）
    - "whisper_local": 本地 faster-whisper 模型
    - "tencent_asr": 腾讯云 ASR
    - "custom_api": 通用 HTTP API（适配任意自定义接口）
    """
    providers: dict[str, type[BaseASR]] = {
        "whisper_api": WhisperAPIASR,
        "whisper_local": WhisperLocalASR,
        "tencent_asr": TencentASR,
        "custom_api": CustomAPIASR,
    }

    # 兼容旧配置 "whisper" -> "whisper_api"
    if provider == "whisper":
        provider = "whisper_api"

    if provider not in providers:
        logger.warning(f"未知的 ASR Provider '{provider}'，回退到 custom_api")
        return CustomAPIASR(**kwargs)

    return providers[provider](**kwargs)
