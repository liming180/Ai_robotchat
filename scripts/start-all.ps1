<#
.SYNOPSIS
启动 AI Companion 的前端、Python AI 与 RAG 知识库服务。
.DESCRIPTION
服务脱离当前 PowerShell 会话运行，日志写入 logs/。
再次运行会跳过已监听对应端口的服务，不会重复启动。
请使用 PowerShell 7（pwsh）执行：pwsh -File scripts/start-all.ps1
#>
[CmdletBinding()]
param(
    [ValidateSet('3000', '5000', '8002', 'All')]
    [string]$Service = 'All',
    [string]$Python = 'D:\python\python.exe'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$LogDirectory = Join-Path $ProjectRoot 'logs'
New-Item -ItemType Directory -Path $LogDirectory -Force | Out-Null

function Write-Status([string]$Message, [string]$Color = 'Cyan') {
    Write-Host "[start-all] $Message" -ForegroundColor $Color
}

function Test-ServiceReady([string]$Url, [int]$Port, [int]$TimeoutSeconds = 30) {
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        $listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($null -ne $listener) {
            try {
                $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
                if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                    return $true
                }
            } catch {
                # 服务进程已经监听，但尚未完成初始化时继续等待。
            }
        }
        Start-Sleep -Seconds 1
    }
    return $false
}

function Start-Service {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][int]$Port,
        [Parameter(Mandatory)][string]$Executable,
        [Parameter(Mandatory)][string[]]$ArgumentList,
        [Parameter(Mandatory)][string]$WorkingDirectory,
        [Parameter(Mandatory)][string]$HealthUrl
    )

    $existing = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -ne $existing) {
        Write-Status "$Name 已在端口 $Port 监听，PID=$($existing.OwningProcess)，跳过。" 'Yellow'
        return
    }

    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $stdout = Join-Path $LogDirectory "$Name-$stamp.out.log"
    $stderr = Join-Path $LogDirectory "$Name-$stamp.error.log"
    $process = Start-Process -FilePath $Executable -ArgumentList $ArgumentList `
        -WorkingDirectory $WorkingDirectory -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    Write-Status "$Name 启动进程 PID=$($process.Id)，等待端口 $Port ..."

    if (-not (Test-ServiceReady -Url $HealthUrl -Port $Port)) {
        $detail = ''
        if (Test-Path $stderr) {
            $detail = (Get-Content -LiteralPath $stderr -Raw -ErrorAction SilentlyContinue)
            if ($detail.Length -gt 1000) { $detail = $detail.Substring(0, 1000) }
        }
        throw "$Name 未在 30 秒内就绪。检查 $stderr`n$detail"
    }
    Write-Status "$Name 就绪：$HealthUrl；日志：$stdout" 'Green'
}

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Python 不存在：$Python。可通过 -Python 指定完整 python.exe 路径。"
}

if ($Service -in @('All', '5000')) {
    Start-Service -Name 'ai-5000' -Port 5000 -Executable $Python `
        -ArgumentList @('-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '5000') `
        -WorkingDirectory (Join-Path $ProjectRoot 'backend') -HealthUrl 'http://127.0.0.1:5000/health'
}

if ($Service -in @('All', '8002')) {
    Start-Service -Name 'rag-8002' -Port 8002 -Executable $Python `
        -ArgumentList @('-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8002') `
        -WorkingDirectory (Join-Path $ProjectRoot 'RAG-Knowledge-System\backend') `
        -HealthUrl 'http://127.0.0.1:8002/health'
}

if ($Service -in @('All', '3000')) {
    $Npm = (Get-Command npm.cmd -ErrorAction Stop).Source
    Start-Service -Name 'frontend-3000' -Port 3000 -Executable $Npm `
        -ArgumentList @('run', 'dev', '--', '--host', '127.0.0.1', '--port', '3000') `
        -WorkingDirectory (Join-Path $ProjectRoot 'frontend') -HealthUrl 'http://127.0.0.1:3000/'
}

Write-Status '完成。使用 pwsh -File scripts/stop-all.ps1 可停止这些服务。' 'Green'
