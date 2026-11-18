# Milvus 2.6.0 Rerank 配置与使用指南

> 生成于 2026-11-18。所有关键结论均在本地 Milvus v2.6.0 + pymilvus 3.0.3 上实测验证过（见文末「实测记录」），
> 非实测项均已标注。

## 一、结论速览

| 结论 | 说明 |
|------|------|
| RERANK 是**查询时传参** | 通过 `client.search(..., ranker=Function(...))` 传入，**不挂 schema、无需重建集合**，随时可加可换 |
| v2.6.0 只内置 `tei` / `vllm` 两个 provider | 实测传 `siliconflow` 报 `Unknow rerank provider:siliconflow`；官方 SiliconFlow Ranker 需更高 2.6.x 版本 |
| `vllm` 在本项目不可用 | Windows Docker Desktop 无 GPU 直通，CPU 跑 vLLM 不现实 |
| **实际可用的唯一路线 = TEI 自托管** | 无 API Key、数据不出本机，与 RAG 后端「去外部依赖」取向一致 |
| `milvus.yaml` **无需任何改动** | 镜像内置配置里 `function.rerank.model.providers.tei.enable` 已为 `true` |
| 连接需认证 | RBAC 已启用，`MilvusClient` 必须带 `user/password`（root 当前为默认口令 `Milvus`，建议尽快修改） |

## 二、TEI 服务部署（待实施，实施前需确认 compose diff）

在 `deploy/milvus/docker-compose.yml` 追加（与 `standalone` 同网络，服务名 `tei` 可被 Milvus 容器直接解析）：

```yaml
services:
  # ……现有 standalone 服务保持不动……

  tei:
    container_name: milvus-tei
    image: ghcr.io/huggingface/text-embeddings-inference:cpu-1.8   # 拉取失败时改用 :cpu-latest
    command: ["--model-id", "BAAI/bge-reranker-v2-m3", "--port", "80"]
    environment:
      HF_ENDPOINT: "https://hf-mirror.com"   # 国内加速模型下载，不走镜像源会卡住
    volumes:
      - tei-data:/data                        # 模型缓存，重启/重建容器不重复下载（模型约 2.3GB）
    ports:
      - "8090:80"                             # 宿主机调试用；Milvus 走内部网络，可按需去掉

volumes:
  tei-data:
```

注意：

- TEI CPU 镜像要求 CPU 支持 AVX2（近十年的 CPU 均满足）。
- 首次启动需下载约 2.3GB 模型（走 hf-mirror），耐心等待；`docker compose logs tei` 观察进度。

启动后先在宿主机冒烟验证 TEI 本身：

```bash
# 健康检查
curl http://localhost:8090/health

# rerank 冒烟
curl -X POST http://localhost:8090/rerank -H "Content-Type: application/json" ^
  -d "{\"query\":\"向量数据库有哪些\",\"texts\":[\"Milvus 是开源向量数据库\",\"今天天气不错\"],\"truncate\":true}"
```

## 三、Python 用法（pymilvus 3.0.3）

### 3.1 构造 Ranker

```python
from pymilvus import Function, FunctionType

ranker = Function(
    name="tei_semantic_ranker",          # 仅自定义标识
    input_field_names=["text"],          # 集合中的 VARCHAR 字段（重排依据的原文）
    function_type=FunctionType.RERANK,   # 固定
    params={
        "reranker": "model",               # 固定，启用模型重排
        "provider": "tei",                 # v2.6.0 可选 tei / vllm
        "queries": ["向量数据库有哪些"],     # 查询词列表；数量必须与 search 的 nq 完全一致，否则报错
        "endpoint": "http://tei:80",       # TEI 服务地址；必须是 Milvus 容器可达地址（compose 服务名），
                                           # 不能写 localhost（那指向 Milvus 容器自身）
        "max_client_batch_size": 32,       # 可选，分批调用模型服务的批大小，默认 32
        "truncate": True,                  # 可选，超长输入截断（False 时超长直接报错）
        "truncation_direction": "Right",   # 可选，截断方向 Right（默认）/ Left
    },
)
```

### 3.2 接入标准向量搜索

```python
res = client.search(
    collection_name="your_collection",
    data=[query_vec],                    # nq=1 时 queries 列表长度必须为 1
    anns_field="vec",
    limit=5,
    output_fields=["text"],              # 重排依据字段建议一并取出
    ranker=ranker,                       # 关键：传入 ranker，服务端调用 TEI 重排
    consistency_level="Bounded",
)
# 返回的 hits 顺序/分数 = 重排后的语义相关性分数（不再是向量相似度）
```

混合检索（`hybrid_search` 多路召回）同样支持传 `ranker`（官方文档支持，本项目未实测，接入时以实测为准）。

### 3.3 完整可运行示例（TEI 启动后可直接跑）

```python
from pymilvus import MilvusClient, DataType, Function, FunctionType

client = MilvusClient(uri="http://localhost:19530", user="root", password="<你的密码>")
# ↑ root 口令修改后此处同步更新；建议后续换 milvus_rag 专用账号

COLL = "rerank_demo"
if client.has_collection(COLL):
    client.drop_collection(COLL)

schema = client.create_schema()
schema.add_field("id", DataType.INT64, is_primary=True)
schema.add_field("text", DataType.VARCHAR, max_length=1024)
schema.add_field("vec", DataType.FLOAT_VECTOR, dim=4)
idx = client.prepare_index_params()
idx.add_index(field_name="vec", index_type="FLAT", metric_type="IP")
client.create_collection(COLL, schema=schema, index_params=idx)

docs = [
    {"id": 1, "text": "Milvus 是开源向量数据库", "vec": [0.1, 0.2, 0.3, 0.4]},
    {"id": 2, "text": "今天天气不错",             "vec": [0.11, 0.21, 0.31, 0.41]},
]
client.insert(COLL, docs)
client.flush(COLL)   # 关键：插入后立即 flush，否则紧跟着的检索可能命中 0 条（实测踩过）

ranker = Function(
    name="tei_semantic_ranker",
    input_field_names=["text"],
    function_type=FunctionType.RERANK,
    params={
        "reranker": "model",
        "provider": "tei",
        "queries": ["向量数据库有哪些"],
        "endpoint": "http://tei:80",
        "max_client_batch_size": 32,
        "truncate": True,
        "truncation_direction": "Right",
    },
)

res = client.search(COLL, data=[[0.1, 0.2, 0.3, 0.4]], anns_field="vec",
                    limit=2, output_fields=["text"], ranker=ranker)
print(res)
client.drop_collection(COLL)
```

## 四、若未来升级 Milvus：SiliconFlow 云端 Ranker（未实施，仅供参考）

升级到 2.6 线更高版本后，可用云端重排（需 SiliconFlow API Key，数据出本机）：

```python
ranker = Function(
    name="siliconflow_semantic_ranker",
    input_field_names=["text"],
    function_type=FunctionType.RERANK,
    params={
        "reranker": "model",
        "provider": "siliconflow",
        "model_name": "BAAI/bge-reranker-v2-m3",
        "queries": ["..."],
        # "credential": "<你的 SiliconFlow Key>"   # 或在 Milvus 服务端环境变量 SILICONFLOW_API_KEY
    },
)
```

注意：**v2.6.0 不支持此 provider（实测）**，且升级会要求重新验证部署稳定性（2.6.0 上已踩稳 5 个回归坑，见 `deploy/milvus/README.md`）。

## 五、实测记录（2026-11-18，临时探针已删除、临时集合已清理）

环境：Milvus v2.6.0 standalone（healthy）、pymilvus 3.0.3、root 认证连接。

| 探针 provider | 结果 | 判定 |
|---------------|------|------|
| `not_a_provider`（对照组） | `Unknow rerank provider:not_a_provider` | 错误语义基线 |
| `tei`（endpoint 指向不通端口） | 检索请求正常受理 | **provider 受支持** |
| `vllm`（同上） | 检索请求正常受理 | **provider 受支持** |
| `siliconflow` | `Unknow rerank provider:siliconflow` | **v2.6.0 不支持** |

探针现象备注：插入后未 flush 立即检索会命中 0 条（此时不会触发对 TEI 端点的真实调用），因此「provider 受支持」的判定依据是服务端是否报「Unknow rerank provider」，端到端重排效果在 TEI 部署后以 3.3 节示例冒烟为准。

## 六、后续实施清单（本次未做，按需启动）

1. compose 追加 TEI 服务（diff 报确认 → `docker compose up -d`）
2. TEI 健康检查 + `/rerank` 冒烟（第二节命令）
3. 运行 3.3 节完整示例，确认重排分数与排序生效
4. （可选但建议）修改 root 默认口令，同步更新 README 与连接配置
5. RAG 后端接入（待办③）时，把 ranker 加入检索链路；后端当前无 pymilvus 依赖、向量库仍为 Chroma，届时一并规划

## 参考文档

- [TEI Ranker 官方文档（Milvus）](https://milvus.io/docs/zh/tei-ranker.md)
- [SiliconFlow Ranker 官方文档（Milvus，需更高 2.6.x）](https://milvus.io/docs/zh/siliconflow-ranker.md)
- [pymilvus FunctionType API（v3.0.x）](https://milvus.io/api-reference/pymilvus/v3.0.x/MilvusClient/Collections/FunctionType.md)
- [TEI 官方仓库（Hugging Face）](https://github.com/huggingface/text-embeddings-inference)
