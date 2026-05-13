"""
Context Providers —— 背景上下文的可插拔提供者。

每个 Provider 是一个独立的"沙箱"，负责：
1. 判断本轮是否需要执行（should_run）
2. 执行自己的逻辑并产出一段文本（run）
3. 声明自己属于哪个组（static / dynamic）

最终所有非空的 Provider 产出会被收集到 state["context_parts"]，
由 call_main_agent 节点按配置模式（单SP / 双SP）组装进 System Prompt。

┌─────────────────────────────────────────────────────────┐
│  Provider 分组                                           │
│                                                          │
│  STATIC（固定，几乎不变）：                              │
│    - PersonaProvider: 人设、性格、说话风格、行为准则     │
│                                                          │
│  DYNAMIC（每轮可能变化）：                               │
│    - ProfileProvider: 用户档案（EAV 全量读取）           │
│    - MemoryProvider: 长期记忆（Gate → 改写 → 检索）     │
│    - ... 未来可扩展更多                                  │
└─────────────────────────────────────────────────────────┘

使用方式：
    from context_providers import get_all_providers

    providers = get_all_providers(agent_config)
    for p in providers:
        if await p.should_run(state):
            text = await p.run(state)
            if text:
                context_parts[p.name] = text

新增功能模块：
    1. 在此目录下新建 xxx_provider.py
    2. 继承 BaseContextProvider
    3. 在 PROVIDER_REGISTRY 中注册
    4. 完成。不需要改 state、nodes 或其他文件。
"""

from context_providers.base import BaseContextProvider, ProviderGroup
from context_providers.persona_provider import PersonaProvider
from context_providers.profile_provider import ProfileProvider
from context_providers.memory_provider import MemoryProvider


# === Provider 注册表 ===
# 按执行顺序排列（影响 SP 中的呈现顺序）
PROVIDER_REGISTRY: list[type[BaseContextProvider]] = [
    PersonaProvider,
    ProfileProvider,
    MemoryProvider,
]


def get_all_providers(agent_config: dict) -> list[BaseContextProvider]:
    """
    根据 agent_config 实例化所有启用的 Provider。

    Provider 可以在 agent_config 中通过 context_providers.disabled 列表禁用。
    """
    disabled = set(agent_config.get("context_providers", {}).get("disabled", []))
    providers = []
    for cls in PROVIDER_REGISTRY:
        if cls.name not in disabled:
            providers.append(cls(agent_config))
    return providers


def get_static_providers(providers: list[BaseContextProvider]) -> list[BaseContextProvider]:
    """筛选出 STATIC 组的 providers。"""
    return [p for p in providers if p.group == ProviderGroup.STATIC]


def get_dynamic_providers(providers: list[BaseContextProvider]) -> list[BaseContextProvider]:
    """筛选出 DYNAMIC 组的 providers。"""
    return [p for p in providers if p.group == ProviderGroup.DYNAMIC]


__all__ = [
    "BaseContextProvider",
    "ProviderGroup",
    "get_all_providers",
    "get_static_providers",
    "get_dynamic_providers",
    "PROVIDER_REGISTRY",
]
