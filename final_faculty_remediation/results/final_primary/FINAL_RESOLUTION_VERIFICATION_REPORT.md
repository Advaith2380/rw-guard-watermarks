# RW-GUARD — FINAL MULTI-RESOLUTION METRICS VERIFICATION REPORT
## Independent Recalculation and Raw Array Audit against Frozen Checkpoint

**Authoritative Prediction Array:** `results/final_primary/resolution_predictions.npz`  
**Evaluated Checkpoint:** `checkpoints/final/rwguard_final_7scheme.pt` (`37680cdd2d4e5100cbb8aa1642e78b9bb3df373e79efd9f8512f89e15d0c0573`)  
**Operating Threshold:** $\tau = 1.3394016$ (Frozen validation threshold)  
**Overall Status:** **FULLY VERIFIED (100% MATCH)**  

---

## 1. Executive Summary and Reconciliation of Discrepant Tables

During faculty audit, two conflicting resolution tables were noted in previous working narratives:
- **Table 1 (Raw Recomputation from `resolution_predictions.npz`):**  
  128px (AUC 0.8463, TPR 32.60%, FPR 6.67%), 256px (AUC 0.8543, TPR 18.67%, FPR 3.33%), 384px (AUC 0.8579, TPR 8.87%, FPR 1.13%), 512px (AUC 0.8501, TPR 9.47%, FPR 1.13%), 1024px (AUC 0.7998, TPR 18.50%, FPR 1.50%).
- **Table 2 (Conflicting Summary Draft):**  
  Listed 128px at 17.20%/3.40%, 384px at 17.93%/2.87%, 512px at 18.47%/3.00%.

### Forensic Resolution Finding:
1. **Source of Truth:** Table 1 reflects the **exact, reproducible, empirical evaluation** of the frozen primary model at the frozen validation threshold $\tau = 1.3394016$. Every integer count (TP, FP, TN, FN) directly sums to the total sample count.
2. **Manuscript Alignment:** Table 7 of `manuscript/corrected_final_manuscript.docx` **already contains Table 1** (`0.326 / 0.067` for 128px, `0.187 / 0.033` for 256px, `0.089 / 0.011` for 384px, `0.095 / 0.011` for 512px, `0.185 / 0.015` for 1024px).
3. **Origin of Table 2:** Table 2 was a draft working estimate where TPRs had been approximated around a target 3% FPR level rather than applying the fixed threshold $\tau = 1.3394016$. Table 1 is officially declared the single authoritative ground truth.

---

## 2. Authoritative Multi-Resolution Verification Matrix

| Resolution | Unique Sources | Total Samples ($N$) | Pos / Neg | TP | FP | TN | FN | ROC-AUC | 95% Bootstrap CI | Fixed TPR ($\tau$) | Fixed FPR ($\tau$) | ROC TPR @ 1% FPR | ROC Threshold | Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **128px** | 1,500 | 3,000 | 1500 / 1500 | 489 | 100 | 1400 | 1011 | **0.8463** | [0.8336, 0.8597] | **32.60%** | **6.67%** | 6.93% | 1.8887 | **VERIFIED_EXACT** |
| **256px** | 1,500 | 3,000 | 1500 / 1500 | 280 | 50 | 1450 | 1220 | **0.8543** | [0.8408, 0.8674] | **18.67%** | **3.33%** | 7.87% | 1.6040 | **VERIFIED_EXACT** |
| **384px** | 1,500 | 3,000 | 1500 / 1500 | 133 | 17 | 1483 | 1367 | **0.8579** | [0.8454, 0.8707] | **8.87%** | **1.13%** | 8.33% | 1.3556 | **VERIFIED_EXACT** |
| **512px** | 1,500 | 3,000 | 1500 / 1500 | 142 | 17 | 1483 | 1358 | **0.8501** | [0.8371, 0.8626] | **9.47%** | **1.13%** | 9.27% | 1.3489 | **VERIFIED_EXACT** |
| **1024px** | 200 | 400 | 200 / 200 | 37 | 3 | 197 | 163 | **0.7998** | [0.7575, 0.8407] | **18.50%** | **1.50%** | 16.50% | 1.4064 | **VERIFIED_EXACT** |

---

## 3. High-Resolution (1024px) Sampling Boundary Disclosure

- **Sample Size Constraint:** 1024px evaluation is performed on 200 held-out COCO source images (400 samples: 200 re-watermarked positive, 200 single-watermarked negative) due to high-resolution GPU VRAM memory ceilings, whereas 128px–512px evaluate 1,500 sources (3,000 samples).
- **Confusion Counts:** $\text{TP} = 37$, $\text{FP} = 3$, $\text{TN} = 197$, $\text{FN} = 163$.
- **Exact Fixed Rates:** $\text{Fixed TPR} = 37 / 200 = 18.50\%$, $\text{Fixed FPR} = 3 / 200 = 1.50\%$.
- **ROC Operating Point @ 1% FPR:** With $N_{\text{neg}} = 200$, 1.0% FPR admits at most $\lfloor 200 \times 0.01 \rfloor = 2$ False Positives. At $\tau = 1.4064$, False Positives = 2 (1.00% FPR) and True Positives = 33 / 200 $\to$ **ROC TPR@1% FPR = 16.50%**.
- **ROC-AUC:** **0.799825** ($95\%\text{ CI: } [0.7575, 0.8407]$). Matches manuscript Table 7 Row 14 (`0.800`).

---

## 4. Verification Conclusion

All five resolution conditions are directly reproduced from the archived raw predictions and agree with manuscript Table 7. Blocker C is completely resolved.
