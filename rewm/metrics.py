import numpy as np


def roc_auc(y, s):
    y, s = np.asarray(y), np.asarray(s, dtype=np.float64)
    npos, nneg = int((y == 1).sum()), int((y == 0).sum())
    if npos == 0 or nneg == 0:
        return float("nan")
    _, inv, counts = np.unique(s, return_inverse=True, return_counts=True)
    ranks = (np.cumsum(counts) - (counts - 1) / 2.0)[inv]
    return float((ranks[y == 1].sum() - npos * (npos + 1) / 2.0) / (npos * nneg))


def threshold_at_fpr(neg_scores, fpr):
    """Smallest threshold whose false-positive rate on the negatives is <= fpr."""
    neg = np.sort(np.asarray(neg_scores))
    k = int(np.floor(fpr * len(neg)))          # number of negatives allowed above the threshold
    return float(neg[len(neg) - k - 1]) if k < len(neg) else float(neg[0] - 1)


def tpr_at_fpr(y, s, fpr):
    y, s = np.asarray(y), np.asarray(s)
    thr = threshold_at_fpr(s[y == 0], fpr)
    return float((s[y == 1] > thr).mean())


def rates_at(y, s, thr):
    y, s = np.asarray(y), np.asarray(s)
    return float((s[y == 1] > thr).mean()), float((s[y == 0] > thr).mean())   # TPR, FPR


def roc_curve(y, s, n=400):
    y, s = np.asarray(y), np.asarray(s)
    thr = np.unique(np.quantile(s, np.linspace(0, 1, n)))
    tpr = np.array([(s[y == 1] > t).mean() for t in thr])
    fpr = np.array([(s[y == 0] > t).mean() for t in thr])
    return fpr, tpr


def summarize(y, s, thr_fixed=None):
    d = dict(n=int(len(y)), auc=roc_auc(y, s),
             tpr_at_1pct_fpr=tpr_at_fpr(y, s, 0.01), tpr_at_0p1pct_fpr=tpr_at_fpr(y, s, 0.001))
    if thr_fixed is not None:
        d["tpr_fixed_thr"], d["fpr_fixed_thr"] = rates_at(y, s, thr_fixed)
    return d


def breakdown(y, s, kinds, thr):
    """Per watermark-combination detection rate at the fixed threshold."""
    y, s, kinds = np.asarray(y), np.asarray(s), np.asarray(kinds)
    out = {}
    for k in sorted(set(kinds)):
        m = kinds == k
        out[k] = dict(n=int(m.sum()), flagged=float((s[m] > thr).mean()), label=int(y[m][0]))
    return out
