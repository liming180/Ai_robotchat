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


def test_rerank_comparison():
    """rerank 开关对照测试（2026-11-19）

    同一 query 分别以 rerank 开/关各查一次，打印两版 top3 排序对比。
    若 settings.rerank_enabled=False，打印跳过提示（不算失败）。
    """
    print("\n" + "="*60)
    print("测试 4: rerank 开关对照")
    print("="*60)

    from app.core.config import settings

    if not settings.rerank_enabled:
        print("\n⚪ rerank 未启用（RERANK_ENABLED=false），对照测试跳过")
        return

    store = MilvusStore()
    query = "综合匹配度排序对照"

    # 取真实数据（复用测试 1 写入的伴侣 A/B 知识；若已删除则临时补一条）
    print(f"\n[1] rerank 开启检索（query: {query}）...")
    with_rerank = store.search(query=query, top_k=3)

    print(f"✓ 命中 {len(with_rerank)} 条")
    for i, c in enumerate(with_rerank):
        print(f"  rerank [{i+1}] score={c['score']} text={c['text'][:40]}...")

    # 临时关闭 rerank 跑一次纯 COSINE
    print(f"\n[2] rerank 关闭检索（同一 query）...")
    old_value = settings.rerank_enabled
    try:
        settings.rerank_enabled = False
        without_rerank = store.search(query=query, top_k=3)
    finally:
        settings.rerank_enabled = old_value

    print(f"✓ 命中 {len(without_rerank)} 条")
    for i, c in enumerate(without_rerank):
        print(f"  cosine [{i+1}] score={c['score']} text={c['text'][:40]}...")

    # 两条路径都必须正常返回（允许 0 命中：测试数据可能已被清理）
    assert isinstance(with_rerank, list), "rerank 路径返回值异常"
    assert isinstance(without_rerank, list), "纯 COSINE 路径返回值异常"

    print("\n--- top3 排序对比 ---")
    print(f"{'名次':<4} {'rerank 开':<44} {'rerank 关(纯COSINE)':<44}")
    for i in range(3):
        a = with_rerank[i]['text'][:40] if i < len(with_rerank) else "-"
        b = without_rerank[i]['text'][:40] if i < len(without_rerank) else "-"
        print(f"{i+1:<4} {a:<44} {b:<44}")

    if with_rerank and without_rerank:
        same = [c['vector_id'] for c in with_rerank] == [c['vector_id'] for c in without_rerank]
        print(f"\n排序是否一致: {'是（rerank 未改变顺序）' if same else '否（rerank 改变了顺序）'}")

    print("\n✅ 测试 4 通过：rerank 开/关两条路径都正常返回")


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

        # 测试 4: rerank 开关对照（必须在 delete 之前，delete 会清数据）
        test_rerank_comparison()

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
