"""
检索门控（Retrieval Gate）—— 判断本轮是否需要召回长期记忆。

动机：
- 每轮都召回会浪费 token 和延迟
- 完全依赖模型 tool call 又可能漏召回
- 折中：用轻量规则 / 小模型判断"这轮是否可能需要长期记忆"

策略层次（从快到慢）：
1. 规则层：短消息 / 问候类 → 直接跳过
2. 启发式层：出现代词、时间词、引用语 → 必须召回
3. 模型层（可选）：让 auxiliary 模型判断

设计为可替换的 Gate，支持通过配置开关各层策略。
"""

from abc import ABC, abstractmethod

from loguru import logger


class BaseRetrievalGate(ABC):
    """检索门控的抽象基类。"""

    @abstractmethod
    async def should_retrieve(
        self,
        user_message: str,
        recent_turns: int = 0,
    ) -> bool:
        """判断当前 user message 是否需要触发长期记忆召回。"""
        ...


class AlwaysRetrieveGate(BaseRetrievalGate):
    """总是召回（最简单策略，MVP 用）。"""

    async def should_retrieve(self, user_message: str, recent_turns: int = 0) -> bool:
        return True


class NeverRetrieveGate(BaseRetrievalGate):
    """从不自动召回（仅允许 LLM 通过 tool 主动调用）。"""

    async def should_retrieve(self, user_message: str, recent_turns: int = 0) -> bool:
        return False


class RuleBasedGate(BaseRetrievalGate):
    """
    基于规则的门控。

    规则：
    - 消息字符数 < min_chars → 不召回（闲聊）
    - 匹配问候词白名单 → 不召回
    - 包含引用代词（"上次/那个/之前"）→ 必召回
    - 其他 → 按默认值
    """

    # 不触发召回的关键词（问候、短回应等）
    GREETING_PATTERNS = {"你好", "嗨", "hello", "hi", "在吗", "早", "晚安"}

    # 强制触发召回的引用词
    REFERENCE_PATTERNS = {"上次", "那个", "之前", "记得", "我说过", "还记得"}

    def __init__(self, min_chars: int = 5, default_retrieve: bool = True):
        self.min_chars = min_chars
        self.default_retrieve = default_retrieve

    async def should_retrieve(self, user_message: str, recent_turns: int = 0) -> bool:
        msg = user_message.strip()

        # 规则 1：太短不召回
        if len(msg) < self.min_chars:
            return False

        # 规则 2：引用词强制召回
        for pattern in self.REFERENCE_PATTERNS:
            if pattern in msg:
                logger.debug(f"引用词命中，强制召回: {pattern}")
                return True

        # 规则 3：问候类不召回
        msg_lower = msg.lower()
        for greeting in self.GREETING_PATTERNS:
            if msg_lower == greeting or msg_lower.startswith(greeting + "，"):
                return False

        return self.default_retrieve


class ModelBasedGate(BaseRetrievalGate):
    """
    基于小模型判断的门控（适合更精准的场景）。

    通过 auxiliary 模型 + 简短提示词判断：
    "这句话的回复是否需要参考长期记忆？只回答 YES 或 NO。"
    """

    def __init__(self, judge_fn):
        """judge_fn: async (user_message: str) -> bool"""
        self.judge_fn = judge_fn

    async def should_retrieve(self, user_message: str, recent_turns: int = 0) -> bool:
        # TODO: 调用 judge_fn 返回判断结果
        raise NotImplementedError


class CompositeGate(BaseRetrievalGate):
    """
    组合门控 —— 规则层先判断，规则不确定时再走模型层。

    用法：
        gate = CompositeGate([
            RuleBasedGate(),     # 先过规则
            ModelBasedGate(...), # 再问模型（可选）
        ])
    """

    def __init__(self, gates: list[BaseRetrievalGate]):
        self.gates = gates

    async def should_retrieve(self, user_message: str, recent_turns: int = 0) -> bool:
        # TODO: 当前简化实现 —— 依次询问，任一返回 True 即召回
        # 更精细的做法：区分"明确不召回 / 明确召回 / 不确定"三态
        for gate in self.gates:
            if await gate.should_retrieve(user_message, recent_turns):
                return True
        return False
