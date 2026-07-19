# AI Companion Java Backend

基于 Spring Boot 3.x + Java 21 的 AI 伴侣应用后端服务。

## 技术栈

- **Spring Boot 3.2.x** - Web 框架
- **Java 21** - 编程语言
- **MyBatis Plus** - ORM 框架
- **MySQL 8.x** - 关系型数据库
- **Redis** - 缓存数据库
- **Spring Security + JWT** - 认证授权
- **Knife4j** - API 文档
- **Maven** - 构建工具

## 项目结构

```
src/main/java/com/ai/companion/
├── AiCompanionApplication.java    # 启动类
├── common/                         # 通用类
│   └── Result.java                 # 统一响应格式
├── config/                         # 配置类
│   ├── JwtAuthenticationFilter.java
│   ├── MyBatisPlusConfig.java
│   ├── RedisConfig.java
│   ├── SecurityConfig.java
│   ├── WebConfig.java
│   └── WebSocketConfig.java
├── controller/                     # 控制器
│   ├── AIController.java
│   ├── AuthController.java
│   ├── ChatController.java
│   ├── CompanionController.java
│   └── UserController.java
├── dto/                            # 数据传输对象
│   ├── request/
│   └── response/
├── entity/                         # 实体类
│   ├── Companion.java
│   ├── Conversation.java
│   ├── Message.java
│   ├── User.java
│   └── UserCompanion.java
├── exception/                      # 异常处理
│   └── GlobalExceptionHandler.java
├── mapper/                         # MyBatis Plus Mapper
│   ├── CompanionMapper.java
│   ├── ConversationMapper.java
│   ├── MessageMapper.java
│   ├── UserCompanionMapper.java
│   └── UserMapper.java
├── service/                        # 业务逻辑
│   ├── impl/
│   ├── AIService.java
│   ├── AuthService.java
│   ├── ChatService.java
│   ├── CompanionService.java
│   └── UserService.java
└── util/                           # 工具类
    ├── JwtUtil.java
    └── PasswordUtil.java

src/main/resources/
├── application.yml                 # 应用配置
└── schema.sql                      # 数据库初始化脚本
```

## 快速开始

### 1. 环境要求

- JDK 21+
- Maven 3.8+
- MySQL 8.0+
- Redis 7.0+

### 2. 数据库配置

1. 创建 MySQL 数据库
2. 执行 `schema.sql` 初始化表结构和预置数据
3. 修改 `application.yml` 中的数据库连接配置

### 3. 配置 Redis

修改 `application.yml` 中的 Redis 连接配置

### 4. 启动服务

```bash
# 进入项目目录
cd backend-java

# Maven 编译
mvn clean install

# 启动应用
mvn spring-boot:run
```

或者在 IDE 中直接运行 `AiCompanionApplication.java`

### 5. 访问 API 文档

启动成功后，访问：`http://localhost:8080/doc.html`

## API 接口

### 认证模块 (Auth)

- `POST /api/v1/auth/send-email-code` - 发送邮箱验证码
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/refresh` - 刷新 Token

### 用户模块 (Users)

- `GET /api/v1/users/me` - 获取当前用户信息
- `PUT /api/v1/users/me` - 更新当前用户信息

### 伴侣模块 (Companions)

- `GET /api/v1/companions` - 获取伴侣列表
- `GET /api/v1/companions/{id}` - 获取伴侣详情
- `POST /api/v1/companions` - 创建自定义伴侣
- `PUT /api/v1/companions/{id}` - 更新伴侣人设
- `PATCH /api/v1/companions/{id}/favorite` - 切换收藏状态
- `PATCH /api/v1/companions/{id}/intimacy` - 增加亲密度

### 聊天模块 (Chat)

- `GET /api/v1/chat/conversations` - 获取对话列表
- `POST /api/v1/chat/conversations` - 创建新对话
- `GET /api/v1/chat/conversations/{id}` - 获取对话详情
- `POST /api/v1/chat/conversations/{id}/messages` - 发送消息
- `DELETE /api/v1/chat/conversations/{id}` - 删除对话

### AI 模块 (AI)

- `POST /api/v1/ai/generate-avatar` - AI 生成头像

## 默认配置

- 服务端口：8080
- 数据库：ai_companion
- Redis：localhost:6379
- JWT：有效期 2 小时

## 注意事项

- 邮箱验证码功能使用模拟实现，请根据实际情况集成真实的邮件服务
- AI 回复为模拟实现，请对接真实的 LLM API
- 头像生成使用 DiceBear 公共 API
