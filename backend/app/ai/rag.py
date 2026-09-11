"""
RAG ????? - ???????Retrieval-Augmented Generation?

?????
1. ???? Embedding?embedding-3???????
2. ?? Chroma ?????????
3. ??? Embedding ??????????/???????????
   ???????????????????????
4. ????????MemoryService / user_memories ?????
   RAG ??"?????"???????????

?????
    from app.ai.rag import get_rag_store
    store = get_rag_store()
    store.add_texts(["???????"], metadatas=[{"user_id": "u1"}])
    docs = store.search("???????", user_id="u1", k=3)
"""

import os
import math
from typing import List, Optional, Dict, Any

from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document

# ---- ????????? ----
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    _SPLITTER_AVAILABLE = True
except ImportError:
    _SPLITTER_AVAILABLE = False

# ---- ?????Chroma ??? ----
try:
    from langchain_community.vectorstores import Chroma
    _CHROMA_AVAILABLE = True
except ImportError:
    Chroma = None
    _CHROMA_AVAILABLE = False


# ============================================================
# Embedding ??
# ============================================================

class ZhipuEmbeddings(Embeddings):
    """?? AI Embedding ???OpenAI ????? embeddings.create?"""

    def __init__(self, api_key: str, model: str = "embedding-3"):
        self.api_key = api_key
        self.model = model
        self._client = None
        self._failed = False  # ???????????????????

    @property
    def client(self):
        if self._client is None:
            from zhipuai import ZhipuAI
            self._client = ZhipuAI(api_key=self.api_key)
        return self._client

    def _embed_one(self, text: str) -> List[float]:
        resp = self.client.embeddings.create(model=self.model, input=text)
        return list(resp.data[0].embedding)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_one(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed_one(text)


class SimpleHashEmbeddings(Embeddings):
    """????????????????????????

    ?????????????"??????"????
    Embedding API ?????????????????????
    Embedding????????????
    """

    def __init__(self, dim: int = 256):
        self.dim = dim

    def _embed(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        text = text or ""
        for i, ch in enumerate(text):
            # ??? + ?????????????????
            h = (ord(ch) * 31 + i * 17) % self.dim
            vec[h] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)


class FallbackEmbeddings(Embeddings):
    """?????? Embedding ???

    ?????????? Embedding??? embedding-3??????
    - ??  -> ????? Embedding????????
    - ??? -> ??????? Embedding?????????
                ??????????????? / 429
    """

    def __init__(self, primary: Embeddings, fallback: Embeddings, probe_text: str = "ping"):
        self.primary = primary
        self.fallback = fallback
        self._use_primary = False
        self._probe(probe_text)

    def _probe(self, probe_text: str):
        try:
            vec = self.primary.embed_query(probe_text)
            if vec and len(vec) > 0:
                self._use_primary = True
                print(f"[RAG] ? Embedding ????? {len(vec)}??????????")
                return
        except Exception as e:
            print(f"[RAG] ? Embedding ??????????????: {str(e)[:120]}")
        self._use_primary = False

    @property
    def active_backend(self) -> str:
        return "zhipu" if self._use_primary else "hash_fallback"

    def _active(self) -> Embeddings:
        return self.primary if self._use_primary else self.fallback

    def embed_documents(self, texts):
        emb = self._active()
        try:
            return emb.embed_documents(texts)
        except Exception as e:
            if self._use_primary:
                print(f"[RAG] ? Embedding ????????????: {str(e)[:120]}")
                self._use_primary = False
                return self.fallback.embed_documents(texts)
            raise

    def embed_query(self, text):
        emb = self._active()
        try:
            return emb.embed_query(text)
        except Exception as e:
            if self._use_primary:
                print(f"[RAG] ? Embedding ????????????: {str(e)[:120]}")
                self._use_primary = False
                return self.fallback.embed_query(text)
            raise


def build_embeddings(api_key: str, model: str = "embedding-3") -> Embeddings:
    """?? Embedding ???????? + ?????"""
    fallback = SimpleHashEmbeddings()
    if not api_key or not api_key.strip():
        print("[RAG] ??? API Key?????????????")
        return fallback
    return FallbackEmbeddings(
        primary=ZhipuEmbeddings(api_key=api_key, model=model),
        fallback=fallback,
    )


# ============================================================
# RAG ??
# ============================================================

class RAGStore:
    """RAG ??????Chroma ??? + ???????"""

    def __init__(
        self,
        persist_dir: str,
        api_key: str = "",
        embedding_model: str = "embedding-3",
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

        # ??????????
        self._memory_docs: List[Document] = []

        self._init_store()

    # ---------- ??? ----------
    def _init_store(self):
        if not _CHROMA_AVAILABLE:
            self._init_error = "langchain_community.vectorstores.Chroma ???"
            print(f"[RAG] {self._init_error}?????????")
            return
        try:
            self._store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_dir,
            )
            print(f"[RAG] Chroma ??????: {self.persist_dir}")
        except Exception as e:
            self._init_error = str(e)
            self._store = None
            print(f"[RAG] Chroma ?????: {e}?????????")

    # ---------- ?? ----------
    def _split(self, text: str) -> List[str]:
        text = (text or "").strip()
        if not text:
            return []
        if _SPLITTER_AVAILABLE and len(text) > self.chunk_size:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n", "?", "?", "?", "?", "?", " ", ""],
            )
            return [c for c in splitter.split_text(text) if c.strip()]
        return [text]

    # ---------- ?? ----------
    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> int:
        """?????????????????"""
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
                print(f"[RAG] ?????????????: {e}")

        # ???????
        self._memory_docs.extend(docs)
        return len(docs)

    # ---------- ?? ----------
    def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        k: int = 4,
    ) -> List[Document]:
        """??????"""
        query = (query or "").strip()
        if not query:
            return []

        if self._store is not None:
            try:
                flt = {"user_id": user_id} if user_id else None
                return self._store.similarity_search(query, k=k, filter=flt)
            except Exception as e:
                print(f"[RAG] ????????????: {e}")

        # ??????????
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

    # ---------- ???? ----------
    def add_memory(self, user_id: str, content: str, memory_type: str = "fact") -> int:
        """????????????"""
        return self.add_texts(
            [content],
            metadatas=[{"user_id": user_id, "memory_type": memory_type, "source": "memory"}],
        )

    def add_knowledge(self, title: str, content: str, category: str = "general") -> int:
        """??????????"""
        return self.add_texts(
            [content],
            metadatas=[{"title": title, "category": category, "source": "knowledge"}],
        )

    @property
    def backend(self) -> str:
        store = "chroma" if self._store is not None else "memory_fallback"
        emb = getattr(self.embeddings, "active_backend", "unknown")
        return f"{store}+{emb}"


# ============================================================
# ??
# ============================================================

_rag_store: Optional[RAGStore] = None


def get_rag_store() -> Optional[RAGStore]:
    """?? RAG ????????????? None????????"""
    global _rag_store
    if _rag_store is not None:
        return _rag_store

    try:
        from app.ai.config import ZhipuAIConfig
        config = ZhipuAIConfig()

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        persist_dir = os.path.join(base_dir, "chroma_db")

        _rag_store = RAGStore(
            persist_dir=persist_dir,
            api_key=config.API_KEY,
            embedding_model=getattr(config, "EMBEDDING_MODEL", "embedding-3"),
        )
    except Exception as e:
        print(f"[RAG] ??????RAG ?????: {e}")
        _rag_store = None

    return _rag_store
