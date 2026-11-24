<#
凭证一致性工具（P2-5 动作 1）。

用途：启动前比对 backend / RAG / frontend 三处 SERVICE_TOKEN 是否同值，
只输出长度与 sha256 前 8 位，**永不打印原值**。

设计要点：
- 解析 .env 时忽略注释与空行，支持 `export ` 前缀、单双引号、CRLF、UTF-8 BOM；
  同名键出现多次时以最后一行为准（与 python-dotenv 行为一致）。
- 比对位置由调用方传入（Checks），按 Service 决定检查哪些文件。
- 函数只返回结果对象，不打印、不抛错；由 start-all.ps1 决定如何展示与中止。
#>

function Get-DotEnvValue {
    <#
    读取 .env 中指定键的值。文件不存在、键不存在或值为空都返回 $null。
    引号包裹的值会去掉外层引号；不处理行尾注释（token 可能包含 #）。
    #>
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Key
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }

    $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 -ErrorAction Stop
    if ($null -eq $raw) { return $null }

    $found = $null
    foreach ($line in ($raw -split '\r?\n')) {
        $trimmed = $line.Trim()
        if ($trimmed.Length -eq 0) { continue }
        if ($trimmed.StartsWith('#')) { continue }
        if ($trimmed -notmatch '^(?:export\s+)?([A-Za-z0-9_]+)\s*=\s*(.*)$') { continue }
        if ($Matches[1] -ne $Key) { continue }

        $value = $Matches[2].Trim()
        if ($value.Length -ge 2 -and
            (($value[0] -eq '"' -and $value[-1] -eq '"') -or
             ($value[0] -eq "'" -and $value[-1] -eq "'"))) {
            $value = $value.Substring(1, $value.Length - 2)
        }
        $found = $value
    }

    if ([string]::IsNullOrEmpty($found)) { return $null }
    return $found
}

function Get-TokenFingerprint {
    <#
    token 的 sha256 十六进制前 8 位。空值返回 EMPTY（不参与相等比较）。
    #>
    param([AllowNull()][string]$Token)

    if ([string]::IsNullOrEmpty($Token)) { return 'EMPTY' }

    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Token)
        $hash = $sha.ComputeHash($bytes)
        return (-join ($hash[0..3] | ForEach-Object { $_.ToString('x2') }))
    } finally {
        $sha.Dispose()
    }
}

function Test-ServiceTokenConsistency {
    <#
    按 Checks 比对多处 token 指纹。

    Checks 每项：@{ Name; File; Key; Severity }
      - Name     ：展示名（相对路径）
      - File     ：相对 ProjectRoot 的路径
      - Key      ：键名
      - Severity ：Base（基准，且只能有一个）/ Error（不一致即失败）/ Warning（仅提示）

    返回：@{ Ok; Errors; Warnings; Rows }
      Rows 每项：@{ Name; File; Key; Severity; Len; Sha8; Status }
      Status ∈ BASE / OK / MISMATCH / MISSING / SKIP
    #>
    param(
        [Parameter(Mandatory)][string]$ProjectRoot,
        [Parameter(Mandatory)][object[]]$Checks
    )

    $baseCheck = $Checks | Where-Object { $_.Severity -eq 'Base' } | Select-Object -First 1
    if ($null -eq $baseCheck) { throw 'Checks 中必须且只能有一个 Severity="Base" 的基准项。' }

    $rows = New-Object System.Collections.Generic.List[object]
    $errors = New-Object System.Collections.Generic.List[string]
    $warnings = New-Object System.Collections.Generic.List[string]

    $readToken = {
        param($check)
        $path = Join-Path $ProjectRoot $check.File
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            return @{ Exists = $false; Token = $null }
        }
        return @{ Exists = $true; Token = (Get-DotEnvValue -Path $path -Key $check.Key) }
    }

    $baseState = & $readToken $baseCheck
    $baseToken = $baseState.Token
    $baseLen = if ([string]::IsNullOrEmpty($baseToken)) { 0 } else { $baseToken.Length }
    $baseSha = Get-TokenFingerprint -Token $baseToken

    if (-not $baseState.Exists) {
        $warnings.Add("基准文件不存在，跳过全部比对：$($baseCheck.File)")
    } elseif ($baseLen -eq 0) {
        $warnings.Add("基准 $($baseCheck.Name) 的 $($baseCheck.Key) 为空：5000 将跳过入站鉴权。")
    }

    foreach ($check in $Checks) {
        $state = & $readToken $check
        $token = $state.Token
        $len = if ([string]::IsNullOrEmpty($token)) { 0 } else { $token.Length }
        $sha8 = Get-TokenFingerprint -Token $token

        $status = 'OK'
        if (-not $state.Exists) {
            $status = 'MISSING'
            if ($check.Severity -ne 'Base') {
                $warnings.Add("文件不存在，跳过比对：$($check.File)")
            }
        } elseif ($check.Severity -eq 'Base') {
            $status = 'BASE'
        } elseif (-not $baseState.Exists) {
            $status = 'SKIP'
        } elseif ($sha8 -ne $baseSha) {
            $status = 'MISMATCH'
            $message = "token 不一致：$($check.Name)（len=$len, sha8=$sha8）≠ 基准 $($baseCheck.Name)（len=$baseLen, sha8=$baseSha）。"
            if ($check.Severity -eq 'Warning') {
                $warnings.Add($message + '仅警告：不影响本机 dev 启动，但生产构建会 401。')
            } else {
                if ($check.Name -like 'frontend/*') {
                    $errors.Add($message + '改完必须重启前端 3000（Vite 只在启动期注入 VITE_SERVICE_TOKEN）。')
                } elseif ($check.Name -like 'RAG-Knowledge-System/*') {
                    $errors.Add($message + '改完必须重启 5000 与 8002。')
                } else {
                    $errors.Add($message + '改完必须重启相关服务。')
                }
            }
        }

        $rows.Add([pscustomobject]@{
            Name     = $check.Name
            File     = $check.File
            Key      = $check.Key
            Severity = $check.Severity
            Len      = $len
            Sha8     = $sha8
            Status   = $status
        })
    }

    return [pscustomobject]@{
        Ok       = ($errors.Count -eq 0)
        Errors   = $errors.ToArray()
        Warnings = $warnings.ToArray()
        Rows     = $rows.ToArray()
    }
}

function Format-CredentialReport {
    <#
    把 Test-ServiceTokenConsistency 的结果渲染成文本行（调用方负责打印）。
    只包含长度与 sha256 前 8 位，不含任何 token 原值。
    #>
    param([Parameter(Mandatory)]$Result)

    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add('凭证一致性检查（只比 sha256 前 8 位，不打印原值）')
    foreach ($row in $Result.Rows) {
        $lines.Add(('  {0,-34} {1,-18} len={2,-3} sha8={3}  {4}' -f $row.Name, $row.Key, $row.Len, $row.Sha8, $row.Status))
    }
    foreach ($warning in $Result.Warnings) { $lines.Add("  [WARN] $warning") }
    foreach ($errorText in $Result.Errors) { $lines.Add("  [ERROR] $errorText") }
    return $lines.ToArray()
}
