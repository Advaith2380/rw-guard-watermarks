# EXPERIMENT_READINESS.md: Live Execution Matrix

Date: 2026-10-31
Auditor: Lead Research & Systems Auditor

| Experiment / Task | Classification | Live Readiness Status | Compute Mode | Path to Execution |
|---|---|---|---|---|
| **Smoke Test** (`sanity_check.py`) | Ready | **READY** | CPU | `python sanity_check.py --data D:/projects/rewm-guard/data/coco` |
| **Statistical Analysis** (`bootstrap_ci.py`) | Ready | **READY** | CPU | Compute 95% CIs on existing `results.json` files |
| **Shortcut Baselines** (`shortcut_baseline.py`) | Ready | **READY** | CPU | Logistic regression on residual energy & frequency features |
| **Attack-Outcome Stratification** (`rewm/outcomes.py`) | Ready | **READY** | CPU | Classify overwritten vs dual-survival vs failed-attack via bit accuracy |
| **Distortion-Matched Controls** (`matched_controls.py`) | Ready | **READY** | CPU/GPU | Match single-watermark residual energy to double-watermark |
| **Unit & Integration Tests** (`tests/`) | Ready | **READY** | CPU | Pytest / unittest covering metrics, watermarks, outcomes, RNG |
| **Config/Manifest Capture** | Ready | **READY** | CPU | Output git commit, env specs, and split manifests |
| **Protocol Scheme-Set Versioning** (`scheme_sets.json`) | Ready | **READY** | CPU | Version `v1_four` and `v2_seven` protocols |
| **Multi-Restart Adversarial PGD** | Ready | **READY** | GPU | Extend PGD in `rewm/engine.py` with multi-restart support |
| **StegaStamp Integration / Test** | Ready with Limitations | **READY_WITH_LIMITATIONS** | CPU/GPU | Pretrained ONNX model weight download; test script |
| **Primary Pipeline Retraining** | Ready | **READY** | GPU (GTX 1650) | Fast 1-epoch / smoke & full validation passes |
| **SRNet / ZhuNet / SiaStegNet Baselines** | Stretch Goal | **BLOCKED_COMPLEXITY** | GPU | High complexity steganalysis network architectures; adapt if timeline permits |
| **PowerShell Experiment Orchestration** | Ready | **READY** | CPU | Automated end-to-end experiment pipeline runner |
