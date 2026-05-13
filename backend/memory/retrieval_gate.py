"""
检索门控（Retrieval Gate）—— 判断本轮是否需要召回长期记忆。

设计说明：
- 长期记忆读取路径为：Gate → 条件改写 query → 向量检索 → 注入 SP
- Gate 的作用是"省无用功"：对短消息、问候类直接跳过，避免每轮都做向量检索
- 生产环境使用 RuleBasedGate，零延迟（纯规则，不调 LLM）

规则策略（从快到慢）：
1. 太短（< min_chars）→ 不召回
2. 出现引用词（"上次/那个/之前/记得"）→ 强制召回
3. 问候类 → 不召回
4. 其余 → 默认召回（宁可多搜一次向量库，也不漏记忆）

未来扩展：
- 如果发现规则误判率高，可在此基础上加关键词白名单/黑名单
- 不建议加 LLM 判断层（多一次调用的延迟得不偿失）
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
    """总是召回 —— 用于测试/调试，确保每轮都能验证检索效果。"""

    async def should_retrieve(self, user_message: str, recent_turns: int = 0) -> bool:
        return True


class RuleBasedGate(BaseRetrievalGate):
    """
    基于规则的门控 —— 生产环境默认使用。

    零延迟（纯字符串匹配），规则逻辑：
    1. 消息字符数 < min_chars → 不召回（"嗯""好""哈哈"等无搜索价值）
    2. 包含引用代词（"上次/那个/之前/记得"）→ 强制召回
    3. 匹配问候词 → 不召回
    4. 其余 → 默认召回（default_retrieve=True）

    可调参数：
    - min_chars: 短消息阈值（默认 4）
    - default_retrieve: 规则都没命中时的兜底策略（默认 True）
    - 可通过子类化或配置覆盖关键词集合
    """

    # 不触发召回的关键词（问候、短回应等）
    GREETING_PATTERNS: set[str] = {
        "你好", "嗨", "hello", "hi", "在吗", "早", "早安", "晚安",
        "在", "嗯嗯", "好的", "ok", "谢谢",
    }

    # 强制触发召回的引用词（用户在引用过去的事情）
    REFERENCE_PATTERNS: set[str] = {
        "上次", "那个", "之前", "记得", "我说过", "还记得",
        "以前", "那天", "当时", "你忘了",
    }

    def __init__(self, min_chars: int = 4, default_retrieve: bool = True):
        self.min_chars = min_chars
        self.default_retrieve = default_retrieve

    async def should_retrieve(self, user_message: str, recent_turns: int = 0) -> bool:
        msg = user_message.strip()

        # 规则 1：太短不召回
        if len(msg) < self.min_chars:
            logger.debug(f"Gate: 消息过短({len(msg)} < {self.min_chars})，跳过召回")
            return False

        # 规则 2：引用词强制召回
        for pattern in self.REFERENCE_PATTERNS:
            if pattern in msg:
                logger.debug(f"Gate: 引用词命中 '{pattern}'，强制召回")
                return True

        # 规则 3：问候类不召回
        msg_lower = msg.lower()
        for greeting in self.GREETING_PATTERNS:
            if msg_lower == greeting or msg_lower.startswith(greeting + "，"):
                logger.debug(f"Gate: 问候词命中 '{greeting}'，跳过召回")
                return False

        # 规则 4：其余按默认值
        return self.default_retrieve
