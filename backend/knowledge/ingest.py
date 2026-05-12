"""
知识库数据摄入 —— 加载、分块、向量化并写入游戏知识。

使用示例：
    python -m knowledge.ingest --source ./knowledge/data/game_name/
"""

from pathlib import Path
from typing import Any

from loguru import logger


class KnowledgeIngestor:
    """将游戏知识文档摄入向量数据库。"""

    def __init__(
        self,
        data_dir: str | Path,
        collection_name: str = "game_knowledge",
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ):
        self.data_dir = Path(data_dir)
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    async def ingest_directory(self, game_name: str | None = None) -> int:
        """
        批量摄入数据目录中的所有文档。

        参数：
            game_name: 可选过滤器，仅摄入某款游戏的数据

        返回值：
            已摄入的 chunk 数量
        """
        # TODO: 具体实现
        # 1. 扫描 data_dir，找出支持的文件（.md / .txt / .json）
        # 2. 加载并解析文档
        # 3. 使用 LangChain 的 text splitter 分块
        # 4. 生成 embedding
        # 5. 写入向量库并附带元数据（游戏名、来源等）
        logger.info(f"开始从 {self.data_dir} 摄入知识")
        return 0

    async def ingest_file(self, file_path: Path, metadata: dict[str, Any] = None) -> int:
        """摄入单个文件。"""
        # TODO: 具体实现
        return 0


async def main():
    """知识库摄入的 CLI 入口。"""
    import argparse

    parser = argparse.ArgumentParser(description="摄入游戏知识库")
    parser.add_argument("--source", type=str, required=True, help="源数据目录")
    parser.add_argument("--game", type=str, help="游戏名称过滤")
    parser.add_argument("--collection", type=str, default="game_knowledge")
    args = parser.parse_args()

    ingestor = KnowledgeIngestor(
        data_dir=args.source,
        collection_name=args.collection,
    )
    count = await ingestor.ingest_directory(game_name=args.game)
    logger.info(f"已摄入 {count} 个 chunk")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
