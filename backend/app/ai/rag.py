"""
RAG 知识库模块 —— 轻量检索增强生成（Retrieval-Augmented Generation）。

设计要点：
1. 当前文本/视觉链路只用到智谱的对话与图像端点，未接入 Embedding API，
   故使用本地哈希向量（SimpleHashEmbeddings）做字符级相似度检索，
   零外部依赖、不会失败。
2. 优先使用 Chroma 持久化向量库；Chroma 不可用时退化为内存文档列表。
3. 文档按中文标点/换行切分，支持大段文本入库。
4. 记忆数据与 MemoryService / user_memories 表互补：
   RAG 负责"非结构化知识"，数据库负责"结构化记忆"。

用法：
    from app.ai.rag import get_rag_store
    store = get_rag_store()
    store.add_texts(["用户喜欢猫"], metadatas=[{"user_id": "u1"}])
    docs = store.search("喜欢什么宠物", user_id="u1", k=3)
"""

import os
import math
from typing import List, Optional, Dict, Any

from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document

# ---- 文本切分器 ----
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    _SPLITTER_AVAILABLE = True
except ImportError:
    _SPLITTER_AVAILABLE = False

# ---- Chroma 向量库 ----
try:
    from langchain_community.vectorstores import Chroma
    _CHROMA_AVAILABLE = True
except ImportError:
    Chroma = None
    _CHROMA_AVAILABLE = False


# ============================================================
# Embedding 实现
# ============================================================

class SimpleHashEmbeddings(Embeddings):
    """本地哈希向量 Embedding（无需任何远程 API）。

    把文本按字符级哈希映射到固定维度向量，用字符重叠近似语义相似度。
    未接入远程 Embedding API 时的默认实现——确定性强、零失败率，
    检索质量弱于语义 Embedding，但对短文本/关键词匹配足够可用。
    """

    def __init__(self, dim: int = 256):
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


def build_embeddings(api_key: str = "", model: str = "") -> Embeddings:
    """构建 Embedding 实现。

    未配置远程 Embedding API，直接使用本地哈希向量；
    保留 api_key/model 形参以兼容旧调用方（未来接入远程 Embedding 时启用）。
    """
    print("[RAG] 使用本地哈希向量 Embedding（未接入远程 Embedding API）")
    return SimpleHashEmbeddings()


# ============================================================
# RAG 存储
# ============================================================

class RAGStore:
    """RAG 存储封装：Chroma 向量库 + 内存兜底"""

    def __init__(
        self,
        persist_dir: str,
        api_key: str = "",
        embedding_model: str = "",
        collection_name: str = "ai_companion_knowledge",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        os.makedirs(persist_dir, exist_ok=True)

        self.embeddings = build_embeddings(api_key, embedding_model)
        self._store = None
        self._init_error = None

        # 内存兜底文档
        self._memory_docs: List[Document] = []

        self._init_store()

    # ---------- 初始化 ----------
    def _init_store(self):
        if not _CHROMA_AVAILABLE:
            self._init_error = "langchain_community.vectorstores.Chroma 不可用"
            print(f"[RAG] {self._init_error}，使用内存兜底")
            return
        try:
            self._store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_dir,
            )
            print(f"[RAG] Chroma 向量库已加载: {self.persist_dir}")
        except Exception as e:
            self._init_error = str(e)
            self._store = None
            print(f"[RAG] Chroma 初始化失败: {e}，使用内存兜底")

    # ---------- 切分 ----------
    def _split(self, text: str) -> List[str]:
        text = (text or "").strip()
        if not text:
            return []
        if _SPLITTER_AVAILABLE and len(text) > self.chunk_size:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n", "。", "？", "！", "，", "：", " ", ""],
            )
            return [c for c in splitter.split_text(text) if c.strip()]
        return [text]

    # ---------- 写入 ----------
    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> int:
        """批量写入文本，返回实际写入的分块数"""
        metadatas = metadatas or [{} for _ in texts]
        docs: List[Document] = []
        doc_ids: List[str] = []

        for i, (text, meta) in enumerate(zip(texts, metadatas)):
            for j, chunk in enumerate(self._split(text)):
                docs.append(Document(page_content=chunk, metadata=dict(meta)))
                base_id = ids[i] if ids and i < len(ids) else f"doc_{i}"
                doc_ids.append(f"{base_id}::chunk_{j}")

        if not docs:
            return 0

        if self._store is not None:
            try:
                self._store.add_documents(documents=docs, ids=doc_ids)
                return len(docs)
            except Exception as e:
                print(f"[RAG] Chroma 写入失败，转内存兜底: {e}")

        # 内存兜底
        self._memory_docs.extend(docs)
        return len(docs)

    # ---------- 检索 ----------
    def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        k: int = 4,
    ) -> List[Document]:
        """相似度检索"""
        query = (query or "").strip()
        if not query:
            return []

        if self._store is not None:
            try:
                flt = {"user_id": user_id} if user_id else None
                return self._store.similarity_search(query, k=k, filter=flt)
            except Exception as e:
                print(f"[RAG] Chroma 检索失败，转内存兜底: {e}")

        # 内存兜底检索
        return self._memory_search(query, user_id, k)

    def _memory_search(
        self, query: str, user_id: Optional[str], k: int
    ) -> List[Document]:
        candidates = self._memory_docs
        if user_id:
            candidates = [
                d for d in candidates if d.metadata.get("user_id") == user_id
            ]
        if not candidates:
            return []

        q_chars = set(query)
        scored = []
        for d in candidates:
            content = d.page_content
            overlap = len(q_chars & set(content))
            score = overlap / (len(q_chars) or 1)
            scored.append((score, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [d for s, d in scored[:k] if s > 0]

    # ---------- 快捷入口 ----------
    def add_memory(self, user_id: str, content: str, memory_type: str = "fact") -> int:
        """写入用户记忆（带 user_id 元数据）"""
        return self.add_texts(
            [content],
            metadatas=[{"user_id": user_id, "memory_type": memory_type, "source": "memory"}],
        )

    def add_knowledge(self, title: str, content: str, category: str = "general") -> int:
        """写入知识库条目"""
        return self.add_texts(
            [content],
            metadatas=[{"title": title, "category": category, "source": "knowledge"}],
        )

    @property
    def backend(self) -> str:
        store = "chroma" if self._store is not None else "memory_fallback"
        emb = getattr(self.embeddings, "active_backend", "hash")
        return f"{store}+{emb}"


# ============================================================
# 单例
# ============================================================

_rag_store: Optional[RAGStore] = None


def get_rag_store() -> Optional[RAGStore]:
    """获取 RAG 存储单例；初始化失败返回 None（调用方降级）"""
    global _rag_store
    if _rag_store is not None:
        return _rag_store

    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        persist_dir = os.path.join(base_dir, "chroma_db")

        _rag_store = RAGStore(persist_dir=persist_dir)
    except Exception as e:
        print(f"[RAG] RAG 存储初始化失败，功能降级: {e}")
        _rag_store = None

    return _rag_store
