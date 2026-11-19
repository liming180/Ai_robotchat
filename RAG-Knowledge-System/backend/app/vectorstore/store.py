"""
向量库统一接口（2026-11-19）

支持两种后端：
- Milvus（新，默认）：单集合 + Partition Key 伴侣隔离，Embedding 由 Milvus Function 服务端调用
- Chroma（旧，回退）：按知识库分集合，本地哈希向量

切换方式：环境变量 VECTOR_STORE_BACKEND=milvus / chroma
"""

from typing import Any, Dict, List, Optional, Tuple
from langchain_core.documents import Document

from app.core.config import settings


# ========== Chroma 后端（旧，保留回退） ==========

def collection_name_of(collection_id: str) -> str:
    """Chroma collection 命名约定。"""
    return f"kb_{collection_id}"


class ChromaStore:
    """Chroma 封装（按 collection 懒加载 + 进程内缓存）。"""

    def __init__(self, persist_dir: Optional[str] = None, embeddings=None):
        import os
        import threading

        self.persist_dir = os.path.abspath(persist_dir or settings.chroma_persist_dir)
        self.embeddings = embeddings
        self._stores: Dict[str, Any] = {}
        self._lock = threading.Lock()
        os.makedirs(self.persist_dir, exist_ok=True)

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
                score = 1.0 - float(distance)
                merged.append((doc, score))

        merged.sort(key=lambda x: x[1], reverse=True)
        return merged[:k]

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

    def count(self, collection_id: str) -> int:
        try:
            store = self._get(collection_id)
            return store._collection.count()  # noqa: SLF001
        except Exception:
            return 0


# ========== 统一接口（根据配置切换后端） ==========

_chroma_store: Optional[ChromaStore] = None
_milvus_store: Optional[Any] = None  # MilvusStore 实例，延迟导入


def get_chroma_store() -> ChromaStore:
    """获取全局 ChromaStore 单例。"""
    global _chroma_store
    if _chroma_store is None:
        _chroma_store = ChromaStore()
    return _chroma_store


def get_milvus_store():
    """获取全局 MilvusStore 单例。"""
    global _milvus_store
    if _milvus_store is None:
        from app.vectorstore.milvus_store import MilvusStore
        _milvus_store = MilvusStore()
    return _milvus_store


def get_vector_store():
    """根据配置获取向量存储实例（统一入口）。

    Returns:
        MilvusStore 或 ChromaStore 实例
    """
    backend = settings.vector_store_backend.lower()

    if backend == "milvus":
        return get_milvus_store()
    elif backend == "chroma":
        return get_chroma_store()
    else:
        raise ValueError(f"不支持的向量存储后端: {backend}，可选值: milvus / chroma")
