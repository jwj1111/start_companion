"""
联网搜索服务 —— 多 Provider 支持。

已支持的 Provider：
- Tavily（推荐，专为 AI 场景设计）
- Serper（Google 搜索 API）
- Bing 搜索 API
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SearchResult:
    """单条搜索结果。"""
    title: str
    url: str
    snippet: str
    content: str = ""


class BaseWebSearch(ABC):
    """联网搜索 Provider 的抽象基类。"""

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """执行一次搜索。"""
        ...


class TavilySearch(BaseWebSearch):
    """Tavily 搜索 Provider（为 AI 场景优化）。"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """使用 Tavily API 进行搜索。"""
        # TODO: 具体实现
        # from tavily import TavilyClient
        raise NotImplementedError


class SerperSearch(BaseWebSearch):
    """Serper（Google）搜索 Provider。"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """使用 Serper API 进行搜索。"""
        # TODO: 具体实现
        raise NotImplementedError


def get_search_provider(provider: str, api_key: str) -> BaseWebSearch:
    """工厂方法：按名称获取搜索 Provider。"""
    providers = {
        "tavily": TavilySearch,
        "serper": SerperSearch,
    }
    if provider not in providers:
        raise ValueError(f"未知的搜索 Provider: {provider}")
    return providers[provider](api_key=api_key)
