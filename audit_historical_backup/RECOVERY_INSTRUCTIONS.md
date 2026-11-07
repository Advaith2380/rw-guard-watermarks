# Recovery and Rollback Instructions: RW-Guard

## Checkpoint Details
- **Checkpoint ID:** `recovery-checkpoint-17a54fc-20261031`
- **Base Commit:** `17a54fc` (`origin/main`)
- **Backup Location:** `_recovery_checkpoint_17a54fc/`
- **Creation Timestamp:** 2026-10-31T22:46:00+05:30

## Safety Guarantees
- Original datasets in `D:/projects/rewm-guard/data` are untouched and preserved.
- Original checkpoints in `D:/projects/rewm-guard/runs` are untouched and preserved.
- Original evaluation results in `D:/projects/rewm-guard/results` are untouched and preserved.
- Rollback will NOT delete original checkpoints or datasets.

## How to Roll Back
To roll back the project files to the verified pre-Stage 2 state:
```powershell
.\scripts\RWGUARD_ROLLBACK.ps1 -ConfirmRollback
```

### Safety Features of Rollback Script
1. Requires explicit `-ConfirmRollback` parameter.
2. Checks that `_recovery_checkpoint_17a54fc` exists and contains files.
3. Automatically creates a pre-rollback emergency snapshot before restoring.
4. Restores all original code and configuration files.
5. Reports exactly which files were restored.
