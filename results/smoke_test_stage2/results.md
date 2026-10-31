# Results for `runs/smoke_test_stage2/best.pt`

Seen schemes: ['dct_qim', 'dwt_qim', 'ss_spatial', 'fft_ring'] - unseen: ['nmp_freq', 'svd_qim', 'dct_svd']

Fixed operating point: logit > -0.002 (1% FPR on validation)


## 1 in-distribution

| condition | n | AUC | TPR@1%FPR | TPR@0.1%FPR | TPR @fixed thr | FPR @fixed thr |
|---|---|---|---|---|---|---|
| COCO 256px (seen schemes) | 40 | 0.530 | 0.050 | 0.050 | 0.050 | 0.050 |

## 2 benign post-processing

| condition | n | AUC | TPR@1%FPR | TPR@0.1%FPR | TPR @fixed thr | FPR @fixed thr |
|---|---|---|---|---|---|---|
| none | 40 | 0.527 | 0.050 | 0.050 | 0.050 | 0.050 |
| jpeg95 | 40 | 0.532 | 0.100 | 0.100 | 0.050 | 0.000 |
| jpeg85 | 40 | 0.450 | 0.000 | 0.000 | 0.000 | 0.000 |
| jpeg75 | 40 | 0.542 | 0.150 | 0.150 | 0.050 | 0.000 |
| noise1 | 40 | 0.482 | 0.000 | 0.000 | 0.050 | 0.050 |
| noise2 | 40 | 0.453 | 0.000 | 0.000 | 0.050 | 0.050 |
| blur0.5 | 40 | 0.507 | 0.050 | 0.050 | 0.050 | 0.000 |
| bright | 40 | 0.522 | 0.050 | 0.050 | 0.050 | 0.050 |

## 3 resolution

| condition | n | AUC | TPR@1%FPR | TPR@0.1%FPR | TPR @fixed thr | FPR @fixed thr |
|---|---|---|---|---|---|---|
| 128px | 40 | 0.540 | 0.000 | 0.000 | 0.000 | 0.000 |
| 256px | 40 | 0.530 | 0.050 | 0.050 | 0.050 | 0.050 |
| 384px | 40 | 0.497 | 0.000 | 0.000 | 0.000 | 0.050 |

## 4 unseen scheme

| condition | n | AUC | TPR@1%FPR | TPR@0.1%FPR | TPR @fixed thr | FPR @fixed thr |
|---|---|---|---|---|---|---|
| unseen attacker ['nmp_freq', 'svd_qim', 'dct_svd'] | 40 | 0.527 | 0.000 | 0.000 | 0.050 | 0.050 |
| unseen victim+attacker ['nmp_freq', 'svd_qim', 'dct_svd'] | 40 | 0.505 | 0.050 | 0.050 | 0.050 | 0.050 |

## 6 adversarial (fraction of re-watermarked images still flagged)

| attack | detected |
|---|---|
| clean positives detected | 0.000 |
| PGD-3 eps=1.0/255 (r=1) | 0.000 |

## Per watermark-combination (in-distribution, fraction flagged as re-watermarked)

| combo | label | n | flagged |
|---|---|---|---|
| clean | 0 | 10 | 0.100 |
| dct_qim>dwt_qim | 1 | 5 | 0.000 |
| dct_qim>fft_ring | 1 | 1 | 0.000 |
| dwt_qim>dct_qim | 1 | 1 | 0.000 |
| dwt_qim>dwt_qim | 1 | 2 | 0.500 |
| dwt_qim>fft_ring | 1 | 1 | 0.000 |
| fft_ring>dct_qim | 1 | 3 | 0.000 |
| fft_ring>dwt_qim | 1 | 1 | 0.000 |
| fft_ring>fft_ring | 1 | 2 | 0.000 |
| fft_ring>ss_spatial | 1 | 2 | 0.000 |
| single:dwt_qim | 0 | 3 | 0.000 |
| single:fft_ring | 0 | 5 | 0.000 |
| single:ss_spatial | 0 | 2 | 0.000 |
| ss_spatial>dwt_qim | 1 | 1 | 0.000 |
| ss_spatial>fft_ring | 1 | 1 | 0.000 |