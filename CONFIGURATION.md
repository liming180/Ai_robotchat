# 配置说明

## 配置信息

### 数据库配置

| 配置项 | 值 |
|--------|-----|
| 数据库类型 | MySQL 8.x |
| 数据库名 | ai_companion |
| 主机地址 | localhost |
| 端口 | 3306 |
| 用户名 | root |
| 密码 | asdfghjkl54321 |

### Redis 配置

| 配置项 | 值 |
|--------|-----|
| 主机地址 | localhost |
| 端口 | 6379 |
| 密码 | asdfghjkl54321 |
| 数据库 | 1 |

### 后端服务配置

| 配置项 | 值 |
|--------|-----|
| 服务端口 | 8080 |
| 上下文路径 | / |
| JWT 密钥 | your-super-secret-key-at-least-256-bits-long-for-hs256-algorithm |
| Access Token 有效期 | 2 小时 |
| Refresh Token 有效期 | 7 天 |
| AI 服务地址 | http://localhost:5000 |

### AI 服务配置

| 配置项 | 值 |
|--------|-----|
| 服务端口 | 5000 |
| 主机地址 | 0.0.0.0 |

## 配置文件位置

- **Java 后端配置**: [backend-java/src/main/resources/application.yml](file:///d:/Ai_robotchat/backend-java/src/main/resources/application.yml)
- **数据库初始化脚本**: [backend-java/src/main/resources/schema.sql](file:///d:/Ai_robotchat/backend-java/src/main/resources/schema.sql)

## 快速启动

### 1. 启动 MySQL 和 Redis

确保 MySQL 和 Redis 服务已启动，使用密码 `asdfghjkl54321`

### 2. 初始化数据库

运行初始化脚本：
```bash
cd backend-java
init-db.bat
```

或者手动执行 SQL 脚本：
```bash
mysql -u root -pasdfghjkl54321 < backend-java/src/main/resources/schema.sql
```

### 3. 启动服务

使用项目启动指南脚本：
```bash
start-all.bat
```

或者手动启动：

- 启动 AI 服务：
  ```bash
  cd backend
  pip install -r requirements.txt
  python main.py
  ```

- 启动 Java 后端：
  ```bash
  cd backend-java
  mvn clean install -DskipTests
  mvn spring-boot:run
  ```

- 启动前端：
  ```bash
  cd frontend
  npm install
  npm run dev
  ```

## 访问地址

| 服务 | 地址 |
|------|------|
| 前端应用 | http://localhost:3000 |
| Java 后端 API | http://localhost:8080 |
| Java 后端文档 | http://localhost:8080/doc.html |
| AI 服务 | http://localhost:5000 |
| AI 服务文档 | http://localhost:5000/docs |
