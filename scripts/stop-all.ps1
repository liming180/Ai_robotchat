<#
.SYNOPSIS
停止 AI Companion 的五个服务：前端(3000)、RAG 管理前端(3001)、Python AI(5000)、Java 业务(8081)、RAG 知识库(8002)。
.DESCRIPTION
仅停止本工作区、指定端口的服务进程：先按端口找到实际监听进程，再向上找到启动器
（npm / uvicorn / mvn），递归收集整棵进程树后逐个停止，避免留下孤儿子进程。

安全边界：
- 只认「端口 + 命令行包含本工作区路径或服务标记」的进程，不匹配的只警告不杀。
- 不碰 MySQL / Redis / 其他项目占用 8080 的进程。
- `-Force` 才会停止命令行不匹配但确实占用端口的进程，用于清理残留。

执行（Windows PowerShell 5.1 与 PowerShell 7 均可）：
    powershell -NoProfile -File scripts/stop-all.ps1
    powershell -NoProfile -File scripts/stop-all.ps1 -Service 8081
#>
[CmdletBinding()]
param(
    [ValidateSet('3000', '3001', '5000', '8081', '8002', 'docker', 'All')]
    [string]$Service = 'All',
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PidDirectory = Join-Path $ProjectRoot 'logs\pids'

function Write-Status([string]$Message, [string]$Color = 'Cyan') {
    Write-Host "[stop-all] $Message" -ForegroundColor $Color
}

function Get-DescendantProcesses([int]$ParentId, [array]$AllProcesses) {
    $result = @()
    foreach ($child in @($AllProcesses | Where-Object { $_.ParentProcessId -eq $ParentId })) {
        $result += Get-DescendantProcesses -ParentId $child.ProcessId -AllProcesses $AllProcesses
        $result += $child
    }
    return $result
}

$Targets = @(
    @{ Name = 'frontend';  Port = 3000; WorkDir = (Join-Path $ProjectRoot 'frontend');                        Markers = @('vite');       Launchers = @('node.exe', 'npm.cmd', 'npm.exe', 'cmd.exe') },
    @{ Name = 'rag-frontend'; Port = 3001; WorkDir = (Join-Path $ProjectRoot 'RAG-Knowledge-System\frontend'); Markers = @('vite');       Launchers = @('node.exe', 'npm.cmd', 'npm.exe', 'cmd.exe') },
    @{ Name = 'ai';        Port = 5000; WorkDir = (Join-Path $ProjectRoot 'backend');                         Markers = @('uvicorn');    Launchers = @('python.exe', 'uvicorn.exe') },
    @{ Name = 'rag';       Port = 8002; WorkDir = (Join-Path $ProjectRoot 'RAG-Knowledge-System\backend');     Markers = @('uvicorn');    Launchers = @('python.exe', 'uvicorn.exe') },
    @{ Name = 'java';      Port = 8081; WorkDir = (Join-Path $ProjectRoot 'backend-java');                    Markers = @('spring-boot'); Launchers = @('java.exe', 'mvn.cmd', 'mvn.exe', 'cmd.exe') }
) | Where-Object { $Service -eq 'All' -or ($Service -match '^\d+$' -and $_.Port -eq [int]$Service) }

$Stopped = @()
foreach ($target in $Targets) {
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort $target.Port -ErrorAction SilentlyContinue)
    if ($listeners.Count -eq 0) {
        Write-Status "$($target.Name)（端口 $($target.Port)）当前未监听，跳过。" 'Yellow'
        continue
    }

    foreach ($listener in @($listeners | Select-Object -ExpandProperty OwningProcess -Unique)) {
        $all = @(Get-CimInstance Win32_Process)
        $owner = $all | Where-Object { $_.ProcessId -eq $listener } | Select-Object -First 1
        if ($null -eq $owner) {
            Write-Status "端口 $($target.Port) 的 PID=$listener 已退出，跳过。" 'Yellow'
            continue
        }

        # 从监听进程向上找实际启动器（mvn/npm/uvicorn 会再起子进程，端口在子进程上）
        $root = $owner
        for ($depth = 0; $depth -lt 8 -and $root.ParentProcessId; $depth++) {
            $parent = $all | Where-Object { $_.ProcessId -eq $root.ParentProcessId } | Select-Object -First 1
            if ($null -eq $parent -or $parent.Name -in @('svchost.exe', 'services.exe', 'explorer.exe')) { break }
            $root = $parent
            if ($parent.Name -in $target.Launchers) { break }
        }

        $tree = @($root) + @(Get-DescendantProcesses -ParentId $root.ProcessId -AllProcesses $all)
        $commands = @($tree | ForEach-Object { [string]$_.CommandLine }) -join "`n"
        $hasProjectPath = $commands -like "*$($target.WorkDir)*"

        $markersOk = $true
        foreach ($marker in $target.Markers) {
            if ($commands -notlike "*$marker*") { $markersOk = $false }
        }
        # 监听进程本身也可能直接带标记（如 java -cp ... AiCompanionApplication 不含 spring-boot 字样时靠路径判断）
        $ownerMarkersOk = $true
        foreach ($marker in $target.Markers) {
            if ([string]$owner.CommandLine -notlike "*$marker*") { $ownerMarkersOk = $false }
        }

        if (-not (($hasProjectPath -and $markersOk) -or $ownerMarkersOk)) {
            $message = "端口 $($target.Port) 由 PID=$listener 占用，但命令行不匹配本工作区服务。`n" +
                "进程：$($owner.Name)`n命令：$($owner.CommandLine)`n" +
                '仅当确认它属于本项目后，才加 -Force 停止该进程树。'
            if (-not $Force) {
                Write-Warning $message
                continue
            }
            Write-Status "$message；已指定 -Force。" 'Yellow'
        }

        foreach ($process in @($tree | Sort-Object ProcessId -Descending)) {
            try {
                Write-Status "停止 $($target.Name)：PID=$($process.ProcessId)，$($process.Name)"
                Stop-Process -Id $process.ProcessId -Force -ErrorAction Stop
                $Stopped += $process.ProcessId
            } catch {
                # Windows PowerShell 5.1 不导出 ProcessCommandException 类型；
                # 只在确认进程已消失时忽略竞态，其他错误照常抛出。
                if ($null -ne (Get-Process -Id $process.ProcessId -ErrorAction SilentlyContinue)) { throw }
                Write-Status "PID=$($process.ProcessId) 已随父进程退出，跳过。" 'Yellow'
            }
        }
    }
}

Start-Sleep -Milliseconds 700

# 应用服务先停，最后停 Milvus/TEI（compose stop 保卷保数据，不用 down）。
if ($Service -in @('All', 'docker')) {
    $compose = Join-Path $ProjectRoot 'deploy\milvus\docker-compose.yml'
    if (Test-Path -LiteralPath $compose -PathType Leaf) {
        if (Get-Command docker -ErrorAction SilentlyContinue) {
            Write-Status '停止 Milvus/TEI（docker compose stop，保留卷与数据）...'
            # 与 start-all 同理：docker 的原生 stderr 在 Stop 模式下会变成终止错误。
            $previousEap = $ErrorActionPreference
            $ErrorActionPreference = 'Continue'
            try {
                & docker compose -f $compose stop 2>&1 | ForEach-Object { Write-Status ([string]$_) }
                $composeExit = $LASTEXITCODE
            } finally {
                $ErrorActionPreference = $previousEap
            }
            if ($composeExit -ne 0) {
                throw "docker compose stop 失败（exit=$composeExit）"
            }
            Write-Status 'Milvus/TEI 已停止。' 'Green'
        } else {
            Write-Status '未找到 docker 命令，跳过 Milvus/TEI。' 'Yellow'
        }
    } else {
        Write-Status "compose 文件不存在：$compose，跳过 Milvus/TEI。" 'Yellow'
    }
}

if ($Service -eq 'docker') {
    Write-Status '完成，仅停止 Milvus/TEI。' 'Green'
    exit 0
}

$PortsToCheck = if ($Service -eq 'All') { @(3000, 3001, 5000, 8081, 8002) } else { @([int]$Service) }
$Remaining = @(Get-NetTCPConnection -State Listen -LocalPort $PortsToCheck -ErrorAction SilentlyContinue)
if ($Remaining.Count -gt 0) {
    $ports = ($Remaining | Select-Object -ExpandProperty LocalPort -Unique) -join ', '
    throw "以下端口仍被占用：$ports。请根据上方提示检查后重试。"
}

# 清理 pid 记录文件
if (Test-Path -LiteralPath $PidDirectory) {
    Get-ChildItem -LiteralPath $PidDirectory -Filter '*.pid' -ErrorAction SilentlyContinue |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

Write-Status "完成，已停止 $($Stopped.Count) 个匹配进程。" 'Green'
