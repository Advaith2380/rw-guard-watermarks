# Limitations, Threat Model & Scientific Scope

## 1. Formal Threat Model

The RW-Guard forensic detection framework operates under a clearly defined forensic threat model:

```
[Original Image I]
       |
       v  (Legitimate Victim Embedding: W_v, k_v, m_v)
[Singly-Watermarked Image I_v]  <--- (Negative Class: y = 0)
       |
       v  (Adversarial Re-Watermarking: W_a, k_a, m_a)
[Sequentially Re-Watermarked Image I_va] <--- (Positive Class: y = 1)
       |
       v  (Query Image X)
[RW-Guard / ForensicNet Detector]
       |
       v
[Scalar Logit z -> Decision: y_hat in {0, 1}]
```

### 1.1 Parties and Capabilities
1. **Victim (Content Creator / Publisher):**
   - Possesses original clean image $I$.
   - Selects legitimate watermark scheme $W_v \in \mathcal{W}$, secret key $k_v$, and payload $m_v$.
   - Generates singly-watermarked carrier $I_v = \text{Embed}(I, W_v, k_v, m_v)$.
2. **Adversary (Re-Watermarking Attacker):**
   - Intercepts or acquires public watermarked carrier $I_v$.
   - Possesses **no access** to victim key $k_v$, victim scheme identity $W_v$, or clean source $I$.
   - Applies secondary embedding $I_{va} = \text{Embed}(I_v, W_a, k_a, m_a)$ using independently chosen scheme $W_a$, key $k_a$, and strength $\alpha_a$.
   - Goal: Suppress victim watermark decodability and/or install decodable attacker signature to assert disputed ownership.
3. **Forensic Examiner (RW-Guard):**
   - Receives candidate query image $X \in \{I_v, I_{va}\}$ (possibly degraded by post-processing).
   - Operates in a **strictly passive, key-free, and database-free** mode.
   - Has **no access** to secret keys $(k_v, k_a)$, scheme identities $(W_v, W_a)$, watermark extractors, or original images.
   - Goal: Output a scalar forensic logit $z \in \mathbb{R}$ indicating whether $X$ has undergone sequential re-watermarking ($y=1$) versus legitimate single watermarking ($y=0$).

---

## 2. Explicit Scientific Limitations

To maintain scientific integrity, the following limitations are explicitly documented and acknowledged:

### 2.1 Low-FPR Sensitivity Boundary
At an operational false positive rate of 1.00%, RW-Guard achieves a True Positive Rate of **7.87%** (ROC-derived at $\tau = 1.6040$). At the frozen validation threshold ($\tau = 1.3394016$), test sensitivity is **18.67%** at **3.33% FPR**. While the ranking discrimination is strong (ROC-AUC 0.8543), passive single-frame detection of imperceptible, localized secondary perturbations at ultra-low false positive tails is intrinsically challenging.

### 2.2 Cross-Domain Score Deflation (PACS Benchmark)
When evaluated on non-photorealistic imagery (e.g., cartoons, sketches), ForensicNet maintains strong ranking separation (ROC-AUC 0.825–0.868) but experiences **negative score deflation**:
- Mean negative logit score shifts from $-0.51$ on natural photos to $-2.45$ on cartoons.
- Consequently, the photo-calibrated threshold under-triggers, yielding low fixed TPR ($13.5\%$ on sketch).
- **Deployment Requirement:** Cross-domain deployment requires domain-specific threshold recalibration or temperature scaling.

### 2.3 Generalization to Deep Neural Watermarkers
- **StegaStamp:** Generalizes strongly in a zero-shot setting (ROC-AUC 0.9293).
- **TrustMark (ICCV 2025):** Exhibits significant cross-family distribution shift under zero-shot evaluation (ROC-AUC 0.6562 on stratified controls). However, modest supervised exposure (15% training mixture) successfully adapts ForensicNet to ROC-AUC 0.8505.
- **Finding:** ForensicNet does not exhibit universal, zero-shot generalization across completely unseen deep latent diffusion watermarkers without minimal representation adaptation.

### 2.4 White-Box Adversarial Vulnerability
ForensicNet is vulnerable to gradient-based adversarial evasion:
- Standard PGD-10 ($L_\infty, \epsilon \ge 1/255$) reduces true positive detection to **0.0%**.
- Standard adversarial training schedules exhibited convergence failures or failed to generalize to unseen test attack strengths.
- **Scope Boundary:** RW-Guard is designed for passive forensic screening, not security against adaptive white-box adversaries with gradient access.

---

## 3. Claims that Must NOT Be Made

> [!CAUTION]
> The following claims are scientifically unsubstantiated and **must never be asserted**:
> 1. **"RW-Guard resolves legal ownership dispute":** Detecting sequential embedding indicates that two watermarks were applied; it cannot establish who owns the intellectual property or who embedded first.
> 2. **"RW-Guard is universally scheme-agnostic":** Detection is effective across classical transform families and evaluated neural watermarkers, but drops to chance ($\approx 0.58$ AUC) when both victim and attacker schemes are completely unseen.
> 3. **"RW-Guard is robust to white-box attacks":** White-box PGD completely evades detection.
> 4. **"RW-Guard extracts or removes watermarks":** The system performs binary forensic classification only; it does not decode or remove payloads.
