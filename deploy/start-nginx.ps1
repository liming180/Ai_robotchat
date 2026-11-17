# Ai_robotchat 前端 nginx 启停脚本（独立实例，端口 8090）
# 用法：
#   powershell -NoProfile -File deploy\start-nginx.ps1          # 启动
#   powershell -NoProfile -File deploy\start-nginx.ps1 -Stop    # 停止
param([switch]$Stop)

$ErrorActionPreference = 'Stop'
$deployDir = Split-Path -Parent $MyInvocation.MyCommand.Path     # deploy\
$nginxDir  = Join-Path $deployDir 'nginx'

# 复用 Xiaoyi 项目里已存在的 nginx.exe（版本 1.27.4）；找不到时提示自行下载
$nginxExe = 'D:\VM1\Xiaoyi_RAG_bookstore\infra\nginx\nginx-1.27.4\nginx.exe'
if (-not (Test-Path $nginxExe)) {
    Write-Error "未找到 nginx.exe: $nginxExe —— 请下载 nginx 1.27.4 解压到该路径，或修改本脚本指向本地 nginx"
}

# nginx 以 exe 所在目录为默认 prefix，必须用 -p 指到我们的 deploy\nginx\，才能吃到独立 conf/logs/temp
if ($Stop) {
    & $nginxExe -p "$nginxDir\" -s stop
    Write-Host 'nginx (8090) 已停止'
} else {
    # 启动前归档旧日志（nginx 追加写，防止跨天日志混在一起）
    $logDir = Join-Path $nginxDir 'logs'
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    $ts = Get-Date -Format 'yyyyMMdd-HHmmss'
    foreach ($f in 'access.log','error.log') {
        $p = Join-Path $logDir $f
        if ((Test-Path $p) -and ((Get-Item $p).Length -gt 0)) {
            Move-Item $p "$p.$ts.log" -Force
        }
    }
    & $nginxExe -p "$nginxDir\" -t
    if ($LASTEXITCODE -ne 0) { Write-Error 'nginx 配置测试失败，见上方输出' }
    # Start-Process 后台启动：-p 参数跟进程走，不会阻塞脚本，也避免被外层 shell 超时杀掉
    Start-Process -FilePath $nginxExe -ArgumentList @('-p', "$nginxDir\") -WindowStyle Hidden
    Start-Sleep -Milliseconds 1200
    $resp = try { (Invoke-WebRequest -Uri 'http://localhost:8090/' -UseBasicParsing -TimeoutSec 5).StatusCode } catch { 'FAIL' }
    if ($resp -eq 200) { Write-Host 'nginx (8090) 启动成功：http://localhost:8090/' }
    else { Write-Error "nginx 启动后自检失败（HTTP $resp），查 deploy\nginx\logs\error.log" }
}
