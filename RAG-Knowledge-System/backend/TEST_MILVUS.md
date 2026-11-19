# Milvus 冒烟测试手动执行指南

## 前置条件

1. Milvus 服务已启动（`docker ps | grep milvus` 显示 healthy）
2. Python 依赖已安装（`pip show pymilvus` 显示 3.0.x）
3. 配置文件已更新（`.env` 中 `VECTOR_STORE_BACKEND=milvus`）

## 执行步骤

### 1. 确认配置

检查 `RAG-Knowledge-System/backend/.env` 文件：

```bash
# 应该包含以下配置
VECTOR_STORE_BACKEND=milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_USER=
MILVUS_PASSWORD=
```

### 2. 运行冒烟测试

```bash
cd RAG-Knowledge-System/backend
set PYTHONIOENCODING=utf-8
python scripts/test_milvus_smoke.py
```

### 3. 预期输出

```
============================================================
Milvus 冒烟测试
============================================================

配置:
  Host: localhost
  Port: 19530
  Backend: milvus

============================================================
测试 1: 插入 → 检索（验证 embedding 链路）
============================================================

[1] 插入伴侣 A 的知识...
✓ 插入成功: 3 条切片

[2] 插入伴侣 B 的知识...
✓ 插入成功: 3 条切片

[3] 检索伴侣 A 的知识（query: 口头禅）...
✓ 命中 3 条
  [1] score=0.9xxx, text=小暖的口头禅是：比想象中顺利。...
  [2] score=0.8xxx, text=小暖是一个温柔体贴的 AI 伴侣...
  [3] score=0.7xxx, text=小暖最喜欢的食物是抹茶蛋糕。...

[4] 检索伴侣 B 的知识（query: 口头禅）...
✓ 命中 3 条
  [1] score=0.9xxx, text=冷月的口头禅是：让我们理性思考一下。...
  ...

✅ 测试 1 通过：插入和检索正常，embedding 链路畅通

============================================================
测试 2: 伴侣隔离（A 查不到 B，B 查不到 A）
============================================================

[1] 伴侣 A 查询「黑咖啡」（伴侣 B 的专属内容）...
✓ 命中 0 条
✅ 伴侣 A 未查到伴侣 B 的专属内容

[2] 伴侣 B 查询「抹茶蛋糕」（伴侣 A 的专属内容）...
✓ 命中 0 条
✅ 伴侣 B 未查到伴侣 A 的专属内容

✅ 测试 2 通过：伴侣隔离生效

============================================================
测试 3: 删除文档
============================================================

[1] 删除伴侣 A 的文档 (document_id=1001)...
✓ 删除成功

[2] 检索伴侣 A 的知识（query: 口头禅）...
✓ 命中 0 条（应为 0）

✅ 测试 3 通过：删除生效

============================================================
清理测试数据
============================================================
✓ 清理完成

============================================================
✅ 所有测试通过！
============================================================

结论:
  1. 插入和检索正常，Milvus Function embedding 链路畅通
  2. 伴侣隔离生效，A 查不到 B，B 查不到 A
  3. 删除功能正常
```

## 故障排查

### 问题 1: `AttributeError: 'Settings' object has no attribute 'MILVUS_HOST'`

**原因**：配置属性名大小写不匹配

**解决**：检查 `app/core/config.py` 中的配置项是小写（`milvus_host`），代码中也要用小写

### 问题 2: 插入成功但检索命中 0 条

**可能原因**：
1. 插入后未 flush（已在代码中自动 flush）
2. Milvus Function embedding 调用失败（检查 Milvus 日志）
3. 智谱 API Key 无效（检查 `deploy/milvus/milvus.yaml`）

**排查步骤**：
```bash
# 查看 Milvus 日志
docker logs milvus-standalone --tail 100 | grep -i "embedding\|error"

# 检查集合是否存在
docker exec -it milvus-standalone milvus_cli
> show collections
```

### 问题 3: 连接失败

**检查**：
```bash
# 确认 Milvus 容器运行
docker ps | grep milvus

# 确认端口可访问
curl http://localhost:9091/healthz
```

### 问题 4: 中文乱码

**解决**：设置环境变量 `PYTHONIOENCODING=utf-8`

## 测试通过后

测试全部通过后，执行以下操作：

1. 提交代码：
   ```bash
   git add RAG-Knowledge-System/backend/
   git commit -m "feat(rag): Milvus 基础接入（vectorstore 切换开关）

   ## 新增
   - app/vectorstore/milvus_store.py: Milvus 向量存储实现
     * Partition Key 伴侣隔离
     * 插入后自动 flush
     * Embedding 由 Milvus Function 服务端调用智谱 Embedding-3
   - scripts/test_milvus_smoke.py: 冒烟测试脚本
   - TEST_MILVUS.md: 测试执行指南

   ## 修改
   - app/core/config.py: 新增 Milvus 配置项和 vector_store_backend 开关
   - .env.example: 补充 Milvus 配置模板
   - requirements.txt: 新增 pymilvus>=2.6.0
   - app/vectorstore/store.py: 统一接口，支持 Milvus/Chroma 切换

   ## 特性
   - 旧数据保留：Chroma 数据不迁移，回退开关切回时旧数据还在
   - 伴侣隔离：Partition Key 按默认参数建，A 查不到 B
   - 冒烟验证：插入→检索→隔离→删除全链路测试通过
   "
   ```

2. 准备第二段 TEI+rerank 接入

## 注意事项

- 测试脚本会创建测试数据（companion_id=1/2, collection_id=101/102），测试完成后自动清理
- 如果测试中断，可手动运行 `cleanup()` 函数清理
- 生产环境使用前，建议修改 Milvus root 默认密码
