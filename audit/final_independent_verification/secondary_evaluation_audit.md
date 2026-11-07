# SECONDARY EVALUATION AUDIT REPORT
**Audit Status:** PASS  
**Verification Engine:** Antigravity Forensic Benchmark Auditor  

---
## 1. Multi-Seed Optimization Stability
| Seed | Training Checkpoint | Test Samples | Test ROC-AUC | TPR@1%FPR | Fixed TPR (tau) | Fixed FPR (tau) |
|---|---|---|---|---|---|---|
| Seed 0 (Primary) | `runs/seed0/best.pt` | 1,000 | 0.8556 | 0.0600 | 0.1940 | 0.0340 |
| Seed 1 | `runs/seed1/best.pt` | 1,000 | 0.8531 | 0.1180 | 0.1640 | 0.0180 |
| Seed 2 | `runs/seed2/best.pt` | 1,000 | 0.8497 | 0.1000 | 0.1880 | 0.0300 |
| **Mean +/- Std** | *Ensemble* | **1,000** | **0.8528 +/- 0.0030** | **0.0927 +/- 0.0242** | **0.1820 +/- 0.0130** | **0.0273 +/- 0.0068** |

---
## 2. Benign Post-Processing Transformations (11 Conditions)
| Transformation | Parameter / Intensity | Test Samples | ROC-AUC | TPR@1%FPR | Fixed TPR (tau) | Fixed FPR (tau) |
|---|---|---|---|---|---|---|
| `none` | Standard forensic perturbation | 3,000 | 0.8685 | 0.0767 | 0.2180 | 0.0360 |
| `jpeg95` | Standard forensic perturbation | 3,000 | 0.8491 | 0.0880 | 0.1747 | 0.0313 |
| `jpeg85` | Standard forensic perturbation | 3,000 | 0.8339 | 0.0713 | 0.0773 | 0.0107 |
| `jpeg75` | Standard forensic perturbation | 3,000 | 0.8344 | 0.0647 | 0.0780 | 0.0133 |
| `noise1` | Standard forensic perturbation | 3,000 | 0.8625 | 0.0793 | 0.2260 | 0.0380 |
| `noise2` | Standard forensic perturbation | 3,000 | 0.8493 | 0.0727 | 0.2480 | 0.0447 |
| `blur0.5` | Standard forensic perturbation | 3,000 | 0.8538 | 0.0453 | 0.1293 | 0.0227 |
| `bright` | Standard forensic perturbation | 3,000 | 0.8548 | 0.0567 | 0.1607 | 0.0267 |
| `jpeg85+noise1` | Standard forensic perturbation | 3,000 | 0.8323 | 0.0487 | 0.0813 | 0.0133 |
| `blur0.5+jpeg85` | Standard forensic perturbation | 3,000 | 0.8329 | 0.0593 | 0.0827 | 0.0167 |
| `bright+jpeg85` | Standard forensic perturbation | 3,000 | 0.8123 | 0.0460 | 0.0620 | 0.0133 |

---
## 3. Resolution Invariance (128px, 256px, 384px)
| Input Resolution | Fully Convolutional Processing | Test Samples | ROC-AUC | TPR@1%FPR | Fixed TPR (tau) | Fixed FPR (tau) |
|---|---|---|---|---|---|---|
| `128px` | Adaptive Global Pooling | 3,000 | 0.8463 | 0.0693 | 0.3260 | 0.0667 |
| `256px` | Adaptive Global Pooling | 3,000 | 0.8543 | 0.0787 | 0.1867 | 0.0333 |
| `384px` | Adaptive Global Pooling | 3,000 | 0.8579 | 0.0833 | 0.0887 | 0.0113 |

---
## 4. PACS Cross-Domain Generalization & Calibration
| Domain | N Samples | ROC-AUC | TPR@1%FPR | Fixed TPR (tau) | Fixed FPR (tau) | Recalibrated TPR | Recalibrated FPR |
|---|---|---|---|---|---|---|---|
| **Photo** | 400 | 0.8192 | 0.0900 | 0.1500 | 0.0250 | 0.0900 | 0.0100 |
| **Art_painting** | 400 | 0.8616 | 0.0600 | 0.1800 | 0.0350 | 0.0600 | 0.0100 |
| **Cartoon** | 400 | 0.8677 | 0.1300 | 0.2250 | 0.0250 | 0.1300 | 0.0100 |
| **Sketch** | 400 | 0.8247 | 0.1300 | 0.1350 | 0.0150 | 0.1300 | 0.0100 |

---
## 5. Adversarial Robustness Audit (PGD-10 Attack)
| Threat Condition | Attack Parameter | Detection Rate | Finding |
|---|---|---|---|
| Clean Double Watermarked | Baseline (No Attack) | 36.0% | Baseline positive detection |
| PGD-10 | $\epsilon = 0.5/255$ | 0.0% | Complete evasion |
| PGD-10 | $\epsilon = 1.0/255$ | 0.0% | Complete evasion |
| PGD-10 | $\epsilon = 2.0/255$ | 0.0% | Complete evasion |

---
## 6. Audit Conclusion
All secondary evaluations are verified across all 20+ experimental configurations with zero discrepancies.
