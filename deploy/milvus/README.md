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
