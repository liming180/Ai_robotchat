"""Milvus 向量存储实现（2026-11-19，2026-11-22 增加 BM25 混合检索）

特性：
- Partition Key 按伴侣 UUID 字符串隔离（companion_id）
- 插入后自动 flush（避免查询命中 0 条）
- 查询时由 Milvus Function 服务端调用智谱 Embedding-3 向量化
- 对外接口与 ChromaStore 对齐，支持按 documentId/collectionId 精确删除

双集合口径（2026-11-22）：
- hybrid=False：kb_chunks，纯 dense + 可选 TEI 精排（现有生产路径，未改动）
- hybrid=True ：kb_chunks_hybrid，dense + BM25 sparse 两路召回，RRF 合并名次，不做精排
  analyzer / BM25 Function / sparse 索引都是**建集合时**的 schema 参数，
  旧集合无法原地改造，所以单独建灰度集合，切开关即可回滚。
"""
from typing import List, Dict, Any, Optional
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    Function,
    FunctionType,
    RRFRanker,
    AnnSearchRequest,
    utility,
)
from langchain_core.documents import Document

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# 分数尺度标记：随检索结果返回给路由层，避免调用方把 RRF 名次分当相似度用。
SCORE_SCALE_COSINE = "cosine"
SCORE_SCALE_TEI = "tei"
SCORE_SCALE_RRF = "rrf"


class MilvusStore:
    """Milvus 向量存储（单集合 + Partition Key 隔离）

    Args:
        collection_name: 覆盖默认集合名；不传时按 hybrid 开关选默认值
        hybrid: True 走 BM25 混合检索（kb_chunks_hybrid），False 走原 dense 单路
    """

    def __init__(self, collection_name: Optional[str] = None, hybrid: bool = False):
        self.hybrid = hybrid
        self.collection_name = collection_name or (
            settings.hybrid_collection_name if hybrid else "kb_chunks"
        )
        self._connected = False
        self._collection: Optional[Collection] = None
        self.score_scale = SCORE_SCALE_RRF if hybrid else (
            SCORE_SCALE_TEI if settings.rerank_enabled else SCORE_SCALE_COSINE
        )

    def connect(self):
        """连接 Milvus"""
        if self._connected:
            return

        try:
            connections.connect(
                alias="default",
                host=settings.milvus_host,
                port=settings.milvus_port,
                user=settings.milvus_user or "",
                password=settings.milvus_password or "",
            )
            self._connected = True
            logger.info(f"Milvus 连接成功: {settings.milvus_host}:{settings.milvus_port}")
        except Exception as e:
            logger.error(f"Milvus 连接失败: {e}")
            raise

    def _get_collection(self) -> Collection:
        """获取集合（不存在则创建）"""
        if not self._connected:
            self.connect()

        if self._collection is not None:
            return self._collection

        if utility.has_collection(self.collection_name):
            self._collection = Collection(self.collection_name)
            logger.info(f"集合已存在: {self.collection_name}")
        else:
            self._create_collection()

        return self._collection

    def _create_collection(self):
        """创建集合（含 Partition Key 和索引）"""
        # hybrid 集合的 text 字段必须建集合时启用 analyzer，BM25 才能对中文切片分词；
        # 旧 kb_chunks 没有该参数且无法追加，故只能新建灰度集合。
        text_field = FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535)
        if self.hybrid:
            text_field = FieldSchema(
                name="text",
                dtype=DataType.VARCHAR,
                max_length=65535,
                enable_analyzer=True,
                analyzer_params={"type": "chinese"},
            )

        # 定义字段
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            text_field,
            FieldSchema(name="dense", dtype=DataType.FLOAT_VECTOR, dim=2048),  # Embedding-3 2048 维
            # Java / MySQL 的伴侣与知识库 ID 是 UUID 或 preset-* 字符串，不能强转 INT64。
            # 36 字符带连字符 UUID 直接原值保存，Partition Key 同样支持 VARCHAR。
            FieldSchema(name="companion_id", dtype=DataType.VARCHAR, max_length=36, is_partition_key=True),
            FieldSchema(name="collection_id", dtype=DataType.VARCHAR, max_length=36),
            FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=36),
            FieldSchema(name="chunk_index", dtype=DataType.INT32),
            FieldSchema(name="vector_id", dtype=DataType.VARCHAR, max_length=255),
        ]
        if self.hybrid:
            # 稀疏向量字段只是 BM25 Function 的输出容器，入库不传值。
            fields.append(FieldSchema(name="sparse", dtype=DataType.SPARSE_FLOAT_VECTOR))

        schema = CollectionSchema(fields=fields, description="RAG 知识库切片")

        # 挂载服务端 Embedding Function：插入/检索时由 Milvus 服务端调用智谱 Embedding-3 自动生成 dense 向量
        # provider 名对应 deploy/milvus/milvus.yaml 的 function.textEmbedding.providers.openai（url 已指向智谱端点）
        embedding_fn = Function(
            name="text_embedding",
            function_type=FunctionType.TEXTEMBEDDING,
            input_field_names=["text"],
            output_field_names=["dense"],
            params={
                "provider": "openai",
                "model_name": "embedding-3",  # 默认输出 2048 维，与 dense 字段 dim 一致
            },
        )
        schema.add_function(embedding_fn)

        if self.hybrid:
            # BM25 Function 同样是服务端生成：text → sparse，插入时无需传稀疏向量。
            schema.add_function(
                Function(
                    name="text_bm25",
                    function_type=FunctionType.BM25,
                    input_field_names=["text"],
                    output_field_names=["sparse"],
                    params={},
                )
            )

        # 创建集合
        self._collection = Collection(name=self.collection_name, schema=schema)
        logger.info(f"集合创建成功: {self.collection_name}")

        # 创建索引（dense 字段 HNSW + COSINE）
        index_params = {
            "index_type": "HNSW",
            "metric_type": "COSINE",
            "params": {"M": 16, "efConstruction": 256},
        }
        self._collection.create_index(field_name="dense", index_params=index_params)
        logger.info("索引创建成功: dense (HNSW + COSINE)")

        if self.hybrid:
            self._collection.create_index(
                field_name="sparse",
                index_params={
                    "index_type": "SPARSE_INVERTED_INDEX",
                    "metric_type": "BM25",
                    "params": {
                        "inverted_index_algo": "DAAT_MAXSCORE",
                        "bm25_k1": settings.bm25_k1,
                        "bm25_b": settings.bm25_b,
                    },
                },
            )
            logger.info(
                "索引创建成功: sparse (SPARSE_INVERTED_INDEX + BM25, "
                f"k1={settings.bm25_k1}, b={settings.bm25_b})"
            )

        # 加载集合到内存
        self._collection.load()
        logger.info("集合已加载到内存")

    def insert(
        self,
        texts: List[str],
        companion_id: str,
        collection_id: str,
        document_id: str,
        chunk_indices: List[int],
        vector_ids: List[str],
    ) -> int:
        """插入切片（自动 flush）

        Args:
            texts: 切片文本列表
            companion_id: 伴侣 ID（Partition Key）
            collection_id: 知识库 ID
            document_id: 文档 ID
            chunk_indices: 切片序号列表
            vector_ids: 业务主键列表（{document_id}::chunk_{index}）

        Returns:
            插入的切片数量
        """
        if not texts:
            return 0

        collection = self._get_collection()

        # 构造插入数据（注意：不传 dense 字段，由 Milvus Function 自动生成）
        entities = [
            {
                "text": texts[i],
                "companion_id": companion_id,
                "collection_id": collection_id,
                "document_id": document_id,
                "chunk_index": chunk_indices[i],
                "vector_id": vector_ids[i],
            }
            for i in range(len(texts))
        ]

        try:
            # 插入数据
            collection.insert(entities)
            # 立即 flush（避免查询命中 0 条）
            collection.flush()
            logger.info(f"插入成功: {len(texts)} 条切片, document_id={document_id}")
            return len(texts)
        except Exception as e:
            logger.error(f"插入失败: {e}, document_id={document_id}")
            raise

    def search(
        self,
        collection_ids: List[str],
        query: str,
        k: int = 4,
        companion_id: Optional[str] = None,
        score_threshold: float = 0.0,
    ) -> List[tuple[Document, float]]:
        """统一检索接口，返回与 ChromaStore 一致的 (Document, 相似度) 列表。

        dense 模式：COSINE / TEI 下 distance 即相似度，越大越相似。
        hybrid 模式：distance 是 RRF 名次融合分（0.015~0.033 量级），**不是相似度**；
        score_threshold 在路由层按对应尺度过滤，不可混用两个尺度。
        """
        chunks = self.search_chunks(
            collection_ids=collection_ids,
            query=query,
            top_k=k,
            companion_id=companion_id,
            score_threshold=score_threshold,
        )
        return [
            (
                Document(
                    page_content=chunk["text"],
                    metadata={
                        "collection_id": chunk["collection_id"],
                        "document_id": chunk["document_id"],
                        "chunk_index": chunk["chunk_index"],
                        "vector_id": chunk["vector_id"],
                        "document_title": chunk["document_title"],
                    },
                ),
                chunk["score"],
            )
            for chunk in chunks
        ]

    def _build_filter_expr(
        self,
        companion_id: Optional[str],
        collection_ids: Optional[List[str]],
    ) -> str:
        """构造过滤表达式：字符串值必须带引号；UUID / preset-* 不能当数字表达式。"""
        filter_expr = []
        if companion_id is not None:
            filter_expr.append(f'companion_id == "{companion_id}"')
        if collection_ids:
            ids_str = ",".join(f'"{cid}"' for cid in collection_ids)
            filter_expr.append(f"collection_id in [{ids_str}]")
        return " && ".join(filter_expr) if filter_expr else ""

    def _parse_hits(self, results, score_threshold: float) -> List[Dict[str, Any]]:
        """把 Milvus 命中解析成统一 chunk 结构，并按尺度阈值过滤。"""
        chunks = []
        for hits in results:
            for hit in hits:
                score = hit.distance
                if score < score_threshold:
                    continue
                chunks.append({
                    "text": hit.entity.get("text"),
                    "score": round(score, 4),
                    "collection_id": hit.entity.get("collection_id"),
                    "document_id": hit.entity.get("document_id"),
                    "chunk_index": hit.entity.get("chunk_index"),
                    "vector_id": hit.entity.get("vector_id"),
                    # 标题由 MySQL 元数据补齐，不在 Milvus 冗余一份中文长字符串。
                    "document_title": None,
                })
        return chunks

    def _hybrid_search_chunks(
        self,
        collection: Collection,
        query: str,
        expr: str,
        top_k: int,
        score_threshold: float,
    ) -> List[Dict[str, Any]]:
        """dense + BM25 两路召回，Milvus 侧 RRFRanker 合并名次。

        口径（用户 2026-11-22 批准方案 A）：**只用一个 ranker，不叠加 TEI 精排**。
        hybrid_search 的位置参数 rerank 与关键字 ranker 只能二选一：
        同时传不会串联两个阶段，ranker 会被静默忽略——所以这里显式拒绝混传，
        并在日志里打印实际分数尺度，防止后续有人以为「RRF 之后还有精排」。
        """
        candidate_k = max(top_k, settings.hybrid_candidate_k)
        dense_req = AnnSearchRequest(
            data=[query],  # 查询文本由 Milvus Function 向量化
            anns_field="dense",
            param={"metric_type": "COSINE", "params": {"ef": 64}},
            limit=candidate_k,
            expr=expr if expr else None,
        )
        sparse_req = AnnSearchRequest(
            data=[query],  # BM25 直接吃文本，由集合上的 analyzer 分词
            anns_field="sparse",
            param={"metric_type": "BM25"},
            limit=candidate_k,
            expr=expr if expr else None,
        )

        ranker = RRFRanker(k=settings.rrf_k)

        # 单 ranker 断言：hybrid_search 的位置参数 rerank 只接受一个 ranker，
        # 混入 RERANK Function 会让其中一方被静默丢弃，分数尺度随之不可预期。
        if settings.rerank_enabled:
            logger.warning(
                "hybrid 模式下 RERANK_ENABLED 被忽略：hybrid_search 只允许一个 ranker（RRF），"
                "不叠加 TEI 精排"
            )
        # App logger 默认 WARNING 级，info 会丢；这里沿用本文件既有 print 口径写 stdout，
        # 让「实际候选数 / 实际 ranker / 分数尺度」可被日志实测，而不是靠推断。
        print(
            f"[hybrid] ranker=RRFRanker(k={settings.rrf_k}) only(no TEI) "
            f"candidate_k={candidate_k} top_k={top_k} score_scale={SCORE_SCALE_RRF}",
            flush=True,
        )

        # 关键字只传 reqs / rerank / limit：不传 ranker=，避免与位置参数混用被客户端静默忽略。
        results = collection.hybrid_search(
            reqs=[dense_req, sparse_req],
            rerank=ranker,
            limit=top_k,
            output_fields=["text", "collection_id", "document_id", "chunk_index", "vector_id"],
        )
        return self._parse_hits(results, score_threshold)

    def search_chunks(
        self,
        query: str,
        companion_id: Optional[str] = None,
        collection_ids: Optional[List[str]] = None,
        top_k: int = 4,
        score_threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """原始 Milvus 检索结果。

        Args:
            query: 查询文本
            companion_id: 伴侣 ID（Partition Key 过滤）
            collection_ids: 知识库 ID 列表（可选过滤）
            top_k: 返回 top K 结果
            score_threshold: 分数下限。dense 模式是 COSINE/TEI 相似度，hybrid 模式是 RRF 名次分

        Returns:
            命中的切片列表，按分数降序
        """
        collection = self._get_collection()
        if not collection_ids:
            return []

        expr = self._build_filter_expr(companion_id, collection_ids)

        try:
            if self.hybrid:
                chunks = self._hybrid_search_chunks(
                    collection, query, expr, top_k, score_threshold
                )
            else:
                chunks = self._dense_search_chunks(
                    collection, query, expr, top_k, score_threshold
                )

            logger.info(
                f"检索完成: mode={'hybrid' if self.hybrid else 'dense'}, "
                f"score_scale={self.score_scale}, query='{query[:50]}...', 命中 {len(chunks)} 条"
            )
            return chunks
        except Exception as e:
            logger.error(f"检索失败: {e}, query='{query[:50]}...'")
            raise

    def _dense_search_chunks(
        self,
        collection: Collection,
        query: str,
        expr: str,
        top_k: int,
        score_threshold: float,
    ) -> List[Dict[str, Any]]:
        """原 dense 单路检索（行为与 2026-11-19 接入时一致，未改动）。"""
        # 构造 ranker（rerank 是查询时传参：不挂 schema、不改集合、无需重建）
        ranker = None
        if settings.rerank_enabled:
            ranker = Function(
                name="rerank",
                function_type=FunctionType.RERANK,
                input_field_names=["text"],
                params={
                    "reranker": "model",
                    "provider": "tei",
                    "queries": [query],  # 数量必须与 search 的 nq 一致（此处 nq=1）
                    "endpoint": settings.tei_endpoint,  # Milvus 容器视角地址，如 http://tei:80
                },
            )

        # 执行检索（query 文本由 Milvus Function 向量化）
        search_kwargs = {
            "data": [query],  # 查询文本
            "anns_field": "dense",
            "param": {"metric_type": "COSINE", "params": {"ef": 64}},
            "limit": top_k,
            "expr": expr if expr else None,
            "output_fields": ["text", "collection_id", "document_id", "chunk_index", "vector_id"],
        }
        if ranker is not None:
            search_kwargs["ranker"] = ranker

        results = collection.search(**search_kwargs)
        # COSINE 下 distance 即余弦相似度；TEI 下是精排分。两者都越大越相似，
        # 结果按分数降序返回（官方 metric.md）。
        return self._parse_hits(results, score_threshold)

    def add_chunks(
        self,
        collection_id: str,
        chunk_ids: List[str],
        texts: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> int:
        """统一入库接口：metadata 中的 companion_id / document_id 原样保留。"""
        if not texts:
            return 0
        if not metadatas or not metadatas[0].get("companion_id"):
            raise ValueError("Milvus 入库必须提供非空 companion_id")
        if not metadatas[0].get("document_id"):
            raise ValueError("Milvus 入库必须提供 document_id")

        return self.insert(
            texts=texts,
            companion_id=str(metadatas[0]["companion_id"]),
            collection_id=str(collection_id),
            document_id=str(metadatas[0]["document_id"]),
            chunk_indices=[int(m["chunk_index"]) for m in metadatas],
            vector_ids=chunk_ids,
        )

    def delete_by_document(self, document_id: str) -> int:
        """按文档 ID 删除切片

        Args:
            document_id: 文档 ID

        Returns:
            删除的切片数量（Milvus 不返回精确数量，返回 -1 表示成功）
        """
        collection = self._get_collection()

        try:
            expr = f'document_id == "{document_id}"'
            collection.delete(expr)
            collection.flush()
            logger.info(f"删除成功: document_id={document_id}")
            return -1  # Milvus delete 不返回数量
        except Exception as e:
            logger.error(f"删除失败: {e}, document_id={document_id}")
            raise

    def delete_by_collection(self, collection_id: str) -> int:
        """按知识库 ID 删除所有切片

        Args:
            collection_id: 知识库 ID

        Returns:
            删除的切片数量（Milvus 不返回精确数量，返回 -1 表示成功）
        """
        collection = self._get_collection()

        try:
            expr = f'collection_id == "{collection_id}"'
            collection.delete(expr)
            collection.flush()
            logger.info(f"删除成功: collection_id={collection_id}")
            return -1
        except Exception as e:
            logger.error(f"删除失败: {e}, collection_id={collection_id}")
            raise

    def delete_chunks(self, collection_id: str, chunk_ids: List[str]) -> None:
        """统一删除接口：按业务 vector_id 删除，不依赖 Milvus 自增主键。"""
        if not chunk_ids:
            return
        collection = self._get_collection()
        ids_str = ",".join(f'"{vector_id}"' for vector_id in chunk_ids)
        try:
            collection.delete(f"vector_id in [{ids_str}]")
            collection.flush()
        except Exception as e:
            logger.error(f"按 vector_id 删除失败: {e}")
            raise

    def drop_collection(self, collection_id: Optional[str] = None):
        """统一清理接口：Milvus 是共享单集合，按知识库删除，不能 drop 整表。"""
        if not self._connected:
            self.connect()

        if utility.has_collection(self.collection_name):
            if collection_id is None:
                raise ValueError("Milvus 业务清理必须指定 collection_id，禁止误删共享集合")
            self.delete_by_collection(collection_id)

    def close(self):
        """关闭连接"""
        if self._connected:
            connections.disconnect("default")
            self._connected = False
            self._collection = None
            logger.info("Milvus 连接已关闭")


# 全局单例
milvus_store = MilvusStore()
