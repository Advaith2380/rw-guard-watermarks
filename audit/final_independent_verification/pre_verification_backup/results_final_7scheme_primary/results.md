# Results for `checkpoints/final/rwguard_final_7scheme.pt`

Seen schemes: ['dct_qim', 'dwt_qim', 'ss_spatial', 'fft_ring', 'nmp_freq', 'svd_qim', 'dct_svd'] - unseen: none

Fixed operating point: logit > 1.339 (1% FPR on validation)


## 1 in-distribution

| condition | n | AUC | TPR@1%FPR | TPR@0.1%FPR | TPR @fixed thr | FPR @fixed thr |
|---|---|---|---|---|---|---|
| COCO 256px (seen schemes) | 3000 | 0.854 | 0.079 | 0.006 | 0.187 | 0.033 |

## 2 benign post-processing

| condition | n | AUC | TPR@1%FPR | TPR@0.1%FPR | TPR @fixed thr | FPR @fixed thr |
|---|---|---|---|---|---|---|
| none | 3000 | 0.868 | 0.077 | 0.008 | 0.218 | 0.036 |
| jpeg95 | 3000 | 0.849 | 0.088 | 0.009 | 0.175 | 0.031 |
| jpeg85 | 3000 | 0.834 | 0.071 | 0.011 | 0.077 | 0.011 |
| jpeg75 | 3000 | 0.834 | 0.065 | 0.009 | 0.078 | 0.013 |
| noise1 | 3000 | 0.862 | 0.079 | 0.010 | 0.226 | 0.038 |
| noise2 | 3000 | 0.849 | 0.073 | 0.019 | 0.248 | 0.045 |
| blur0.5 | 3000 | 0.854 | 0.045 | 0.010 | 0.129 | 0.023 |
| bright | 3000 | 0.855 | 0.057 | 0.005 | 0.161 | 0.027 |
| jpeg85+noise1 | 3000 | 0.832 | 0.049 | 0.013 | 0.081 | 0.013 |
| blur0.5+jpeg85 | 3000 | 0.833 | 0.059 | 0.007 | 0.083 | 0.017 |
| bright+jpeg85 | 3000 | 0.812 | 0.046 | 0.011 | 0.062 | 0.013 |

## 3 resolution

| condition | n | AUC | TPR@1%FPR | TPR@0.1%FPR | TPR @fixed thr | FPR @fixed thr |
|---|---|---|---|---|---|---|
| 128px | 3000 | 0.846 | 0.069 | 0.009 | 0.326 | 0.067 |
| 256px | 3000 | 0.854 | 0.079 | 0.006 | 0.187 | 0.033 |
| 384px | 3000 | 0.858 | 0.083 | 0.005 | 0.089 | 0.011 |

## 5 cross-domain (PACS)

| condition | n | AUC | TPR@1%FPR | TPR@0.1%FPR | TPR @fixed thr | FPR @fixed thr |
|---|---|---|---|---|---|---|
| art_painting | 800 | 0.840 | 0.080 | 0.010 | 0.233 | 0.033 |
| cartoon | 800 | 0.865 | 0.145 | 0.028 | 0.207 | 0.030 |
| photo | 800 | 0.808 | 0.095 | 0.010 | 0.135 | 0.013 |
| sketch | 800 | 0.843 | 0.200 | 0.140 | 0.175 | 0.005 |

## 6 adversarial (fraction of re-watermarked images still flagged)

| attack | detected |
|---|---|
| clean positives detected | 0.360 |
| PGD-10 eps=0.5/255 (r=1) | 0.000 |
| PGD-10 eps=1.0/255 (r=1) | 0.000 |
| PGD-10 eps=2.0/255 (r=1) | 0.000 |

## Per watermark-combination (in-distribution, fraction flagged as re-watermarked)

| combo | label | n | flagged |
|---|---|---|---|
| clean | 0 | 762 | 0.001 |
| dct_qim>dct_qim | 1 | 37 | 0.108 |
| dct_qim>dct_svd | 1 | 35 | 0.143 |
| dct_qim>dwt_qim | 1 | 27 | 0.444 |
| dct_qim>fft_ring | 1 | 32 | 0.375 |
| dct_qim>nmp_freq | 1 | 25 | 0.160 |
| dct_qim>ss_spatial | 1 | 32 | 0.250 |
| dct_qim>svd_qim | 1 | 32 | 0.156 |
| dct_svd>dct_qim | 1 | 32 | 0.125 |
| dct_svd>dct_svd | 1 | 24 | 0.042 |
| dct_svd>dwt_qim | 1 | 34 | 0.206 |
| dct_svd>fft_ring | 1 | 40 | 0.025 |
| dct_svd>nmp_freq | 1 | 26 | 0.077 |
| dct_svd>ss_spatial | 1 | 31 | 0.323 |
| dct_svd>svd_qim | 1 | 25 | 0.000 |
| dwt_qim>dct_qim | 1 | 38 | 0.395 |
| dwt_qim>dct_svd | 1 | 35 | 0.257 |
| dwt_qim>dwt_qim | 1 | 23 | 0.087 |
| dwt_qim>fft_ring | 1 | 38 | 0.184 |
| dwt_qim>nmp_freq | 1 | 31 | 0.323 |
| dwt_qim>ss_spatial | 1 | 35 | 0.429 |
| dwt_qim>svd_qim | 1 | 23 | 0.174 |
| fft_ring>dct_qim | 1 | 24 | 0.083 |
| fft_ring>dct_svd | 1 | 25 | 0.080 |
| fft_ring>dwt_qim | 1 | 31 | 0.258 |
| fft_ring>fft_ring | 1 | 24 | 0.083 |
| fft_ring>nmp_freq | 1 | 36 | 0.028 |
| fft_ring>ss_spatial | 1 | 51 | 0.255 |
| fft_ring>svd_qim | 1 | 23 | 0.043 |
| nmp_freq>dct_qim | 1 | 36 | 0.389 |
| nmp_freq>dct_svd | 1 | 24 | 0.042 |
| nmp_freq>dwt_qim | 1 | 29 | 0.276 |
| nmp_freq>fft_ring | 1 | 28 | 0.071 |
| nmp_freq>nmp_freq | 1 | 31 | 0.032 |
| nmp_freq>ss_spatial | 1 | 32 | 0.281 |
| nmp_freq>svd_qim | 1 | 23 | 0.043 |
| single:dct_qim | 0 | 106 | 0.104 |
| single:dct_svd | 0 | 116 | 0.000 |
| single:dwt_qim | 0 | 86 | 0.140 |
| single:fft_ring | 0 | 97 | 0.041 |
| single:nmp_freq | 0 | 116 | 0.000 |
| single:ss_spatial | 0 | 115 | 0.191 |
| single:svd_qim | 0 | 102 | 0.000 |
| ss_spatial>dct_qim | 1 | 27 | 0.222 |
| ss_spatial>dct_svd | 1 | 41 | 0.220 |
| ss_spatial>dwt_qim | 1 | 25 | 0.400 |
| ss_spatial>fft_ring | 1 | 33 | 0.212 |
| ss_spatial>nmp_freq | 1 | 20 | 0.150 |
| ss_spatial>ss_spatial | 1 | 32 | 0.344 |
| ss_spatial>svd_qim | 1 | 26 | 0.192 |
| svd_qim>dct_qim | 1 | 33 | 0.091 |
| svd_qim>dct_svd | 1 | 32 | 0.000 |
| svd_qim>dwt_qim | 1 | 39 | 0.333 |
| svd_qim>fft_ring | 1 | 32 | 0.094 |
| svd_qim>nmp_freq | 1 | 30 | 0.067 |
| svd_qim>ss_spatial | 1 | 29 | 0.207 |
| svd_qim>svd_qim | 1 | 29 | 0.000 |