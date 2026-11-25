<#
.SYNOPSIS
    启用 Windows 时间服务（w32time）并校准本机时钟。

.DESCRIPTION
    背景（2026-11-25 可用性收口）：
      w32time 处于 Stopped / DEMAND_START，NtpServer 却指向 time.windows.com。
      实测该源在本机 UDP 123 不可达（2s 超时），ntp.aliyun.com 55ms、
      cn.pool.ntp.org 171ms 可用。所以「只启动服务不改源」会得到一个
      永远同步不上的服务，必须先换源再启动。

    本脚本幂等，可重复运行。必须用管理员 PowerShell 执行。

.PARAMETER NtpServers
    NTP 源列表，默认 ntp.aliyun.com + cn.pool.ntp.org。
    写入注册表时每个源带 ,0x9 后缀（客户端模式 + 使用 SpecialPollInterval）。

.PARAMETER PollIntervalSeconds
    轮询间隔，默认 3600（1 小时）。0x9 模式下由 SpecialPollInterval 生效。

.PARAMETER LogPath
    转录日志路径，默认 <项目根>\logs\w32time-setup.log。
    提权进程的输出不会被调用方捕获，靠转录落盘再回读。

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\enable-w32time.ps1
#>
[CmdletBinding()]
param(
    [string[]]$NtpServers = @('ntp.aliyun.com', 'cn.pool.ntp.org'),
    [int]$PollIntervalSeconds = 3600,
    [string]$LogPath = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $LogPath) {
    $projectRoot = Split-Path -Parent $PSScriptRoot
    $logDir = Join-Path $projectRoot 'logs'
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    $LogPath = Join-Path $logDir 'w32time-setup.log'
} else {
    New-Item -ItemType Directory -Path (Split-Path -Parent $LogPath) -Force | Out-Null
}

Start-Transcript -Path $LogPath -Force | Out-Null
try {
    function Assert-Admin {
        $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
        $principal = New-Object Security.Principal.WindowsPrincipal($identity)
        if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
            throw '需要管理员权限：请以「管理员身份运行 PowerShell」后重试。'
        }
    }

    Assert-Admin

    $peerList = ($NtpServers | ForEach-Object { "$_,0x9" }) -join ' '
    Write-Host "[w32time] NTP 源: $peerList（轮询 ${PollIntervalSeconds}s）" -ForegroundColor Cyan

    # 1) 启动类型改为自动。对 w32time 用 sc.exe 比 Set-Service 可靠。
    #    注意 PowerShell 里 `sc` 是 Set-Content 的别名，必须写 sc.exe。
    & sc.exe config w32time start= auto | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "sc config w32time 失败（exit=$LASTEXITCODE）" }

    # 2) 轮询间隔 + 确保 NtpClient 提供程序启用
    $ntpClientKey = 'HKLM:\SYSTEM\CurrentControlSet\Services\W32Time\TimeProviders\NtpClient'
    Set-ItemProperty -Path $ntpClientKey -Name 'Enabled' -Value 1 -Type DWord
    Set-ItemProperty -Path $ntpClientKey -Name 'SpecialPollInterval' -Value $PollIntervalSeconds -Type DWord

    # 3) 删除 Win10/11 默认的「网络可用后启动、约 60s 后自动停止」触发器，
    #    否则服务会被系统自己停掉，看起来像「启用失败」。
    & sc.exe triggerinfo w32time delete | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Warning "sc triggerinfo 删除触发器失败（exit=$LASTEXITCODE），服务可能仍会被系统自动停止" }

    # 4) 先启动服务再写配置：`w32tm /config ... /update` 需要服务处于运行态，
    #    否则返回 0x80070426（ERROR_SERVICE_NOT_ACTIVE，exit=-2147023834）。
    $service = Get-Service -Name w32time
    if ($service.Status -eq 'Running') {
        Restart-Service -Name w32time -Force
    } else {
        Start-Service -Name w32time
    }
    Start-Sleep -Seconds 2

    # 5) 写入 NTP 源与同步模式（非域环境：手动指定源）。
    #    用参数数组传给原生命令，避免手动加引号被 PowerShell 把双引号带进参数值。
    $configArgs = @(
        '/config',
        "/manualpeerlist:$peerList",
        '/syncfromflags:manual',
        '/reliable:no',
        '/update'
    )
    & w32tm @configArgs | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "w32tm /config 失败（exit=$LASTEXITCODE）" }

    # 6) 立即校时（失败不中断：可能是相位差超阈值，让后续轮询处理）
    & w32tm /resync /force
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "w32tm /resync 失败（exit=$LASTEXITCODE）：可能相位差超过 MaxPosPhaseCorrection，等待下一轮自动同步"
    }

    # 7) 回显终态
    Write-Host ''
    Write-Host '=== 服务状态 ===' -ForegroundColor Green
    Get-Service -Name w32time | Format-List Name, Status, StartType | Out-String | Write-Host

    Write-Host '=== 同步状态 ===' -ForegroundColor Green
    & w32tm /query /status

    Write-Host '=== 生效的 NTP 配置 ===' -ForegroundColor Green
    & w32tm /query /configuration | Select-String -Pattern 'NtpServer|Type:|SpecialPollInterval|Enabled:'

    Write-Host ''
    Write-Host "[w32time] 完成。期望 StartType=Automatic、Status=Running，Source 指向 $($NtpServers[0])。" -ForegroundColor Green
}
catch {
    Write-Host "[w32time] 失败：$($_.Exception.Message)" -ForegroundColor Red
    throw
}
finally {
    Stop-Transcript | Out-Null
}
