"""Milvus 分批写入防回归测试。

背景（2026-11-24）：Milvus 2.6.0 单次 insert 上限 64 条，超出返回
code=1214「input数组最大不得超过64条」。原实现整篇文档一次 insert，
任何 >64 切片的文档都会入库失败；历史回归文档最多 30 块，所以长期未暴露。
生产建库时一篇 69 块的文档直接失败才发现。

本测试用假 collection 验证切窗逻辑，不依赖 Milvus 在线：
- 150 条 -> 3 次 insert（64/64/22）
- 每次都不超过 MAX_INSERT_BATCH
- flush 只调用一次
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.vectorstore.milvus_store import MAX_INSERT_BATCH, MilvusStore  # noqa: E402


class FakeCollection:
    def __init__(self):
        self.batches = []
        self.flush_count = 0

    def insert(self, entities):
        self.batches.append(len(entities))
        if len(entities) > MAX_INSERT_BATCH:
            raise RuntimeError("单次 insert 超过 64 条")

    def flush(self):
        self.flush_count += 1


def make_store(fake):
    """绕过 __init__ 的连接逻辑，直接注入假 collection。"""
    store = object.__new__(MilvusStore)
    store._collection = fake
    store._connected = True
    return store


def call_insert(store, n):
    return store.insert(
        texts=[f"文本{i}" for i in range(n)],
        companion_id="preset-2",
        collection_id="c-test",
        document_id="d-test",
        chunk_indices=list(range(n)),
        vector_ids=[f"d-test::chunk_{i}" for i in range(n)],
    )


def test_batch_size_constant_is_64():
    assert MAX_INSERT_BATCH == 64


def test_over_64_chunks_are_split():
    fake = FakeCollection()
    store = make_store(fake)
    assert call_insert(store, 150) == 150
    assert fake.batches == [64, 64, 22]
    assert all(b <= MAX_INSERT_BATCH for b in fake.batches)
    assert sum(fake.batches) == 150
    assert fake.flush_count == 1


def test_exactly_64_single_batch():
    fake = FakeCollection()
    store = make_store(fake)
    assert call_insert(store, 64) == 64
    assert fake.batches == [64]
    assert fake.flush_count == 1


def test_under_64_single_batch():
    fake = FakeCollection()
    store = make_store(fake)
    assert call_insert(store, 3) == 3
    assert fake.batches == [3]


def test_empty_returns_zero_without_flush():
    fake = FakeCollection()
    store = make_store(fake)
    assert call_insert(store, 0) == 0
    assert fake.batches == []
    assert fake.flush_count == 0
