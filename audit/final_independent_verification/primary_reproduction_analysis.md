# PRIMARY MODEL EVALUATION REPRODUCTION REPORT
**Checkpoint:** `checkpoints/final/rwguard_final_7scheme.pt`  
**Frozen Decision Threshold:** `tau = 1.339402` (nominal 1.0% val FPR)  
**Evaluation Corpus:** MS-COCO Test Split (1500 source images, 3000 derived samples)  

---
## 1. Reproduction Reconciliation Matrix
| Metric | Reported Reference | Reproduced Value | 95% Bootstrap CI | Absolute Difference | Status |
|---|---:|---:|---:|---:|:---:|
| Test Sources | 1,500 | 1500 | — | 0 | EXACT |
| Test Samples | 3,000 | 3000 | — | 0 | EXACT |
| ROC-AUC | 0.8543 | 0.8543 | [0.8408, 0.8674] | 0.00003 | PASS |
| TPR@1%FPR (Test ROC) | 0.0787 | 0.0787 | [0.0500, 0.1060] | 0.00003 | PASS |
| Fixed-Threshold TPR | 0.1867 | 0.1867 | [0.1680, 0.2067] | 0.00003 | PASS |
| Fixed-Threshold FPR | 0.0333 | 0.0333 | [0.0247, 0.0433] | 0.00003 | PASS |

## 2. Dataset Split Isolation
- Train sources: 3000
- Val sources: 500
- Test sources: 1500
- Cross-split overlap: 0 (Strict source-level isolation verified: True)

## 3. Confusion Matrix at Operating Threshold (tau = 1.3394)
- True Positives:  280 (Sensitivity: 18.67%)
- False Positives: 50 (Fall-out FPR: 3.33%)
- True Negatives:  1450 (Specificity: 96.67%)
- False Negatives: 1220

## 4. Key Takeaways
1. The primary 7-scheme model reproduces headline ROC-AUC of 0.8543 within 0.0001 numerical precision.
2. The threshold is strictly frozen at tau = 1.3394016 and achieves exactly 18.67% test TPR at 3.33% test FPR.
3. All 3,000 per-sample prediction logits and binary decisions are serialized to CSV for full third-party auditability.
