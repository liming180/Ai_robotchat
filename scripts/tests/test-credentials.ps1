<#
回归用例：scripts/lib/credentials.ps1（P2-5 动作 1 的凭证一致性校验）。

用临时目录构造假 .env，不触碰真实配置。覆盖：
  1) 三处一致                     → 通过
  2) 前端 dev 漂移                → 错误（2026-11-24 故障形态）
  3) RAG 漂移                     → 错误
  4) .env.production 漂移         → 仅警告
  5) 基准为空 + RAG 非空          → 错误
  6) 前端缺键                     → 错误
  7) .env 解析鲁棒性（BOM/CRLF/export/引号/注释/重复键）
  8) 报告不泄漏明文 token

执行：powershell -NoProfile -File scripts/tests/test-credentials.ps1
#>
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:PassCount = 0
$script:FailCount = 0

. (Join-Path (Split-Path -Parent $PSScriptRoot) 'lib\credentials.ps1')

function Assert-True {
    param([bool]$Condition, [string]$Name)
    if ($Condition) {
        $script:PassCount++
        Write-Host "  PASS  $Name" -ForegroundColor Green
    } else {
        $script:FailCount++
        Write-Host "  FAIL  $Name" -ForegroundColor Red
    }
}

function Assert-Equal {
    param($Expected, $Actual, [string]$Name)
    $ok = ("$Expected" -eq "$Actual")
    if ($ok) {
        Assert-True $true $Name
    } else {
        Assert-True $false "$Name（期望=$Expected，实际=$Actual）"
    }
}

function Assert-Contains {
    param($Collection, [string]$Needle, [string]$Name)
    $hit = @($Collection | Where-Object { "$_" -like "*$Needle*" }).Count -gt 0
    if (-not $hit) { $Name = "$Name（未找到：$Needle）" }
    Assert-True $hit $Name
}

$script:TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "credtest-$PID"

function New-CaseRoot {
    param([string]$Name)
    $root = Join-Path $script:TempRoot $Name
    foreach ($dir in @('backend', 'frontend', 'RAG-Knowledge-System\backend')) {
        New-Item -ItemType Directory -Path (Join-Path $root $dir) -Force | Out-Null
    }
    return $root
}

function Write-EnvFile {
    param([string]$Root, [string]$Relative, [string]$Content)
    $path = Join-Path $Root $Relative
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($path, $Content, $utf8NoBom)
}

function New-Checks {
    return @(
        [pscustomobject]@{ Name = 'backend/.env'; File = 'backend/.env'; Key = 'SERVICE_TOKEN'; Severity = 'Base' },
        [pscustomobject]@{ Name = 'frontend/.env.development'; File = 'frontend/.env.development'; Key = 'VITE_SERVICE_TOKEN'; Severity = 'Error' },
        [pscustomobject]@{ Name = 'frontend/.env.production'; File = 'frontend/.env.production'; Key = 'VITE_SERVICE_TOKEN'; Severity = 'Warning' },
        [pscustomobject]@{ Name = 'RAG-Knowledge-System/backend/.env'; File = 'RAG-Knowledge-System/backend/.env'; Key = 'SERVICE_TOKEN'; Severity = 'Error' }
    )
}

function Get-Row {
    param($Result, [string]$Name)
    return ($Result.Rows | Where-Object { $_.Name -eq $Name } | Select-Object -First 1)
}

try {
    New-Item -ItemType Directory -Path $script:TempRoot -Force | Out-Null

    # ---------- 用例 1：三处一致 ----------
    Write-Host '用例 1：三处 token 一致 → 通过' -ForegroundColor Cyan
    $root = New-CaseRoot 'ok'
    $same = 'token-consistent-0123456789abcdef'
    Write-EnvFile $root 'backend\.env' "SERVICE_TOKEN=$same"
    Write-EnvFile $root 'frontend\.env.development' "VITE_SERVICE_TOKEN=$same"
    Write-EnvFile $root 'frontend\.env.production' "VITE_SERVICE_TOKEN=$same"
    Write-EnvFile $root 'RAG-Knowledge-System\backend\.env' "SERVICE_TOKEN=$same"
    $result = Test-ServiceTokenConsistency -ProjectRoot $root -Checks (New-Checks)
    Assert-True $result.Ok 'Ok=true'
    Assert-Equal 0 $result.Errors.Count 'Errors 为空'
    Assert-Equal 'BASE' (Get-Row $result 'backend/.env').Status '基准行状态 BASE'
    foreach ($name in @('frontend/.env.development', 'frontend/.env.production', 'RAG-Knowledge-System/backend/.env')) {
        Assert-Equal 'OK' (Get-Row $result $name).Status "$name 状态 OK"
    }

    # ---------- 用例 2：前端 dev 漂移 ----------
    Write-Host '用例 2：frontend/.env.development 漂移 → 错误' -ForegroundColor Cyan
    $root = New-CaseRoot 'dev-drift'
    $devToken = 'token-short-14'
    Write-EnvFile $root 'backend\.env' "SERVICE_TOKEN=$same"
    Write-EnvFile $root 'frontend\.env.development' "VITE_SERVICE_TOKEN=$devToken"
    Write-EnvFile $root 'frontend\.env.production' "VITE_SERVICE_TOKEN=$same"
    Write-EnvFile $root 'RAG-Knowledge-System\backend\.env' "SERVICE_TOKEN=$same"
    $result = Test-ServiceTokenConsistency -ProjectRoot $root -Checks (New-Checks)
    Assert-True (-not $result.Ok) 'Ok=false'
    Assert-Equal 1 $result.Errors.Count '只有 1 条错误'
    Assert-Contains $result.Errors 'frontend/.env.development' '错误信息带前端路径'
    Assert-Contains $result.Errors (Get-TokenFingerprint -Token $same) '错误信息带基准指纹'
    Assert-Contains $result.Errors (Get-TokenFingerprint -Token $devToken) '错误信息带漂移方指纹'
    Assert-Contains $result.Errors '重启前端 3000' '错误信息提示重启前端'
    Assert-Equal 'MISMATCH' (Get-Row $result 'frontend/.env.development').Status '前端 dev 行状态 MISMATCH'
    Assert-Equal 0 $result.Warnings.Count '生产文件一致时不产生警告'

    # ---------- 用例 3：RAG 漂移 ----------
    Write-Host '用例 3：RAG SERVICE_TOKEN 漂移 → 错误' -ForegroundColor Cyan
    $root = New-CaseRoot 'rag-drift'
    Write-EnvFile $root 'backend\.env' "SERVICE_TOKEN=$same"
    Write-EnvFile $root 'frontend\.env.development' "VITE_SERVICE_TOKEN=$same"
    Write-EnvFile $root 'frontend\.env.production' "VITE_SERVICE_TOKEN=$same"
    Write-EnvFile $root 'RAG-Knowledge-System\backend\.env' 'SERVICE_TOKEN=rag-different-token'
    $result = Test-ServiceTokenConsistency -ProjectRoot $root -Checks (New-Checks)
    Assert-True (-not $result.Ok) 'Ok=false'
    Assert-Equal 1 $result.Errors.Count '只有 1 条错误'
    Assert-Contains $result.Errors 'RAG-Knowledge-System/backend/.env' '错误信息带 RAG 路径'
    Assert-Contains $result.Errors '重启 5000 与 8002' '错误信息提示重启 5000/8002'

    # ---------- 用例 4：.env.production 漂移仅警告 ----------
    Write-Host '用例 4：.env.production 漂移 → 仅警告，不阻断' -ForegroundColor Cyan
    $root = New-CaseRoot 'prod-drift'
    Write-EnvFile $root 'backend\.env' "SERVICE_TOKEN=$same"
    Write-EnvFile $root 'frontend\.env.development' "VITE_SERVICE_TOKEN=$same"
    Write-EnvFile $root 'frontend\.env.production' 'VITE_SERVICE_TOKEN=prod-only-different'
    Write-EnvFile $root 'RAG-Knowledge-System\backend\.env' "SERVICE_TOKEN=$same"
    $result = Test-ServiceTokenConsistency -ProjectRoot $root -Checks (New-Checks)
    Assert-True $result.Ok 'Ok=true'
    Assert-Equal 0 $result.Errors.Count 'Errors 为空'
    Assert-Equal 1 $result.Warnings.Count '1 条警告'
    Assert-Contains $result.Warnings 'frontend/.env.production' '警告带生产文件路径'
    Assert-Contains $result.Warnings '仅警告' '警告明确不阻断'
    Assert-Equal 'MISMATCH' (Get-Row $result 'frontend/.env.production').Status '生产行状态 MISMATCH'

    # ---------- 用例 5：基准为空 + RAG 非空 ----------
    Write-Host '用例 5：基准 token 为空 + RAG 非空 → 错误' -ForegroundColor Cyan
    $root = New-CaseRoot 'empty-base'
    Write-EnvFile $root 'backend\.env' 'SERVICE_TOKEN='
    Write-EnvFile $root 'frontend\.env.development' 'VITE_SERVICE_TOKEN='
    Write-EnvFile $root 'frontend\.env.production' 'VITE_SERVICE_TOKEN='
    Write-EnvFile $root 'RAG-Knowledge-System\backend\.env' 'SERVICE_TOKEN=rag-non-empty'
    $result = Test-ServiceTokenConsistency -ProjectRoot $root -Checks (New-Checks)
    Assert-True (-not $result.Ok) 'Ok=false'
    Assert-Contains $result.Warnings '基准 backend/.env 的 SERVICE_TOKEN 为空' '警告基准为空'
    Assert-Equal 1 $result.Errors.Count '只有 1 条错误（RAG）'
    Assert-Contains $result.Errors 'RAG-Knowledge-System/backend/.env' '错误指向 RAG'
    Assert-Equal 0 (Get-Row $result 'backend/.env').Len '基准行长度为 0'
    Assert-Equal 'OK' (Get-Row $result 'frontend/.env.development').Status '前端同为空视为一致'

    # ---------- 用例 6：前端缺键 ----------
    Write-Host '用例 6：前端文件存在但缺键 → 错误' -ForegroundColor Cyan
    $root = New-CaseRoot 'missing-key'
    Write-EnvFile $root 'backend\.env' "SERVICE_TOKEN=$same"
    Write-EnvFile $root 'frontend\.env.development' 'VITE_API_BASE_URL=http://localhost:8081'
    Write-EnvFile $root 'frontend\.env.production' 'VITE_API_BASE_URL=http://localhost:8081'
    Write-EnvFile $root 'RAG-Knowledge-System\backend\.env' "SERVICE_TOKEN=$same"
    $result = Test-ServiceTokenConsistency -ProjectRoot $root -Checks (New-Checks)
    Assert-True (-not $result.Ok) 'Ok=false'
    Assert-Equal 1 $result.Errors.Count '只有 1 条错误（dev）'
    Assert-Equal 1 $result.Warnings.Count '1 条警告（prod 为 Warning 级）'
    Assert-Equal 0 (Get-Row $result 'frontend/.env.development').Len 'dev 行长度为 0'
    Assert-Equal 'MISMATCH' (Get-Row $result 'frontend/.env.development').Status 'dev 行状态 MISMATCH'

    # ---------- 用例 7：解析鲁棒性 ----------
    Write-Host '用例 7：.env 解析（BOM/CRLF/export/引号/注释/重复键）' -ForegroundColor Cyan
    $root = New-CaseRoot 'parse'
    $content = ([string][char]0xFEFF) +
        "# 注释行`r`nexport SERVICE_TOKEN = `"quoted-token`"`r`n" +
        "OTHER_KEY=1`r`n" +
        "SERVICE_TOKEN=last-wins-token`r`n"
    Write-EnvFile $root 'backend\.env' $content
    $value = Get-DotEnvValue -Path (Join-Path $root 'backend\.env') -Key 'SERVICE_TOKEN'
    Assert-Equal 'last-wins-token' $value 'BOM+CRLF+export+引号+重复键→取最后一行且去引号'
    $singleQuoted = Get-DotEnvValue -Path (Join-Path $root 'backend\.env') -Key 'OTHER_KEY'
    Assert-Equal '1' $singleQuoted '普通键解析正确'
    $absent = Get-DotEnvValue -Path (Join-Path $root 'backend\.env') -Key 'NO_SUCH_KEY'
    Assert-True ($null -eq $absent) '缺键返回 $null'
    $missingFile = Get-DotEnvValue -Path (Join-Path $root 'nope\.env') -Key 'SERVICE_TOKEN'
    Assert-True ($null -eq $missingFile) '文件不存在返回 $null'

    # ---------- 用例 8：报告不泄漏明文 ----------
    Write-Host '用例 8：格式化报告不泄漏明文 token' -ForegroundColor Cyan
    $root = New-CaseRoot 'leak'
    $canary = 'PLAINTEXT-CANARY-9Z'
    Write-EnvFile $root 'backend\.env' "SERVICE_TOKEN=$canary"
    Write-EnvFile $root 'frontend\.env.development' "VITE_SERVICE_TOKEN=$canary"
    Write-EnvFile $root 'frontend\.env.production' "VITE_SERVICE_TOKEN=other-canary-value"
    Write-EnvFile $root 'RAG-Knowledge-System\backend\.env' "SERVICE_TOKEN=$canary"
    $result = Test-ServiceTokenConsistency -ProjectRoot $root -Checks (New-Checks)
    $report = (Format-CredentialReport -Result $result) -join "`n"
    Assert-True (-not $report.Contains($canary)) '报告不含基准明文'
    Assert-True (-not $report.Contains('other-canary-value')) '报告不含漂移方明文'
    Assert-True ($report.Contains((Get-TokenFingerprint -Token $canary))) '报告含 sha8 指纹'
    Assert-True ($report.Contains('len=')) '报告含长度'
    Assert-True ($report.Contains('sha8=')) '报告含指纹字段名'
} finally {
    if (Test-Path -LiteralPath $script:TempRoot) {
        Remove-Item -LiteralPath $script:TempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host ''
Write-Host ("结果：{0} 通过，{1} 失败" -f $script:PassCount, $script:FailCount) -ForegroundColor $(if ($script:FailCount -eq 0) { 'Green' } else { 'Red' })
if ($script:FailCount -gt 0) { exit 1 }
exit 0
