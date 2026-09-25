"""Download the two datasets.

  python download_data.py                # COCO val2017 (5000 photos, ~1 GB) + PACS (cross-domain test)
  python download_data.py --n-coco 3000  # smaller / faster

If a download fails, you can simply drop your own images into
    data/coco/*.jpg                      (any natural photos)
    data/pacs/<domain>/*.png             (one sub-folder per domain, e.g. cartoon, sketch, art_painting, photo)
and everything else keeps working.
"""
import argparse
import os
import urllib.request
import zipfile

from tqdm import tqdm

COCO_URL = "http://images.cocodataset.org/zips/val2017.zip"


class _Bar(tqdm):
    def update_to(self, blocks=1, bsize=1, total=None):
        if total is not None:
            self.total = total
        self.update(blocks * bsize - self.n)


def get_coco(n, root="data"):
    out = os.path.join(root, "coco")
    if os.path.isdir(out) and len(os.listdir(out)) >= min(n, 5000):
        print(f"COCO already present in {out}")
        return
    os.makedirs(out, exist_ok=True)
    zpath = os.path.join(root, "val2017.zip")
    if not os.path.exists(zpath):
        with _Bar(unit="B", unit_scale=True, desc="downloading COCO val2017") as bar:
            urllib.request.urlretrieve(COCO_URL, zpath, reporthook=bar.update_to)
    with zipfile.ZipFile(zpath) as z:
        names = sorted(x for x in z.namelist() if x.lower().endswith(".jpg"))[:n]
        for nm in tqdm(names, desc="extracting"):
            with open(os.path.join(out, os.path.basename(nm)), "wb") as f:
                f.write(z.read(nm))
    print(f"{len(names)} COCO images in {out}")


def get_pacs(n_per_domain, root="data"):
    from datasets import load_dataset
    out = os.path.join(root, "pacs")
    ds = load_dataset("flwrlabs/pacs", split="train")
    feat = ds.features["domain"]
    domains = ds["domain"]
    if hasattr(feat, "int2str"):
        domains = [feat.int2str(d) for d in domains]
    counts = {}
    for i, dom in enumerate(tqdm(domains, desc="saving PACS")):
        if counts.get(dom, 0) >= n_per_domain:
            continue
        os.makedirs(os.path.join(out, dom), exist_ok=True)
        ds[i]["image"].convert("RGB").save(os.path.join(out, dom, f"{i:05d}.png"))
        counts[dom] = counts.get(dom, 0) + 1
    print("PACS images per domain:", counts)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--n-coco", type=int, default=5000)
    p.add_argument("--n-pacs", type=int, default=400, help="images per PACS domain")
    p.add_argument("--skip-coco", action="store_true")
    p.add_argument("--skip-pacs", action="store_true")
    a = p.parse_args()
    if not a.skip_coco:
        get_coco(a.n_coco)
    if not a.skip_pacs:
        get_pacs(a.n_pacs)
