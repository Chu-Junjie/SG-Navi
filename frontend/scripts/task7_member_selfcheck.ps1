# Task 7 / member-owned Windows independent environment verification.
# YOU must execute this in a brand-new git clone; this is not a CI attestation.
# From a new parent directory:
#   git clone https://github.com/Chu-Junjie/SG-Navi.git SG-Navi-task7-clean
#   cd SG-Navi-task7-clean
#   powershell -NoProfile -ExecutionPolicy Bypass -File .\frontend\scripts\task7_member_selfcheck.ps1
param([switch]$SkipBrowser)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $repo
$date = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
$dir = Join-Path $repo ('instance\task7-selfcheck-' + $date)
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$transcript = Join-Path $dir 'actual-terminal-log.txt'
Start-Transcript -Path $transcript -Force | Out-Null
$results = New-Object System.Collections.Generic.List[object]
$python = Join-Path $repo '.venv\Scripts\python.exe'
$server = $null

function Run-Stage {
  param([string]$Name,[scriptblock]$Work)
  Write-Host ''
  Write-Host ('=== ' + $Name + ' ===')
  $exitCode = 0
  try {
    $global:LASTEXITCODE = 0
    & $Work
    if ($LASTEXITCODE -ne 0) { $exitCode = [int]$LASTEXITCODE }
  } catch {
    Write-Host ('ERROR: ' + $_.Exception.Message)
    $exitCode = 1
  }
  $outcome = if ($exitCode -eq 0) { 'PASS' } else { 'FAIL' }
  $results.Add([pscustomobject]@{ step=$Name; status=$outcome; exit_code=$exitCode }) | Out-Null
  Write-Host ($Name + ': ' + $outcome + ' (exit=' + $exitCode + ')')
  return ($exitCode -eq 0)
}
function Not-Run {
  param([string]$Name,[string]$Reason)
  $results.Add([pscustomobject]@{ step=$Name; status='NOT RUN'; reason=$Reason }) | Out-Null
  Write-Host ($Name + ': NOT RUN (' + $Reason + ')')
}
$metadata = [ordered]@{ date_utc=(Get-Date).ToUniversalTime().ToString('o'); clone_directory=$repo; sha='NOT RUN'; python='NOT RUN'; node='NOT RUN' }
try {
  $ok = Run-Stage 'git and tool versions' {
    $metadata.sha = (git rev-parse HEAD).Trim()
    Write-Host ('Exact SHA: ' + $metadata.sha)
    git status --short
    git --version
    $metadata.python = (py --version | Out-String).Trim()
    Write-Host $metadata.python
    $metadata.node = (node --version | Out-String).Trim()
    Write-Host $metadata.node
  }
  if (-not $ok) { throw 'Git/tool setup failed' }
  if (Test-Path $python) { throw 'Existing .venv detected: clone into a truly NEW directory instead' }
  $ok = Run-Stage 'create fresh isolated virtual environment' { py -m venv .venv }
  if (-not $ok -or -not (Test-Path $python)) { throw 'Fresh .venv creation failed' }
  $ok = Run-Stage 'install all requirements and capture pip freeze' {
    & $python -m pip install -r tests/contracts/requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'pip installation failed' }
    & $python -m pip freeze
  }
  if (-not $ok) { throw 'Requirements installation failed' }
  Run-Stage 'validate shared contract' { & $python -m shared.validate_contracts }
  Run-Stage 'import knowledge base' { & $python -m rag.import_knowledge_base }
  Run-Stage 'backend RAG real integration checks' { & $python -m integration.checks }
  Run-Stage 'full pytest: record the actual PASS FAIL SKIP summary' {
    & $python -X utf8 -m pytest tests/contracts tests/backend frontend/tests tests/rag tests/integration -q
  }
  $started = Run-Stage 'local Flask start and health' {
    $stdout = Join-Path $dir 'flask-stdout.txt'
    $stderr = Join-Path $dir 'flask-stderr.txt'
    $server = Start-Process -FilePath $python -ArgumentList @(
      '-m','flask','--app','integration.app','run','--host','127.0.0.1','--port','5055'
    ) -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru -WindowStyle Hidden
    $healthy = $false
    for($i=0;$i -lt 35;$i++){
      Start-Sleep -Seconds 1
      try {
        $body = Invoke-RestMethod -Uri 'http://127.0.0.1:5055/api/health' -TimeoutSec 3
        if ($body.status -eq 'ok') { $healthy=$true; break }
      } catch {}
      if ($server.HasExited) { break }
    }
    if (-not $healthy) { throw 'Flask health not ready after actual startup attempt' }
    Write-Host ('Flask PID: ' + $server.Id)
  }
  if ($started) {
    Run-Stage 'local health/version/form HTTP GET' {
      Invoke-RestMethod 'http://127.0.0.1:5055/api/health' | ConvertTo-Json
      Invoke-RestMethod 'http://127.0.0.1:5055/api/version' | ConvertTo-Json
      $resp=Invoke-WebRequest 'http://127.0.0.1:5055/task5-flow.html' -UseBasicParsing
      if ($resp.StatusCode -ne 200) { throw 'form did not return HTTP 200' }
      Write-Host 'Form HTTP 200'
    }
    if ($SkipBrowser) {
      Not-Run 'local Chromium diagnostic' 'operator chose SkipBrowser'
    } else {
      Run-Stage 'local Chromium browser diagnostic' { node integration/browser_check.mjs http://127.0.0.1:5055 }
    }
  } else {
    Not-Run 'local health/version/form HTTP GET' 'Flask startup failed'
    Not-Run 'local Chromium diagnostic' 'Flask startup failed'
  }
} catch {
  Write-Host ('SETUP STOPPED: ' + $_.Exception.Message)
  $results.Add([pscustomobject]@{step='setup termination';status='FAIL';exit_code=1}) | Out-Null
} finally {
  if ($null -ne $server) {
    try { Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue } catch {}
  }
  $summary = [ordered]@{
    environment=$metadata
    stage_results=@($results)
    passed=@($results | Where-Object { $_.status -eq 'PASS' }).Count
    failed=@($results | Where-Object { $_.status -eq 'FAIL' }).Count
    not_run=@($results | Where-Object { $_.status -eq 'NOT RUN' }).Count
    note='Stage counts are distinct from pytest individual test results; read the actual transcript.'
  }
  $summary | ConvertTo-Json -Depth 6 | Out-File (Join-Path $dir 'actual-results.json') -Encoding utf8
  Write-Host ('Stage summary: PASS=' + $summary.passed + ', FAIL=' + $summary.failed + ', NOT RUN=' + $summary.not_run)
  Write-Host ('Evidence saved: ' + $dir)
  Write-Host 'Submit actual terminal log and JSON only after reviewing them. This is your own personal test, not CI.'
  Stop-Transcript | Out-Null
}
