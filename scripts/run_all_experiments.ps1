# Run All Experiments PowerShell Wrapper (REQ-Y)
# Executes the full scientific suite for RW-Guard Stage 2 audit and validation.

param(
    [string]$PythonPath = "D:\projects\rewm-guard\.venv\Scripts\python.exe",
    [string]$DataDir = "D:/projects/rewm-guard/data/coco",
    [string]$CheckpointPath = "D:/projects/rewm-guard/runs/baseline_e9/best.pt",
    [switch]$Smoke,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   RW-GUARD: STAGE 2 MASTER EXPERIMENTAL VALIDATION" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Python: $PythonPath"
Write-Host "Data:   $DataDir"
Write-Host "Model:  $CheckpointPath"
Write-Host "Smoke:  $Smoke"
Write-Host ""

if (-not (Test-Path $PythonPath)) {
    Write-Error "Python executable not found at: $PythonPath"
    exit 1
}

$cmdArgs = @("scripts/orchestrate.py", "--python", $PythonPath, "--data", $DataDir, "--ckpt", $CheckpointPath)
if ($Smoke) {
    $cmdArgs += "--smoke"
}
if ($SkipTests) {
    $cmdArgs += "--skip-tests"
}

Write-Host "Executing orchestrator: & $PythonPath $cmdArgs" -ForegroundColor Yellow
$sw = [System.Diagnostics.Stopwatch]::StartNew()

& $PythonPath $cmdArgs

if ($LASTEXITCODE -ne 0) {
    Write-Error "Master orchestrator exited with code $LASTEXITCODE"
    exit $LASTEXITCODE
}

$sw.Stop()
Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host " All experiments successfully executed in $($sw.Elapsed.TotalSeconds.ToString('F1'))s" -ForegroundColor Green
Write-Host " Results and manifests written to audit/" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
