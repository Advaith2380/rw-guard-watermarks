[CmdletBinding()]
param (
    [switch]$ConfirmRollback
)

$CheckpointId = "recovery-checkpoint-17a54fc-20261031"
$BackupDir = "_recovery_checkpoint_17a54fc"
$ManifestPath = "audit/recovery_manifest.json"

Write-Host "================================================="
Write-Host " RW-GUARD EMERGENCY RECOVERY / ROLLBACK UTILITY"
Write-Host "================================================="
Write-Host "Target Checkpoint: $CheckpointId"
Write-Host "Source Backup:     $BackupDir"

if (-not $ConfirmRollback) {
    Write-Warning "Rollback aborted: You must supply -ConfirmRollback to execute restoration."
    Write-Host "Usage: .\scripts\RWGUARD_ROLLBACK.ps1 -ConfirmRollback"
    exit 1
}

if (-not (Test-Path $BackupDir)) {
    Write-Error "CRITICAL: Backup directory '$BackupDir' was not found! Aborting rollback."
    exit 2
}

if (-not (Test-Path $ManifestPath)) {
    Write-Warning "Manifest '$ManifestPath' not found. Proceeding with backup directory files..."
}

# Create a safety pre-rollback snapshot of current working tree
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$PreRollbackDir = "_pre_rollback_snapshot_$Timestamp"
Write-Host "Creating safety snapshot of current state to '$PreRollbackDir'..."
New-Item -ItemType Directory -Path $PreRollbackDir -Force | Out-Null
Copy-Item -Path "rewm", "train.py", "evaluate.py" -Destination $PreRollbackDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Restoring files from recovery checkpoint..."
$RestoredCount = 0
$Items = Get-ChildItem -Path $BackupDir
foreach ($item in $Items) {
    Copy-Item -Path $item.FullName -Destination "." -Recurse -Force
    Write-Host " - Restored: $($item.Name)"
    $RestoredCount++
}

Write-Host "================================================="
Write-Host "Rollback complete. Restored $RestoredCount items from $BackupDir."
Write-Host "Pre-rollback files saved in $PreRollbackDir."
Write-Host "================================================="
