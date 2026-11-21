# Milvus 部署指南

## 前置要求

- Docker Desktop 已安装并运行
- Docker Compose v2.x
- 端口 19530/9091 空闲（使用内嵌 etcd 和本地存储，无需额外端口）

## 部署步骤

### 1. 配置密钥

复制配置模板并填入真实密钥：

```bash
cd deploy/milvus
cp milvus.yaml.example milvus.yaml
```

编辑 `milvus.yaml`，将 `sk-***` 替换为真实的智谱 API Key。

### 2. 启动服务

```bash
docker compose up -d
```

等待约 1-2 分钟，容器健康检查通过：

```bash
docker compose ps
```

应看到 `milvus-standalone` 容器状态为 `healthy`。

### 3. 验证服务

- **Milvus gRPC**：`localhost:19530`
- **Milvus WebUI**：http://localhost:9091

### 4. 创建 RBAC 账号（可选）

使用 Attu 或 Milvus CLI 连接后创建专用账号：

```python
from pymilvus import connections, utility

connections.connect(
    alias="default",
    host="localhost",
    port="19530",
    user="root",
    password="<你的密码>"  # 默认 root 密码，首次登录后建议修改
)

# 创建用户（替换 your_secure_password 为实际密码）
utility.create_user(user="milvus_rag", password="your_secure_password")

# 授权（根据实际需求调整）
utility.grant_privilege(
    role_name="public",
    object="Global",
    object_name="*",
    privilege="CreateCollection",
    user="milvus_rag"
)
```

将创建的账号密码写入 `RAG-Knowledge-System/backend/.env`：

```
MILVUS_USER=milvus_rag
MILVUS_PASSWORD=<你的密码>***  # 替换为实际密码
```

## 停止服务

```bash
docker compose down
```

数据持久化在 Docker volumes 中，重启不丢失。

## 清理数据（谨慎）

```bash
docker compose down -v  # 删除所有数据卷
```

## 故障排查

### 容器启动失败

查看日志：

```bash
docker compose logs standalone
```

### 健康检查超时

首次启动需要拉取镜像和初始化，耐心等待 2-3 分钟。

### 端口冲突

检查端口占用：

```bash
netstat -ano | findstr "19530 9091"
```

修改 `docker-compose.yml` 中的端口映射。

## Milvus v2.6.0 已知回归与 workaround

自定义 `milvus.yaml` 挂载到 `/milvus/configs/milvus.yaml` 会**整体替换**镜像内置配置；
v2.6.0 部分参数的代码兜底默认值与内置 yaml 不一致，缺项会启动失败。以下三处必须显式配置：

| # | 症状 | 原因 | workaround |
|---|------|------|------------|
| 1 | panic「内嵌 etcd 不能用于分布式模式」 | 2.6.0 组件角色误判 | compose 环境变量 `DEPLOY_MODE=STANDALONE`（官方 issue [#43760](https://github.com/milvus-io/milvus/issues/43760)） |
| 2 | 19530 端口自冲突（rootCoord 与 Proxy 抢端口） | 2.6.0 代码把 rootCoord 默认端口回归为 19530 | yaml 显式固定各组件端口：rootCoord=53100、queryCoord=19531、dataNode=21124、dataCoord=13333、queryNode=21123、streamingNode=22222 |
| 3 | panic「invalid stats config, ... minSizeFromIdleTime:0」 | `dataCoord.segment.minSizeFromIdleToSealed` 代码兜底为 0（内置 yaml 默认 16） | yaml 显式 `minSizeFromIdleToSealed: 16` |

| 4 | 建集合等 DDL 全部超时卡死，日志反复出现 `kafka ... 9092 Connection refused` | 精简 yaml 缺 `mq:`/`rocksmq:` 段，2.6.0 自动选型把 WAL 误落到 Kafka（本地并无 Kafka） | `milvus.yaml` 改用镜像内置完整配置 + 覆盖点重建，并显式 `mq.type: rocksmq` |
| 5 | 建集合（含外部函数）报 404，智谱网关返回 `path=/v4` | openai provider 把 `url` 当作完整端点直接 POST，不自动追加 `/embeddings` | `url` 必须写全：`https://open.bigmodel.cn/api/paas/v4/embeddings` |

> 当前 `milvus.yaml` = 镜像内置完整配置 + 少量覆盖点（etcd 内嵌与数据目录、`mq.type: rocksmq`、local 存储、RBAC、日志路径、智谱凭证、openai provider 的 credential/url）。不要改回精简版。

启动验证标准：`curl http://localhost:9091/healthz` 返回 OK，且容器 `running`、restarts=0 稳定 30 秒以上；建集合、带智谱 embedding 函数的插入与检索冒烟通过。

## 参考文档

- [Milvus 官方文档](https://milvus.io/docs)
- [Milvus Function 配置](https://milvus.io/docs/zh/embedding-function-overview.md)

## TEI Rerank 部署与收官（2026-11-20/21）

### 模型缓存手术修复

TEI 首次启动下载 `model.safetensors` 失败的根因不是网络，而是 hf-hub chunked 下载器的
`.part` 文件比完整文件**多 8 字节**（末 chunk 对齐尾巴）：以 `.part` 当前长度为续传起点发
`Range: bytes=2271071860-` 必被服务器 416 拒绝，无限冻结；且 515MiB 起整段错位损坏（od 逐字节对照证实）。

修复：`truncate` 到 514MiB 安全线 → 容器内 curl 单流循环续拉 1.73GB（25 轮断流续传零损失）→
`sha256 == d9e3e081…5286`（LFS oid 即内容 sha256）通过后 rename 成 blob + 建 snapshot symlink。

关键经验：
- HF resolve 响应的 **ETag 不是内容 sha256**，blob 名（即 `.part` 名去后缀）才是 LFS oid；
- 校验唯一可信手段是 **od 逐字节对照**（busybox 下 `tr -d \000` 的八进制转义会被 sh 吃掉变删字符 `0`，
  `dd` 大块扫描统计不可信）；
- 官方源尾段本身完好（最后 1 字节 206 可拉），错位发生在下载器侧而非 CDN。

### warmup OOM（SIGKILL 137）

Docker VM 仅 3.7GB（宿主仅 8GB、无 `.wslconfig` 默认 50%）：fp32 全量加载 warmup 时被内核
OOM killer 击杀，`restart: unless-stopped` 导致无限重启。**fp16 不够**——权重虽降到 1.1GB，
但 warmup 的激活瞬态由 `max_batch_tokens=16384` 驱动可达数 GB（比权重还大）。最终双参数修复：

```
--dtype float16 --max-batch-tokens 2048
```

注意：running 容器 `inspect .State.ExitCode=0` 是占位值，真实退出码要容器退出后再看。

### 最终 compose 形态

- `cpu-1.8` 镜像 + 上述双参数 + `HF_HUB_OFFLINE=1`（模型全缓存，代理变量已删）
- ONNX 探测瞬间连接失败属设计内回退链（仓库无 ONNX，回退 safetensors 缓存命中）
- 就绪判定：宿主机 `curl http://127.0.0.1:8080/health` 返回 200

### Rerank 开关对照冒烟（2026-11-21）

链路：RAG 8002 配置层 → Milvus ranker Function（查询时传参，endpoint=`http://tei:80` 为
**Milvus 容器视角**）→ Milvus 容器调 TEI 容器 → fp16 推理 → 分数回填重排。

同一 query 开/关各查一次（8 条书城域文本，临时 companion_id=999，跑完即清）：

| query | rerank 开 top3 分数 | rerank 关（纯 COSINE）top3 分数 | 结论 |
|-------|--------------------|------------------------------|------|
| 借书最多能借几本 | **0.9662 / 0.1237 / 0.0026** | 0.7541 / 0.6282 / 0.6076 | 顺序一致但 rerank 拉开三级梯度，COSINE 挤在 0.61-0.75 无法做阈值过滤 |
| 押金怎么收，能退吗 | 0.1198 / 0.0031 / 0.0001 | 0.5774 / 0.4765 / 0.4670 | **2/3 名被 rerank 校正**（COSINE 词面向量把会员等级排到第 2） |
| 晚上几点闭馆 | **0.4285** / 0.0003 / 0.0 | 0.5684 / 0.4974 / 0.4625 | 部分匹配 rerank 给中等分（诚实），COSINE 虚高 |

配置：`RAG-Knowledge-System/backend/.env` 的 `RERANK_ENABLED=true`（`TEI_ENDPOINT` 默认值即
`http://tei:80`，可不写）；开关在 `milvus_store.search` 内动态读取，改 `.env` 后重启 8002 生效。

### 网络与代理教训

- 代理客户端扛不住高频连发探测（TLS EOF → 端口拒连），但**单流 + 断点续传循环**可用；
- hf-mirror 对该 LFS 文件 308 直接回官方源，国内直连通道无效；
- 宿主 curl 的「直连 200」可能被本机加速器反代接管（响应头 `Server: WattToolkit` 暴露），
  判断真实网络路径要看响应头而非状态码。
