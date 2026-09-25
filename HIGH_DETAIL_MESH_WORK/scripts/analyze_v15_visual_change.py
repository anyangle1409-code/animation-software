"""Quantify matched V13e/V15 review-image change without auto-accepting anatomy.

This is a heuristic aid, not a visual verdict. It reports:
- subject-region pixel change;
- silhouette XOR;
- interior shading-gradient change (useful for faceting/segmentation);
- whether the candidate appears non-marginally different from V13e.

Matched cameras/poses come from prepare_v15_matched_review.py.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VERSION = "v15a_deep_hand_rebuild"

VIEWS = [
    ("open_palm", "open_hand_review", "hand"),
    ("open_back", "open_hand_review", "hand_back"),
    ("open_web", "open_hand_review", "hand_web"),
    ("fist_palm", "closed_fist_review", "hand"),
    ("fist_back", "closed_fist_review", "hand_back"),
    ("fist_side", "closed_fist_review", "hand_side"),
    ("curl", "dumbbell_bicep_curl_bottom", "hand"),
    ("pushup", "push_up_bottom", "hand"),
    ("pullup", "pull_up_peak", "hand"),
]

def load(path):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)

def background(im):
    h, w, _ = im.shape
    s = max(8, min(h, w) // 20)
    samples = np.concatenate([
        im[:s, :s].reshape(-1, 3),
        im[:s, -s:].reshape(-1, 3),
        im[-s:, :s].reshape(-1, 3),
        im[-s:, -s:].reshape(-1, 3),
    ], axis=0)
    return np.median(samples, axis=0)

def mask(im, bg):
    return np.linalg.norm(im - bg[None, None, :], axis=2) > 22.0

def erode1(m):
    out = m.copy()
    out[1:, :] &= m[:-1, :]
    out[:-1, :] &= m[1:, :]
    out[:, 1:] &= m[:, :-1]
    out[:, :-1] &= m[:, 1:]
    return out

def gradient_energy(im, m):
    gray = im.mean(axis=2)
    gx = np.zeros_like(gray)
    gy = np.zeros_like(gray)
    gx[:, 1:] = np.abs(gray[:, 1:] - gray[:, :-1])
    gy[1:, :] = np.abs(gray[1:, :] - gray[:-1, :])
    interior = erode1(m)
    values = (gx + gy)[interior]
    return float(values.mean()) if values.size else 0.0

def analyze(a, b):
    bg = (background(a) + background(b)) * 0.5
    ma, mb = mask(a, bg), mask(b, bg)
    union = ma | mb
    diff = np.abs(a - b)
    changed = np.max(diff, axis=2) > 8.0
    subject_pixels = int(union.sum())
    changed_subject = int((changed & union).sum())
    silhouette = int((ma ^ mb).sum())
    return {
        "subject_pixels": subject_pixels,
        "changed_subject_pct": (100.0 * changed_subject / subject_pixels) if subject_pixels else 0.0,
        "silhouette_xor_pct": (100.0 * silhouette / subject_pixels) if subject_pixels else 0.0,
        "mean_abs_rgb_delta_subject": float(diff[union].mean()) if subject_pixels else 0.0,
        "baseline_interior_gradient": gradient_energy(a, ma),
        "candidate_interior_gradient": gradient_energy(b, mb),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default=DEFAULT_VERSION)
    args = ap.parse_args()
    folder = ROOT / f"renders_{args.version}"
    rows = {}
    for label, pose, view in VIEWS:
        base = folder / f"{pose}_baseline_{view}.png"
        cand = folder / f"{pose}_candidate_{view}.png"
        if not base.is_file() or not cand.is_file():
            raise SystemExit(f"Missing matched visual pair: {base.name} / {cand.name}")
        rows[label] = analyze(load(base), load(cand))

    primary = [rows[k]["changed_subject_pct"] for k in (
        "open_palm", "open_back", "open_web", "fist_palm", "fist_back", "fist_side"
    )]
    silhouette = [rows[k]["silhouette_xor_pct"] for k in (
        "open_palm", "open_back", "fist_palm", "fist_back", "fist_side"
    )]
    gradient_delta = {
        k: rows[k]["candidate_interior_gradient"] - rows[k]["baseline_interior_gradient"]
        for k in rows
    }

    # This does NOT mean anatomically better. It only catches a repeat of the
    # V14e problem where a technically large topology edit barely changes the image.
    change_signal_present = (
        float(np.median(primary)) >= 0.50
        or max(primary, default=0.0) >= 1.50
        or max(silhouette, default=0.0) >= 0.60
    )
    report = {
        "baseline": "V13e",
        "candidate": args.version,
        "views": rows,
        "primary_changed_subject_median_pct": float(np.median(primary)),
        "primary_changed_subject_max_pct": max(primary, default=0.0),
        "primary_silhouette_xor_max_pct": max(silhouette, default=0.0),
        "interior_gradient_delta_candidate_minus_baseline": gradient_delta,
        "change_signal_present": bool(change_signal_present),
        "interpretation": (
            "Heuristic only. change_signal_present=false means the new candidate is probably "
            "too visually similar to V13e to justify acceptance. true does not mean anatomy is correct."
        ),
    }
    out = ROOT / "reports" / f"{args.version}_visual_change_metrics.json"
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
