<#
.SYNOPSIS
停止 AI Companion 的前端、Python AI 与 RAG 知识库服务。
.DESCRIPTION
仅匹配本工作区、指定端口的服务进程，先递归收集子进程再停止，
避免 uvicorn reload 或 npm 留下子进程。不会终止 Java 服务或 MySQL。
执行（Windows PowerShell 5.1 与 PowerShell 7 均可）：
    powershell -NoProfile -File scripts/stop-all.ps1
（PowerShell 7 用户也可用 pwsh -File scripts/stop-all.ps1）
#>
[CmdletBinding()]
param(
    [ValidateSet('3000', '5000', '8002', 'All')]
    [string]$Service = 'All',
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot

function Get-DescendantProcesses([int]$ParentId, [array]$AllProcesses) {
    $result = @()
    foreach ($child in @($AllProcesses | Where-Object { $_.ParentProcessId -eq $ParentId })) {
        $result += Get-DescendantProcesses -ParentId $child.ProcessId -AllProcesses $AllProcesses
        $result += $child
    }
    return $result
}

function Write-Status([string]$Message, [string]$Color = 'Cyan') {
    Write-Host "[stop-all] $Message" -ForegroundColor $Color
}

$Targets = @(
    @{ Name = 'frontend'; Port = 3000; WorkDir = (Join-Path $ProjectRoot 'frontend'); Markers = @('vite') },
    @{ Name = 'ai'; Port = 5000; WorkDir = (Join-Path $ProjectRoot 'backend'); Markers = @('uvicorn', '--port 5000') },
    @{ Name = 'rag'; Port = 8002; WorkDir = (Join-Path $ProjectRoot 'RAG-Knowledge-System\backend'); Markers = @('uvicorn', '--port 8002') }
) | Where-Object { $Service -eq 'All' -or $_.Port -eq [int]$Service }

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

        # 从监听进程向上找到实际启动器（uvicorn.exe / npm / shell），再收集整棵进程树。
        $root = $owner
        for ($depth = 0; $depth -lt 8 -and $root.ParentProcessId; $depth++) {
            $parent = $all | Where-Object { $_.ProcessId -eq $root.ParentProcessId } | Select-Object -First 1
            if ($null -eq $parent -or $parent.Name -in @('svchost.exe', 'services.exe', 'explorer.exe')) { break }
            $root = $parent
            if ($parent.Name -in @('uvicorn.exe', 'npm.exe', 'npm.cmd', 'cmd.exe', 'powershell.exe', 'pwsh.exe', 'bash.exe')) {
                break
            }
        }
        $tree = @($root) + @(Get-DescendantProcesses -ParentId $root.ProcessId -AllProcesses $all)
        $commands = @($tree | ForEach-Object { [string]$_.CommandLine }) -join "`n"
        $hasProjectPath = $commands -like "*$($target.WorkDir)*"
        $hasMarkers = $true
        foreach ($marker in $target.Markers) {
            if ($commands -notlike "*$marker*") { $hasMarkers = $false }
        }
        # uvicorn/npm 通过工作目录区分项目时，进程命令行不含目录；以监听进程的命令行为准。
        $ownerCommand = [string]$owner.CommandLine
        $ownerMarkers = $true
        foreach ($marker in $target.Markers) {
            if ($ownerCommand -notlike "*$marker*") { $ownerMarkers = $false }
        }
        $isScoped = $hasProjectPath -or $ownerMarkers

        if (-not ($isScoped -and $hasMarkers)) {
            $message = "端口 $($target.Port) 由 PID=$listener 占用，但命令行不匹配本工作区服务。`n" +
                "进程：$($owner.Name)`n命令：$($owner.CommandLine)`n" +
                '仅当确认它属于本项目后，才加 -Force 停止该进程树。'
            if (-not $Force) {
                Write-Warning $message
                continue
            }
            Write-Status "$message；已指定 -Force。" 'Yellow'
        }
        $matched = $tree

        foreach ($process in @($matched | Sort-Object ProcessId -Descending)) {
            try {
                Write-Status "停止 $($target.Name)：PID=$($process.ProcessId)，$($process.Name)"
                Stop-Process -Id $process.ProcessId -Force -ErrorAction Stop
                $Stopped += $process.ProcessId
            } catch {
                # Windows PowerShell 5.1 不导出 ProcessCommandException 类型；
                # 只在确认进程已消失时忽略竞态，其他错误照常抛出。
                if ($null -ne (Get-Process -Id $process.ProcessId -ErrorAction SilentlyContinue)) {
                    throw
                }
                Write-Status "PID=$($process.ProcessId) 已随父进程退出，跳过。" 'Yellow'
            }
        }
    }
}

Start-Sleep -Milliseconds 700
$Remaining = @()
if ($Service -eq 'All') {
    $Remaining = @(Get-NetTCPConnection -State Listen -LocalPort 3000,5000,8002 -ErrorAction SilentlyContinue)
} else {
    $Remaining = @(Get-NetTCPConnection -State Listen -LocalPort ([int]$Service) -ErrorAction SilentlyContinue)
}
if ($Remaining.Count -gt 0) {
    $ports = ($Remaining | Select-Object -ExpandProperty LocalPort -Unique) -join ', '
    throw "以下端口仍被占用：$ports。请根据上方提示检查后重试。"
}
Write-Status "完成，已停止 $($Stopped.Count) 个匹配进程。" 'Green'
