@echo off
echo ========================================
echo AI Companion 数据库初始化脚本
echo ========================================
echo.

echo [1/3] 检查 MySQL 是否可用...
mysql --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到 MySQL 命令，请确保 MySQL 已安装并添加到 PATH 环境变量
    pause
    exit /b 1
)

echo MySQL 检测成功！
echo.

echo [2/3] 执行数据库初始化脚本...
mysql -u root -pasdfghjkl54321 < src\main\resources\schema.sql
if %errorlevel% neq 0 (
    echo 错误: 数据库初始化失败
    pause
    exit /b 1
)

echo 数据库初始化成功！
echo.

echo [3/3] 数据库初始化完成！
echo.
echo ========================================
echo 接下来请按顺序启动服务：
echo 1. 启动 Redis 服务
echo 2. 启动 Java 后端: cd backend-java; mvn spring-boot:run
echo 3. 启动 AI 服务: cd backend; python main.py
echo ========================================
echo.
pause
