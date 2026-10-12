"""
Chroma 向量库封装。

设计要点：
1. 一个知识库集合 = 一个 Chroma collection，命名 kb_{collection_id}；
2. collection 使用 cosine 距离，score = 1 - distance，便于设置阈值；
3. 元数据统一写入 collection_id / document_id / companion_id / title / chunk_index，
   检索时按 collection_id 做 $in 过滤；
4. 独立持久化目录，不复用主服务 backend/chroma_db，避免多进程写入冲突。
"""

import os
import threading
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.documents import Document

from app.core.config import settings


def collection_name_of(collection_id: str) -> str:
    """Chroma collection 命名约定。"""
    return f"kb_{collection_id}"


class ChromaStore:
    """Chroma 封装（按 collection 懒加载 + 进程内缓存）。"""

    def __init__(self, persist_dir: Optional[str] = None, embeddings=None):
        self.persist_dir = os.path.abspath(persist_dir or settings.chroma_persist_dir)
        self.embeddings = embeddings
        self._stores: Dict[str, Any] = {}
        self._lock = threading.Lock()
        os.makedirs(self.persist_dir, exist_ok=True)

    # ---------- 内部 ----------
    def _build_embeddings(self):
        """按需构建 Embedding（延迟初始化，避免导入即联网）。"""
        if self.embeddings is not None:
            return self.embeddings

        from app.vectorstore.embeddings import SimpleHashEmbeddings

        self.embeddings = SimpleHashEmbeddings(dim=settings.embedding_dim)
        return self.embeddings

    def _get(self, collection_id: str):
        name = collection_name_of(collection_id)
        if name in self._stores:
            return self._stores[name]

        with self._lock:
            if name in self._stores:
                return self._stores[name]

            from langchain_chroma import Chroma

            store = Chroma(
                collection_name=name,
                embedding_function=self._build_embeddings(),
                persist_directory=self.persist_dir,
                collection_metadata={"hnsw:space": "cosine"},
            )
            self._stores[name] = store
            return store

    # ---------- 写入 ----------
    def add_chunks(
        self,
        collection_id: str,
        chunk_ids: List[str],
        texts: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> int:
        """写入切片向量。chunk_ids 作为 Chroma 中的向量 id。"""
        if not texts:
            return 0
        store = self._get(collection_id)
        store.add_texts(texts=texts, metadatas=metadatas, ids=chunk_ids)
        return len(texts)

    # ---------- 检索 ----------
    def search(
        self,
        collection_ids: List[str],
        query: str,
        k: int = 4,
    ) -> List[Tuple[Document, float]]:
        """跨多个知识库检索，返回 (文档, 相似度) 列表，相似度降序。"""
        query = (query or "").strip()
        if not query or not collection_ids:
            return []

        where = {"collection_id": {"$in": list(collection_ids)}}
        merged: List[Tuple[Document, float]] = []

        for cid in collection_ids:
            try:
                store = self._get(cid)
                pairs = store.similarity_search_with_score(query, k=k, filter=where)
            except Exception as e:
                print(f"[ChromaStore] collection={cid} 检索失败: {str(e)[:200]}")
                continue

            for doc, distance in pairs:
                # cosine 距离 -> 相似度
                score = 1.0 - float(distance)
                merged.append((doc, score))

        merged.sort(key=lambda x: x[1], reverse=True)
        return merged[:k]

    # ---------- 删除 ----------
    def delete_chunks(self, collection_id: str, chunk_ids: List[str]) -> None:
        """按向量 id 删除。Chroma 无事务，调用方需自行保证与元数据库的最终一致。"""
        if not chunk_ids:
            return
        try:
            store = self._get(collection_id)
            store.delete(ids=list(chunk_ids))
        except Exception as e:
            print(f"[ChromaStore] 删除向量失败 collection={collection_id}: {str(e)[:200]}")
            raise

    def drop_collection(self, collection_id: str) -> None:
        """删除整个 collection（删除知识库时调用）。"""
        name = collection_name_of(collection_id)
        try:
            store = self._get(collection_id)
            store.delete_collection()
        except Exception as e:
            print(f"[ChromaStore] 删除 collection 失败 {name}: {str(e)[:200]}")
        finally:
            self._stores.pop(name, None)

    # ---------- 统计 ----------
    def count(self, collection_id: str) -> int:
        try:
            store = self._get(collection_id)
            return store._collection.count()  # noqa: SLF001
        except Exception:
            return 0


_store: Optional[ChromaStore] = None


def get_chroma_store() -> ChromaStore:
    """获取全局 ChromaStore 单例。"""
    global _store
    if _store is None:
        _store = ChromaStore()
    return _store
