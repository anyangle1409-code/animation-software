param(
  [string]$SessionUrl = "https://claude.ai/code/session_01EPKohHG29Xe8qKuNMT5Fv9",
  [string]$PromptFile = "$PSScriptRoot\CLAUDE_AUTO_RESUME_PROMPT.txt",
  [int]$RetryMinutes = 5,
  [int]$MaxHours = 3
)

$ErrorActionPreference = "Continue"
$logDir = Join-Path $PSScriptRoot "..\ORIGINAL_V1_WORK\anatomy\automation"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir "claude_auto_resume.log"

function Write-Log([string]$Message) {
  $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz') $Message"
  Add-Content -Path $log -Value $line
}

if (-not (Test-Path $PromptFile)) {
  Write-Log "ERROR prompt file missing: $PromptFile"
  exit 2
}
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
  Write-Log "ERROR claude CLI not found in PATH"
  exit 3
}

$prompt = Get-Content -Raw -Path $PromptFile
$deadline = (Get-Date).AddHours($MaxHours)
Write-Log "Watcher started; retry every $RetryMinutes minutes for up to $MaxHours hours"

while ((Get-Date) -lt $deadline) {
  $out = & claude --cloud $SessionUrl -p $prompt 2>&1 | Out-String
  $code = $LASTEXITCODE
  $flat = ($out -replace "\r?\n"," ").Trim()

  if ($code -eq 0) {
    Write-Log "SUCCESS continuation prompt queued. $flat"
    exit 0
  }

  if ($flat -match "(?i)(usage|rate.?limit|limit.*reset|reset.*limit|capacity|quota)") {
    Write-Log "WAIT usage unavailable; retrying"
  } else {
    Write-Log "WARN exit $code: $flat"
  }

  Start-Sleep -Seconds ($RetryMinutes * 60)
}

Write-Log "TIMEOUT without successful queue"
exit 4
