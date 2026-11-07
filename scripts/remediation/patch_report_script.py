import os

path = "scripts/remediation/generate_final_acceptance_report.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read().replace("\r\n", "\n")

old_1024 = """| **1024 x 1024 px** | `{pri_sha[:8]}...` | 200 | 400 | **0.8290** [0.8012, 0.8568] | 7.20% | 0.93% | 7.13% |"""

new_1024 = """| **1024 x 1024 px** | `{pri_sha[:8]}...` | 200 | 400 | **0.7998** [0.7575, 0.8407] | 18.50% | 1.50% | 16.50% |

- **Sample Size Disclosure (1024px):** The 1024px evaluation evaluates 200 held-out sources (400 samples: 200 positive, 200 negative) due to high-resolution GPU VRAM constraints, whereas 128–512px evaluate 1,500 sources (3,000 samples). Exact integer confusion counts at tau=1.3394016: True Positives = 37, False Positives = 3, True Negatives = 197, False Negatives = 163. Fixed TPR = 37/200 = 18.50%, Fixed FPR = 3/200 = 1.50%, ROC TPR@1% FPR = 33/200 = 16.50% at tau=1.4064. ROC-AUC is 0.799825 (0.7998 or 0.800), perfectly matching manuscript Table 7 Row 14. The previously reported narrative figures (0.8290, 7.20%, 0.93%, 7.13%) were an obsolete transcription from jpeg85 benign edit metrics and an early rough estimate, now fully cleansed."""

assert old_1024 in text, "old_1024 not found in report script"
text = text.replace(old_1024, new_1024)

old_pacs = """     - **Calibration Benchmark (800 sources / 1,600 samples, size 224, `pacs_results.json`):**
       - Photo: **0.8192** [95% CI: 0.7824, 0.8564]
       - Art Painting: **0.8616** [95% CI: 0.8247, 0.8973]
       - Cartoon: **0.8677** [95% CI: 0.8334, 0.9007]
       - Sketch: **0.8247** [95% CI: 0.7843, 0.8631]
     - **Full-Corpus Benchmark (1,600 sources / 3,200 samples, size 224):**
       - Photo: **0.8054**, Art Painting: **0.8421**, Cartoon: **0.8675**, Sketch: **0.8398**.
     - **Scientific Finding:** The fixed SRM high-pass filter bank (K_hp) suppresses low-frequency semantic content, preserving high ranking discrimination (AUC 0.80-0.87) across all domains. However, artistic rendering alters residual statistics, causing negative logit scores to deflate (mean score drops from -0.51 on Photo to -2.45 on Cartoon), which causes a fixed photo-threshold (tau=1.3394) to under-trigger (sketch TPR drops to 13.5%)."""

new_pacs = """     - **Calibration Benchmark (800 sources / 1,600 samples, size 224, `pacs_results.json`):**
       - Photo: **0.8192** [95% CI: 0.7824, 0.8564] | Fixed TPR: **15.00%** (30/200), Fixed FPR: **2.50%** (5/200)
       - Art Painting: **0.8616** [95% CI: 0.8247, 0.8973] | Fixed TPR: **18.00%** (36/200), Fixed FPR: **3.50%** (7/200)
       - Cartoon: **0.8677** [95% CI: 0.8334, 0.9007] | Fixed TPR: **22.50%** (45/200), Fixed FPR: **2.50%** (5/200)
       - Sketch: **0.8247** [95% CI: 0.7843, 0.8631] | Fixed TPR: **13.50%** (27/200), Fixed FPR: **1.50%** (3/200)
     - **Full-Corpus Benchmark (1,600 sources / 3,200 samples, size 224):**
       - Photo: **0.8054**, Art Painting: **0.8421**, Cartoon: **0.8675**, Sketch: **0.8398**.
     - **Scientific Finding & Narrative Cleansing:** The fixed SRM high-pass filter bank (K_hp) suppresses low-frequency semantic content, preserving high ranking discrimination (AUC 0.80-0.87) across all domains. However, artistic rendering alters residual statistics, causing negative logit scores to deflate (mean score drops from -0.51 on Photo to -2.45 on Cartoon), which causes a fixed photo-threshold (tau=1.3394) to under-trigger (Fixed TPR is 15.00% on Photo and drops to 13.50% on Sketch). Note: The 18.67% figure cited in earlier working notes was the COCO in-distribution natural photograph test TPR (280/1500), not the PACS Photo TPR (30/200 = 15.00%). Manuscript Table 9 correctly cites 0.150 for Photo and 0.135 for Sketch."""

assert old_pacs in text, "old_pacs not found in report script"
text = text.replace(old_pacs, new_pacs)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("Patch applied successfully to generate_final_acceptance_report.py")
