"""
模型 Provider —— 统一的模型实例化与管理。

设计：
- 模型池 (model_pool): 在 config.yaml 中声明所有可用模型
- 角色映射 (model_roles): 声明每种用途使用哪个模型
- provider 只有 4 种: openai / anthropic / ollama / huggingface
  （openai 覆盖所有 OpenAI 兼容 API，包括混元、DeepSeek、智谱、司内等）

使用方式：
    from models.provider import get_model, get_embedding_model

    llm = get_model("main")              # 按角色获取
    llm = get_model("main_fallback")     # 自定义角色也行
    embeddings = get_embedding_model()    # 默认用 "embedding" 角色
    embeddings = get_embedding_model("embedding_knowledge")  # 指定角色
"""

from __future__ import annotations

from typing import Any

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from loguru import logger

from app.config.settings import resolve_role


def get_model(role: str = "main") -> BaseChatModel:
    """
    按角色获取对话模型实例。

    参数：
        role: 角色名，对应 config.yaml 中 model_roles 的 key
              框架内置角色: main / vision / auxiliary
              也可以自定义: main_fallback / game_expert / ...

    返回值：
        兼容 LangChain 的对话模型实例
    """
    config = resolve_role(role)
    return _create_chat_model(config)


def get_embedding_model(role: str = "embedding") -> Embeddings:
    """
    按角色获取 embedding 模型实例。

    参数：
        role: 角色名，默认 "embedding"
              也可以配多个: embedding_memory / embedding_knowledge
    """
    config = resolve_role(role)
    return _create_embedding_model(config)


# ============================================================
# 内部工厂方法 —— 只有 4 种 provider
# ============================================================

def _create_chat_model(config: dict[str, Any]) -> BaseChatModel:
    """根据配置创建对话模型。"""
    provider = config["provider"]
    model = config["model"]
    api_key = config.get("api_key", "")
    base_url = config.get("base_url", "")

    logger.debug(f"创建对话模型: provider={provider}, model={model}")

    if provider == "openai":
        # 覆盖所有 OpenAI 兼容 API：
        # OpenAI / 混元 / DeepSeek / 智谱 / 司内 API / vLLM / LM Studio ...
        from langchain_openai import ChatOpenAI

        kwargs: dict[str, Any] = {"model": model, "api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        if "temperature" in config:
            kwargs["temperature"] = config["temperature"]
        if "max_tokens" in config:
            kwargs["max_tokens"] = config["max_tokens"]
        return ChatOpenAI(**kwargs)

    elif provider == "anthropic":
        # Claude 系列（协议不兼容 OpenAI）
        from langchain_anthropic import ChatAnthropic

        kwargs = {"model": model, "api_key": api_key}
        if "temperature" in config:
            kwargs["temperature"] = config["temperature"]
        if "max_tokens" in config:
            kwargs["max_tokens"] = config["max_tokens"]
        return ChatAnthropic(**kwargs)

    elif provider == "ollama":
        # 本地 Ollama 模型
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=model,
            base_url=base_url or "http://localhost:11434",
        )

    else:
        # 兜底：当作 OpenAI 兼容处理
        from langchain_openai import ChatOpenAI

        logger.warning(f"未知 provider '{provider}'，按 OpenAI 兼容处理")
        kwargs = {"model": model, "api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        return ChatOpenAI(**kwargs)


def _create_embedding_model(config: dict[str, Any]) -> Embeddings:
    """根据配置创建 embedding 模型。"""
    provider = config["provider"]
    model = config["model"]
    api_key = config.get("api_key", "")
    base_url = config.get("base_url", "")

    logger.debug(f"创建 embedding 模型: provider={provider}, model={model}")

    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        kwargs: dict[str, Any] = {"model": model, "api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        return OpenAIEmbeddings(**kwargs)

    elif provider == "ollama":
        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(
            model=model,
            base_url=base_url or "http://localhost:11434",
        )

    elif provider == "huggingface":
        # 本地 HuggingFace 模型（BGE / GTE / M3E 等）
        from langchain_huggingface import HuggingFaceEmbeddings

        kwargs = {
            "model_name": model,
            "encode_kwargs": {"normalize_embeddings": True},
        }
        if device := config.get("device"):
            kwargs["model_kwargs"] = {"device": device}
        return HuggingFaceEmbeddings(**kwargs)

    else:
        # 兜底
        from langchain_openai import OpenAIEmbeddings

        kwargs = {"model": model, "api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        return OpenAIEmbeddings(**kwargs)
