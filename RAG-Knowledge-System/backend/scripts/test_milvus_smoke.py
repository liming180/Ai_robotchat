"""Milvus 冒烟测试脚本（2026-11-19）

验证：
1. 插入 → 检索（证明插入+查询两端 embedding 都通）
2. 伴侣隔离（A 伴侣查不到 B 伴侣数据）

运行方式：
    cd RAG-Knowledge-System/backend
    python scripts/test_milvus_smoke.py
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.vectorstore.milvus_store import MilvusStore


def test_insert_and_search():
    """测试插入和检索"""
    print("\n" + "="*60)
    print("测试 1: 插入 → 检索（验证 embedding 链路）")
    print("="*60)

    store = MilvusStore()

    # 插入伴侣 A 的知识
    print("\n[1] 插入伴侣 A 的知识...")
    texts_a = [
        "小暖是一个温柔体贴的 AI 伴侣，喜欢阅读和旅行。",
        "小暖的口头禅是：比想象中顺利。",
        "小暖最喜欢的食物是抹茶蛋糕。",
    ]
    store.insert(
        texts=texts_a,
        companion_id=1,  # 伴侣 A
        collection_id=101,
        document_id=1001,
        chunk_indices=[0, 1, 2],
        vector_ids=["1001::chunk_0", "1001::chunk_1", "1001::chunk_2"],
    )
    print(f"✓ 插入成功: {len(texts_a)} 条切片")

    # 插入伴侣 B 的知识
    print("\n[2] 插入伴侣 B 的知识...")
    texts_b = [
        "冷月是一个理性冷静的 AI 伴侣，擅长逻辑分析。",
        "冷月的口头禅是：让我们理性思考一下。",
        "冷月最喜欢的食物是黑咖啡。",
    ]
    store.insert(
        texts=texts_b,
        companion_id=2,  # 伴侣 B
        collection_id=102,
        document_id=1002,
        chunk_indices=[0, 1, 2],
        vector_ids=["1002::chunk_0", "1002::chunk_1", "1002::chunk_2"],
    )
    print(f"✓ 插入成功: {len(texts_b)} 条切片")

    # 检索伴侣 A 的知识
    print("\n[3] 检索伴侣 A 的知识（query: 口头禅）...")
    results_a = store.search(
        query="口头禅",
        companion_id=1,
        top_k=3,
    )
    print(f"✓ 命中 {len(results_a)} 条")
    for i, chunk in enumerate(results_a):
        print(f"  [{i+1}] score={chunk['score']}, text={chunk['text'][:50]}...")
        assert "小暖" in chunk['text'], f"伴侣 A 的检索结果不应包含伴侣 B 的内容: {chunk['text']}"

    # 检索伴侣 B 的知识
    print("\n[4] 检索伴侣 B 的知识（query: 口头禅）...")
    results_b = store.search(
        query="口头禅",
        companion_id=2,
        top_k=3,
    )
    print(f"✓ 命中 {len(results_b)} 条")
    for i, chunk in enumerate(results_b):
        print(f"  [{i+1}] score={chunk['score']}, text={chunk['text'][:50]}...")
        assert "冷月" in chunk['text'], f"伴侣 B 的检索结果不应包含伴侣 A 的内容: {chunk['text']}"

    print("\n✅ 测试 1 通过：插入和检索正常，embedding 链路畅通")


def test_companion_isolation():
    """测试伴侣隔离"""
    print("\n" + "="*60)
    print("测试 2: 伴侣隔离（A 查不到 B，B 查不到 A）")
    print("="*60)

    store = MilvusStore()

    # 伴侣 A 查询伴侣 B 的专属内容
    print("\n[1] 伴侣 A 查询「黑咖啡」（伴侣 B 的专属内容）...")
    results = store.search(
        query="黑咖啡",
        companion_id=1,  # 伴侣 A
        top_k=5,
    )
    print(f"✓ 命中 {len(results)} 条")
    for chunk in results:
        assert "黑咖啡" not in chunk['text'], f"伴侣 A 不应查到伴侣 B 的内容: {chunk['text']}"
    print("✅ 伴侣 A 未查到伴侣 B 的专属内容")

    # 伴侣 B 查询伴侣 A 的专属内容
    print("\n[2] 伴侣 B 查询「抹茶蛋糕」（伴侣 A 的专属内容）...")
    results = store.search(
        query="抹茶蛋糕",
        companion_id=2,  # 伴侣 B
        top_k=5,
    )
    print(f"✓ 命中 {len(results)} 条")
    for chunk in results:
        assert "抹茶蛋糕" not in chunk['text'], f"伴侣 B 不应查到伴侣 A 的内容: {chunk['text']}"
    print("✅ 伴侣 B 未查到伴侣 A 的专属内容")

    print("\n✅ 测试 2 通过：伴侣隔离生效")


def test_delete():
    """测试删除"""
    print("\n" + "="*60)
    print("测试 3: 删除文档")
    print("="*60)

    store = MilvusStore()

    # 删除伴侣 A 的文档
    print("\n[1] 删除伴侣 A 的文档 (document_id=1001)...")
    store.delete_by_document(document_id=1001)
    print("✓ 删除成功")

    # 检索验证已删除
    print("\n[2] 检索伴侣 A 的知识（query: 口头禅）...")
    results = store.search(
        query="口头禅",
        companion_id=1,
        top_k=3,
    )
    print(f"✓ 命中 {len(results)} 条（应为 0）")
    assert len(results) == 0, f"删除后不应再命中，实际命中 {len(results)} 条"

    print("\n✅ 测试 3 通过：删除生效")


def cleanup():
    """清理测试数据"""
    print("\n" + "="*60)
    print("清理测试数据")
    print("="*60)

    store = MilvusStore()
    store.delete_by_collection(collection_id=101)
    store.delete_by_collection(collection_id=102)
    print("✓ 清理完成")


def main():
    print("\n" + "="*60)
    print("Milvus 冒烟测试")
    print("="*60)
    print("\n配置:")
    print(f"  Host: {os.getenv('MILVUS_HOST', 'localhost')}")
    print(f"  Port: {os.getenv('MILVUS_PORT', '19530')}")
    print(f"  Backend: {os.getenv('VECTOR_STORE_BACKEND', 'milvus')}")

    try:
        # 测试 1: 插入和检索
        test_insert_and_search()

        # 测试 2: 伴侣隔离
        test_companion_isolation()

        # 测试 3: 删除
        test_delete()

        # 清理
        cleanup()

        print("\n" + "="*60)
        print("✅ 所有测试通过！")
        print("="*60)
        print("\n结论:")
        print("  1. 插入和检索正常，Milvus Function embedding 链路畅通")
        print("  2. 伴侣隔离生效，A 查不到 B，B 查不到 A")
        print("  3. 删除功能正常")

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
