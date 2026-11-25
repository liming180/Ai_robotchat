<#
.SYNOPSIS
启动 AI Companion 的五个服务：前端(3000)、RAG 管理前端(3001)、Python AI(5000)、Java 业务(8081)、RAG 知识库(8002)。
.DESCRIPTION
五个服务统一走同一套启动逻辑（Start-Process + 重定向），日志固定写入 logs/<name>.out.log
与 logs/<name>.error.log。**每次启动前会把旧日志归档为 <name>.<stream>.<时间戳>.log**，
每个服务每种流最多保留 KeepArchives 个归档（默认 5），超出自动删除。

设计要点（踩坑记录）：
- **不要在 bash 里拼 `-RedirectStandardOutput "D:\path\\$VAR"`**：bash 双引号会把 `\\` 折成 `\`
  并把 `$VAR` 展开成空串，最终得到一个畸形路径（如 `D:\Ai_robotchat$VAR`），日志被写到
  项目根目录且文件名不对，看起来就像「重定向不生效」。脚本里一律用 Join-Path 构造路径。
- Start-Process 的重定向对 .cmd（mvn.cmd / npm.cmd）与直接 exe 都有效，已实测。
- Java 用 `mvn spring-boot:run`，其真正监听 8081 的是 java 子进程；stop-all 按端口反查整棵进程树。

执行（Windows PowerShell 5.1 与 PowerShell 7 均可）：
    powershell -NoProfile -File scripts/start-all.ps1
    powershell -NoProfile -File scripts/start-all.ps1 -Service 8081
    powershell -NoProfile -File scripts/start-all.ps1 -CheckOnly   # 只校验凭证一致性，退出码 0/1
#>
[CmdletBinding()]
param(
    [ValidateSet('3000', '3001', '5000', '8081', '8002', 'docker', 'All')]
    [string]$Service = 'All',

    # 只做前置校验（凭证一致性），不启动任何服务；退出码 0=通过 / 1=失败
    [switch]$CheckOnly,

    # 默认值与本机环境一致；换机器时用参数覆盖，不要改脚本
    [string]$Python = 'D:\python\python.exe',
    [string]$Maven = 'D:\IDEA\Maven\apache-maven-3.9.9\bin\mvn.cmd',

    # 每个服务每种日志流最多保留几个归档；超出按时间删除最旧的
    [int]$KeepArchives = 5
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$LogDirectory = Join-Path $ProjectRoot 'logs'
$PidDirectory = Join-Path $LogDirectory 'pids'
New-Item -ItemType Directory -Path $LogDirectory -Force | Out-Null
New-Item -ItemType Directory -Path $PidDirectory -Force | Out-Null

# 凭证一致性工具（P2-5 动作 1）：只比 sha256 前 8 位，不打印 token 原值
. (Join-Path $PSScriptRoot 'lib\credentials.ps1')

function Write-Status([string]$Message, [string]$Color = 'Cyan') {
    Write-Host "[start-all] $Message" -ForegroundColor $Color
}

function Test-PortListening([int]$Port) {
    return $null -ne (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue |
        Select-Object -First 1)
}

function Test-ServiceReady([string]$Url, [int]$Port, [int]$TimeoutSeconds = 60) {
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (Test-PortListening -Port $Port) {
            try {
                $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
                if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) { return $true }
            } catch {
                # 端口已监听但应用尚未完成初始化，继续等待
            }
        }
        Start-Sleep -Seconds 1
    }
    return $false
}

<#
归档并清理：每次启动前把现有的 <name>.out.log / .error.log 改名为带时间戳的归档。

为什么每次启动都归档（而不只是超大时归档）：
**Start-Process -RedirectStandardOutput 会在启动时截断目标文件**，实测重启后
日志从 719 字节变成 660 字节——上一次运行的输出直接丢失。因此必须先把旧文件
挪走，让重定向写入一个全新的文件。轮转（仅超大时才归档）+ 截断（每次启动）
两条路径合并成「每次启动都归档」，逻辑更简单且不会丢日志。

保留策略：每个服务的每种流最多保留 KeepArchives 个归档，超出按时间从旧到新删除。
空文件不归档（避免零字节垃圾文件堆积）。
#>
function Invoke-LogArchive([string]$Name) {
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    foreach ($suffix in @('out', 'error')) {
        $file = Join-Path $LogDirectory "$Name.$suffix.log"
        if (-not (Test-Path -LiteralPath $file)) { continue }
        if ((Get-Item -LiteralPath $file).Length -eq 0) {
            Remove-Item -LiteralPath $file -Force -ErrorAction SilentlyContinue
            continue
        }

        $archive = Join-Path $LogDirectory "$Name.$suffix.$stamp.log"
        Move-Item -LiteralPath $file -Destination $archive -Force
        Write-Status "归档日志：$(Split-Path -Leaf $file) -> $(Split-Path -Leaf $archive)" 'DarkGray'

        $old = @(Get-ChildItem -LiteralPath $LogDirectory -Filter "$Name.$suffix.*.log" |
            Sort-Object LastWriteTime -Descending | Select-Object -Skip $KeepArchives)
        foreach ($item in $old) {
            Remove-Item -LiteralPath $item.FullName -Force -ErrorAction SilentlyContinue
            Write-Status "清理旧归档：$($item.Name)" 'DarkGray'
        }
    }
}

function Test-RerankEnabled {
    <#
    读 RAG 后端 .env 的 RERANK_ENABLED，决定要不要拉起并等待 TEI。

    背景（2026-11-22 dense-only 定案）：生产配置 RERANK_ENABLED=false，检索
    走纯 COSINE，TEI 完全不参与。此时还 `compose up -d` 全量会把 milvus-tei
    一起拉起来，实测把 vmmemWSL 从 3122MB 顶到 4016MB，而这台机器只有 8GB，
    「等待 TEI health=200」还要白等最多 600s（TEI CPU 冷启动 3.5–4 分钟），
    且一旦 TEI 没起来就直接 throw，`-Service All/8002/docker` 整条链路起不来。

    读不到文件或读不到该键时按 $false 处理，与 app/core/config.py:57
    `rerank_enabled: bool = False` 的代码默认值保持一致。
    #>
    $envFile = Join-Path $ProjectRoot 'RAG-Knowledge-System\backend\.env'
    if (-not (Test-Path -LiteralPath $envFile -PathType Leaf)) { return $false }
    foreach ($line in (Get-Content -LiteralPath $envFile -Encoding UTF8)) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#')) { continue }
        if ($trimmed -match '^RERANK_ENABLED\s*=\s*(?<v>[^#]*)') {
            $value = $Matches['v'].Trim().Trim('"').Trim("'").ToLowerInvariant()
            return ($value -in @('1', 'true', 'yes', 'on'))
        }
    }
    return $false
}

function Start-DockerStack {
    <#
    启动 Milvus（+ 可选 TEI），并等到 milvus-standalone healthy 才放行。
    8002 启动即连 Milvus，先起 8002 会得到「Milvus 连接失败」的假故障。

    是否连 TEI 一起起、是否等 TEI /health，由 Test-RerankEnabled 决定：
    - RERANK_ENABLED=false（生产当前配置）：只 `up -d standalone`，只等 Milvus
      healthy。TEI 容器即使之前在跑也不会被带起来，省 1GB 级内存与 3.5 分钟等待。
    - RERANK_ENABLED=true：行为与本函数改造前逐字节一致（up -d 全量 + 等两者）。

    只用 up -d / stop，不用 down —— 保卷保数据。
    #>
    $compose = Join-Path $ProjectRoot 'deploy\milvus\docker-compose.yml'
    if (-not (Test-Path -LiteralPath $compose -PathType Leaf)) {
        throw "compose 文件不存在：$compose"
    }
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw '未找到 docker 命令，无法启动 Milvus/TEI。'
    }

    $rerankEnabled = Test-RerankEnabled
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $log = Join-Path $LogDirectory "milvus-compose.$stamp.log"
    if ($rerankEnabled) {
        Write-Status '启动 Milvus/TEI（docker compose up -d，RERANK_ENABLED=true）...'
    } else {
        Write-Status '启动 Milvus（docker compose up -d standalone；RERANK_ENABLED=false，跳过 TEI）...'
    }
    # docker compose 把 "Container xxx Running" 写到 stderr；脚本全局
    # $ErrorActionPreference='Stop' 会把原生 stderr 当成 NativeCommandError。
    # 这里局部降为 Continue，用退出码判断成败。
    $previousEap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $composeOutput = @()
    $composeExit = 1
    try {
        # 用变量接住 2>&1，避免 PowerShell 把 docker 的 stderr 渲染成
        # NativeCommandError 装饰文本写进日志。
        # 只写服务名 standalone：`up -d` 不带服务名会解析整个 compose 文件，
        # 把 tei 也一并拉起（RERANK_ENABLED=false 时纯属浪费内存）。
        if ($rerankEnabled) {
            $composeOutput = & docker compose -f $compose up -d 2>&1
        } else {
            $composeOutput = & docker compose -f $compose up -d standalone 2>&1
        }
        $composeExit = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousEap
    }
    $composeOutput | ForEach-Object { [string]$_ } | Set-Content -LiteralPath $log -Encoding utf8
    if ($composeExit -ne 0) {
        throw "docker compose up 失败（exit=$composeExit），日志：$log"
    }

    # TEI 冷启动实测约 3.5 分钟（Bert 加载 + CPU warmup），180s 不够；
    # Milvus 通常 <60s healthy。
    # RERANK_ENABLED=false 时不探 TEI（它可能压根没起），只等 Milvus healthy。
    $deadline = [DateTime]::UtcNow.AddSeconds(600)
    $lastReport = [DateTime]::UtcNow
    while ([DateTime]::UtcNow -lt $deadline) {
        $milvusState = [string](& docker inspect --format '{{.State.Health.Status}}' milvus-standalone 2>$null)
        $teiOk = $null
        if ($rerankEnabled) {
            $teiOk = $false
            try {
                $resp = Invoke-WebRequest -Uri 'http://127.0.0.1:8080/health' -UseBasicParsing -TimeoutSec 3
                $teiOk = $resp.StatusCode -eq 200
            } catch {
                $teiOk = $false
            }
        }
        $ready = ($milvusState.Trim() -eq 'healthy')
        if ($rerankEnabled) { $ready = $ready -and $teiOk }
        if ($ready) {
            if ($rerankEnabled) {
                Write-Status "Milvus/TEI 就绪（compose 日志：$log）" 'Green'
            } else {
                Write-Status "Milvus 就绪（未启 TEI；compose 日志：$log）" 'Green'
            }
            return
        }
        if (([DateTime]::UtcNow - $lastReport).TotalSeconds -ge 15) {
            if ($rerankEnabled) {
                Write-Status "等待就绪：milvus=$($milvusState.Trim())，TEI health=$teiOk（最长 600s，冷启动约 3.5 分钟）" 'Yellow'
            } else {
                Write-Status "等待就绪：milvus=$($milvusState.Trim())（未启 TEI，最长 600s）" 'Yellow'
            }
            $lastReport = [DateTime]::UtcNow
        }
        Start-Sleep -Seconds 3
    }
    if ($rerankEnabled) {
        throw "Milvus/TEI 600 秒内未就绪，请查看日志：$log"
    }
    throw "Milvus 600 秒内未就绪，请查看日志：$log"
}

function Start-AppService {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][int]$Port,
        [Parameter(Mandatory)][string]$Executable,
        [Parameter(Mandatory)][string[]]$ArgumentList,
        [Parameter(Mandatory)][string]$WorkingDirectory,
        [Parameter(Mandatory)][string]$HealthUrl,
        [int]$TimeoutSeconds = 90
    )

    if (Test-PortListening -Port $Port) {
        $owner = (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue |
            Select-Object -First 1).OwningProcess
        Write-Status "$Name 已在端口 $Port 监听，PID=$owner，跳过。" 'Yellow'
        return
    }

    if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) {
        throw "$Name 的可执行文件不存在：$Executable"
    }
    if (-not (Test-Path -LiteralPath $WorkingDirectory -PathType Container)) {
        throw "$Name 的工作目录不存在：$WorkingDirectory"
    }

    Invoke-LogArchive -Name $Name

    # 固定文件名（不带时间戳），便于 tail -f；旧内容已由 Invoke-LogArchive 归档。
    # 注意 Start-Process 会截断目标文件，所以每次启动必然是全新文件。
    $stdout = Join-Path $LogDirectory "$Name.out.log"
    $stderr = Join-Path $LogDirectory "$Name.error.log"

    $process = Start-Process -FilePath $Executable -ArgumentList $ArgumentList `
        -WorkingDirectory $WorkingDirectory -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput $stdout -RedirectStandardError $stderr

    Set-Content -LiteralPath (Join-Path $PidDirectory "$Name.launcher.pid") -Value $process.Id -Encoding ascii
    Write-Status "$Name 启动中，launcher PID=$($process.Id)，等待端口 $Port ..."

    if (-not (Test-ServiceReady -Url $HealthUrl -Port $Port -TimeoutSeconds $TimeoutSeconds)) {
        $detail = ''
        if (Test-Path -LiteralPath $stderr) {
            $detail = Get-Content -LiteralPath $stderr -Raw -ErrorAction SilentlyContinue
            if ($detail -and $detail.Length -gt 1500) { $detail = $detail.Substring(0, 1500) }
        }
        $outTail = ''
        if (Test-Path -LiteralPath $stdout) {
            $outTail = (Get-Content -LiteralPath $stdout -Tail 30 -ErrorAction SilentlyContinue) -join "`n"
        }
        throw "$Name 未在 $TimeoutSeconds 秒内就绪。`n--- $stderr ---`n$detail`n--- $stdout (tail) ---`n$outTail"
    }

    # 端口真正监听者可能不是 launcher（mvn/npm 会再起子进程），记录实际监听 PID 方便排查
    $listener = (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue |
        Select-Object -First 1).OwningProcess
    Set-Content -LiteralPath (Join-Path $PidDirectory "$Name.port.pid") -Value $listener -Encoding ascii
    Write-Status "$Name 就绪：$HealthUrl（监听 PID=$listener）；日志：$stdout" 'Green'
}

# ---------- 凭证一致性前置检查（P2-5 动作 1）----------
# 任何服务启动之前执行：四处 SERVICE_TOKEN 不一致会让 5000 或 3001 直接 401，
# 请求不进业务逻辑（2026-11-24 故障）。只比 sha256 前 8 位，不打印原值。
# 范围按 -Service 收敛：Java/docker 与 token 无关，跳过。
if ($Service -in @('All', '3000', '3001', '5000', '8002')) {
    $credentialChecks = @(
        [pscustomobject]@{ Name = 'backend/.env'; File = 'backend/.env'; Key = 'SERVICE_TOKEN'; Severity = 'Base' }
    )
    if ($Service -in @('All', '3000', '5000')) {
        $credentialChecks += [pscustomobject]@{
            Name = 'frontend/.env.development'; File = 'frontend/.env.development'
            Key = 'VITE_SERVICE_TOKEN'; Severity = 'Error'
        }
        # 生产构建用，本机 dev 启动不读它：不一致只警告，不阻断
        $credentialChecks += [pscustomobject]@{
            Name = 'frontend/.env.production'; File = 'frontend/.env.production'
            Key = 'VITE_SERVICE_TOKEN'; Severity = 'Warning'
        }
    }
    if ($Service -in @('All', '5000', '8002')) {
        $credentialChecks += [pscustomobject]@{
            Name = 'RAG-Knowledge-System/backend/.env'; File = 'RAG-Knowledge-System/backend/.env'
            Key = 'SERVICE_TOKEN'; Severity = 'Error'
        }
    }
    # 第 4 处（2026-11-25）：RAG 管理前端经 vite proxy 调 8002 的 /retrieve，
    # 该页面的 VITE_RAG_SERVICE_TOKEN 必须与 8002 的 SERVICE_TOKEN 同值，否则 401。
    if ($Service -in @('All', '3001')) {
        $credentialChecks += [pscustomobject]@{
            Name = 'RAG-Knowledge-System/frontend/.env.development'
            File = 'RAG-Knowledge-System/frontend/.env.development'
            Key = 'VITE_RAG_SERVICE_TOKEN'; Severity = 'Error'
        }
    }

    $credentialResult = Test-ServiceTokenConsistency -ProjectRoot $ProjectRoot -Checks $credentialChecks
    foreach ($line in (Format-CredentialReport -Result $credentialResult)) {
        Write-Status $line 'DarkGray'
    }
    if (-not $credentialResult.Ok) {
        $detail = ($credentialResult.Errors -join "`n")
        if ($CheckOnly) {
            Write-Status "凭证一致性校验未通过：`n$detail" 'Red'
            exit 1
        }
        throw "凭证一致性校验未通过，已中止启动：`n$detail"
    }
    Write-Status '凭证一致性校验通过' 'Green'
} else {
    Write-Status "跳过凭证一致性校验（-Service $Service 与 SERVICE_TOKEN 无关）" 'DarkGray'
}

if ($CheckOnly) {
    Write-Status '校验完成（-CheckOnly 模式，未启动任何服务）' 'Green'
    exit 0
}

# ---------- 前置检查 ----------
if ($Service -in @('All', '5000', '8002') -and -not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Python 不存在：$Python。可用 -Python 指定完整 python.exe 路径。"
}
if ($Service -in @('All', '8081') -and -not (Test-Path -LiteralPath $Maven -PathType Leaf)) {
    throw "Maven 不存在：$Maven。可用 -Maven 指定完整 mvn.cmd 路径。"
}

# ---------- 按端口序号启动（Java 最后，它依赖 Python/8002 就绪后调用的接口更稳定）----------
# Milvus/TEI 必须先于 8002：8002 启动即连 Milvus，检索依赖 TEI rerank。
if ($Service -in @('All', '8002', 'docker')) {
    Start-DockerStack
}

if ($Service -in @('All', '3000')) {
    $Npm = (Get-Command npm.cmd -ErrorAction Stop).Source
    Start-AppService -Name 'frontend-3000' -Port 3000 -Executable $Npm `
        -ArgumentList @('run', 'dev', '--', '--host', '127.0.0.1', '--port', '3000') `
        -WorkingDirectory (Join-Path $ProjectRoot 'frontend') -HealthUrl 'http://127.0.0.1:3000/'
}

if ($Service -in @('All', '3001')) {
    # RAG 管理前端：与 3000 共用 npm，走自己的 vite（端口 3001 + /rag-api 代理到 8002）。
    # 8GB 机器上两个 Vite 并存时默认 V8 参数会报「Committing semi space failed」
    # 直接崩（2026-11-25 实测两次），故启动期间临时压低堆上限，启动完立刻还原。
    $Npm = (Get-Command npm.cmd -ErrorAction Stop).Source
    $previousNodeOptions = [Environment]::GetEnvironmentVariable('NODE_OPTIONS', 'Process')
    try {
        [Environment]::SetEnvironmentVariable('NODE_OPTIONS', '--max-old-space-size=384 --max-semi-space-size=2', 'Process')
        Start-AppService -Name 'rag-frontend-3001' -Port 3001 -Executable $Npm `
            -ArgumentList @('run', 'dev', '--', '--host', '127.0.0.1', '--port', '3001') `
            -WorkingDirectory (Join-Path $ProjectRoot 'RAG-Knowledge-System\frontend') `
            -HealthUrl 'http://127.0.0.1:3001/'
    } finally {
        [Environment]::SetEnvironmentVariable('NODE_OPTIONS', $previousNodeOptions, 'Process')
    }
}

if ($Service -in @('All', '5000')) {
    Start-AppService -Name 'ai-5000' -Port 5000 -Executable $Python `
        -ArgumentList @('-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '5000') `
        -WorkingDirectory (Join-Path $ProjectRoot 'backend') -HealthUrl 'http://127.0.0.1:5000/health'
}

if ($Service -in @('All', '8002')) {
    # 8002 启动自检（RAG-Knowledge-System/backend/app/core/security.py
    # verify_secret_alignment）在 settings.jwt_secret_key 为空时直接
    # raise RuntimeError("未读取到 JWT_SECRET")，服务起不来。
    # 密钥只存在于「用户级」环境变量（setx 写入），本进程环境为空——而
    # Start-Process 从当前进程复制环境，所以必须显式把用户级值搬进 Process
    # 作用域，否则 -Service 8002 / All 必然自检失败（2026-11-25 实测）。
    # 与 3001 的 NODE_OPTIONS 同一套写法：改前取值，finally 还原。
    $previousJwtSecret = [Environment]::GetEnvironmentVariable('JWT_SECRET', 'Process')
    $userJwtSecret = [Environment]::GetEnvironmentVariable('JWT_SECRET', 'User')
    if (-not $userJwtSecret) {
        throw "未读取到用户级 JWT_SECRET，8002 启动自检会失败。先执行：setx JWT_SECRET <值>（HS512 需 >=64 字节）并用新终端重试。"
    }
    try {
        [Environment]::SetEnvironmentVariable('JWT_SECRET', $userJwtSecret, 'Process')
        Start-AppService -Name 'rag-8002' -Port 8002 -Executable $Python `
            -ArgumentList @('-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8002') `
            -WorkingDirectory (Join-Path $ProjectRoot 'RAG-Knowledge-System\backend') `
            -HealthUrl 'http://127.0.0.1:8002/health'
    } finally {
        [Environment]::SetEnvironmentVariable('JWT_SECRET', $previousJwtSecret, 'Process')
    }
}

if ($Service -in @('All', '8081')) {
    Start-AppService -Name 'java-8081' -Port 8081 -Executable $Maven `
        -ArgumentList @('-o', 'spring-boot:run') `
        -WorkingDirectory (Join-Path $ProjectRoot 'backend-java') `
        -HealthUrl 'http://127.0.0.1:8081/doc.html' -TimeoutSeconds 120
}

Write-Status "完成。停止服务：powershell -NoProfile -File scripts/stop-all.ps1" 'Green'
Write-Status "日志目录：$LogDirectory（每次启动归档旧日志，每个服务保留最近 $KeepArchives 个归档）" 'Green'
