import json
import glob
import os
import hashlib
import torch

def get_hash(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while chunk := f.read(8192*1024):
            h.update(chunk)
    return h.hexdigest()

runs = ['seed0', 'seed1', 'seed2', 'baseline_e9', 'baseline_full', 'holdout_dct', 'holdout_fft', 'trustmark_mix', 'nohp_ablation', 'resnet18_baseline', 'simple_baseline']
base = 'D:/projects/rewm-guard/runs'

results = {}
for r in runs:
    p_best = os.path.join(base, r, 'best.pt')
    p_hist = os.path.join(base, r, 'history.json')
    p_cfg = os.path.join(base, r, 'config.json')
    print(f"=== Run: {r} ===")
    info = {'run': r}
    if os.path.exists(p_best):
        info['best_pt_exists'] = True
        info['size_bytes'] = os.path.getsize(p_best)
        info['sha256'] = get_hash(p_best)
        print(f"  best.pt size: {info['size_bytes']} bytes, SHA256: {info['sha256']}")
        ckpt = torch.load(p_best, map_location='cpu')
        info['keys'] = list(ckpt.keys())
        for k in ['epoch', 'val_auc', 'auc', 'threshold', 'args']:
            if k in ckpt:
                info[k] = str(ckpt[k])
                print(f"  {k}: {ckpt[k]}")
    else:
        info['best_pt_exists'] = False
        print("  best.pt NOT found")
        
    if os.path.exists(p_hist):
        with open(p_hist) as f:
            hist = json.load(f)
            info['num_epochs'] = len(hist)
            best_entry = max(hist, key=lambda x: x.get('val_auc', x.get('auc', 0)))
            info['best_val_entry'] = best_entry
            print(f"  history epochs: {len(hist)}, best entry: {best_entry}")
            
    if os.path.exists(p_cfg):
        with open(p_cfg) as f:
            cfg = json.load(f)
            info['config'] = cfg
            print(f"  config: {cfg}")
            
    results[r] = info

with open("audit/checkpoint_audit.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nAudit written to audit/checkpoint_audit.json")
