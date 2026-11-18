# RAG 知识库管理前端（端口 3001）

Vue 3 + TypeScript + Vite 5 + Pinia + Tailwind CSS + element-plus，与主项目 `frontend/` 完全同栈。
管理 AI 伴侣的角色专属知识库：知识库 CRUD、文档上传 / 手动知识、任务进度、检索调试。

## 启动

```bash
cd RAG-Knowledge-System/frontend
npm install
npm run dev        # 开发服务器 http://localhost:3001
npm run build      # vue-tsc 类型检查 + 打包
npm run check      # 仅 TypeScript 类型检查
npm run lint       # ESLint（lint:fix 自动修复）
```

## 依赖服务

| 服务 | 地址 | 用途 |
| --- | --- | --- |
| RAG 后端 | http://localhost:8002 | 知识库 / 文档 / 检索接口 |
| Java 业务后端 | http://localhost:8081 | 登录（8002 `/api/v1/auth/login` 转发到 8081，账号即主应用账号） |

## 配置

- `.env.development`：`VITE_RAG_API_BASE_URL`（RAG 后端地址，默认 http://localhost:8002），不入库；模板为 `.env.example`。
- 登录后的 accessToken 存 localStorage（key：`rag_access_token`），所有请求自动带 `Authorization: Bearer`；401 自动跳回登录页。
- JWT 鉴权强制化属方案 Phase 2（见 `docs/RAG知识库技术栈方案.md`），当前 8002 对管理接口暂未强制校验，前端已按带 token 方式实现，Phase 2 上线后无需返工。
