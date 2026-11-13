"""
本地哈希 Embedding 封装（无需任何远程 API）。

历史：原为智谱 embedding-3 封装（2048 维）。智谱 API key 已作废、
当前链路未接入远程 Embedding API，故与主服务
backend/app/ai/rag.py 采用同一方案：字符级哈希向量，零外部依赖、零失败率。

注意：向量维度为 256。此前用 embedding-3（2048 维）导入的旧集合
与本实现不兼容，检索时会因维度不匹配报错——旧知识库需重新导入。
"""

import math
from typing import List

from langchain_core.embeddings import Embeddings


class SimpleHashEmbeddings(Embeddings):
    """本地哈希向量 Embedding（langchain Embeddings 接口）。

    把文本按字符级哈希映射到固定维度向量，用字符重叠近似语义相似度。
    检索质量弱于语义 Embedding，但对短文本/关键词匹配足够可用。
    """

    def __init__(self, dim: int = 256):
        if dim <= 0:
            raise ValueError(f"向量维度必须为正整数，收到 {dim}")
        self.dim = dim

    def _embed(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        text = text or ""
        for i, ch in enumerate(text):
            # 字符 + 位置联合哈希，降低碰撞集中度
            h = (ord(ch) * 31 + i * 17) % self.dim
            vec[h] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)
