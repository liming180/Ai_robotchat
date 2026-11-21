"""Milvus 向量存储实现（2026-11-19）

特性：
- Partition Key 按伴侣隔离（companion_id）
- 插入后自动 flush（避免查询命中 0 条）
- 查询时由 Milvus Function 服务端调用智谱 Embedding-3 向量化
- 支持按 documentId/collectionId 精确删除
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
    utility,
)
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class MilvusStore:
    """Milvus 向量存储（单集合 + Partition Key 隔离）"""

    def __init__(self):
        self.collection_name = "kb_chunks"
        self._connected = False
        self._collection: Optional[Collection] = None

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
        # 定义字段
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="dense", dtype=DataType.FLOAT_VECTOR, dim=2048),  # Embedding-3 2048 维
            FieldSchema(name="companion_id", dtype=DataType.INT64, is_partition_key=True),  # Partition Key
            FieldSchema(name="collection_id", dtype=DataType.INT64),
            FieldSchema(name="document_id", dtype=DataType.INT64),
            FieldSchema(name="chunk_index", dtype=DataType.INT32),
            FieldSchema(name="vector_id", dtype=DataType.VARCHAR, max_length=255),
        ]

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

        # 加载集合到内存
        self._collection.load()
        logger.info("集合已加载到内存")

    def insert(
        self,
        texts: List[str],
        companion_id: int,
        collection_id: int,
        document_id: int,
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
        query: str,
        companion_id: Optional[int] = None,
        collection_ids: Optional[List[int]] = None,
        top_k: int = 4,
        score_threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """检索切片（查询文本由 Milvus Function 向量化）

        Args:
            query: 查询文本
            companion_id: 伴侣 ID（Partition Key 过滤）
            collection_ids: 知识库 ID 列表（可选过滤）
            top_k: 返回 top K 结果
            score_threshold: 相似度阈值（0-1，COSINE 相似度，越大越相似）

        Returns:
            命中的切片列表，按相似度降序
        """
        collection = self._get_collection()

        # 构造过滤表达式
        filter_expr = []
        if companion_id is not None:
            filter_expr.append(f"companion_id == {companion_id}")
        if collection_ids:
            ids_str = ",".join(str(cid) for cid in collection_ids)
            filter_expr.append(f"collection_id in [{ids_str}]")

        expr = " && ".join(filter_expr) if filter_expr else ""

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

        try:
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

            # 解析结果
            chunks = []
            for hits in results:
                for hit in hits:
                    # COSINE 下 Milvus 返回的 distance 即余弦相似度，越大越相似
                    # （官方 metric.md："A greater value indicates a greater similarity"，结果按相似度降序返回）
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
                    })

            logger.info(f"检索完成: query='{query[:50]}...', 命中 {len(chunks)} 条")
            return chunks
        except Exception as e:
            logger.error(f"检索失败: {e}, query='{query[:50]}...'")
            raise

    def delete_by_document(self, document_id: int) -> int:
        """按文档 ID 删除切片

        Args:
            document_id: 文档 ID

        Returns:
            删除的切片数量（Milvus 不返回精确数量，返回 -1 表示成功）
        """
        collection = self._get_collection()

        try:
            expr = f"document_id == {document_id}"
            collection.delete(expr)
            collection.flush()
            logger.info(f"删除成功: document_id={document_id}")
            return -1  # Milvus delete 不返回数量
        except Exception as e:
            logger.error(f"删除失败: {e}, document_id={document_id}")
            raise

    def delete_by_collection(self, collection_id: int) -> int:
        """按知识库 ID 删除所有切片

        Args:
            collection_id: 知识库 ID

        Returns:
            删除的切片数量（Milvus 不返回精确数量，返回 -1 表示成功）
        """
        collection = self._get_collection()

        try:
            expr = f"collection_id == {collection_id}"
            collection.delete(expr)
            collection.flush()
            logger.info(f"删除成功: collection_id={collection_id}")
            return -1
        except Exception as e:
            logger.error(f"删除失败: {e}, collection_id={collection_id}")
            raise

    def drop_collection(self):
        """删除整个集合（谨慎使用）"""
        if not self._connected:
            self.connect()

        if utility.has_collection(self.collection_name):
            utility.drop_collection(self.collection_name)
            self._collection = None
            logger.warning(f"集合已删除: {self.collection_name}")

    def close(self):
        """关闭连接"""
        if self._connected:
            connections.disconnect("default")
            self._connected = False
            self._collection = None
            logger.info("Milvus 连接已关闭")


# 全局单例
milvus_store = MilvusStore()
