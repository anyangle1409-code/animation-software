"""Quantify matched V13e/V15 visual change, calibrated against rejected V14e.

This is a heuristic aid, not an anatomy verdict.

The repository already contains the matched V13e/V14e boards that were rejected
because the topology change was visually too small. This script measures those
boards at runtime and asks a stronger question than a fixed threshold:

    Does V15 create materially more visible hand-surface/silhouette change than
    the rejected V14e pass?

A positive result still does not mean the anatomy is correct. It only means the
candidate is not repeating V14e's "lots of topology, barely visible" failure.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VERSION = "v15a_deep_hand_rebuild"
TARGET_SIZE = (550, 600)
LABEL_CROP_TOP = 60

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

V14_BOARDS = {
    "open": ROOT / "renders_v14e_finger_body_trial" / "V14E_V13E_OPEN_HAND_COMPARISON.jpg",
    "fist": ROOT / "renders_v14e_finger_body_trial" / "V14E_V13E_CLOSED_FIST_COMPARISON.jpg",
    "exercise": ROOT / "renders_v14e_finger_body_trial" / "V14E_V13E_EXERCISE_HAND_COMPARISON.jpg",
}
BOARD_KEYS = {
    "open": ("open_palm", "open_back", "open_web"),
    "fist": ("fist_palm", "fist_back", "fist_side"),
    "exercise": ("curl", "pushup", "pullup"),
}

def load_render(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        image = image.convert("RGB").resize(TARGET_SIZE, Image.Resampling.LANCZOS)
        image = image.crop((0, LABEL_CROP_TOP, TARGET_SIZE[0], TARGET_SIZE[1]))
        return np.asarray(image, dtype=np.float32)

def board_pairs(path: Path):
    """Return [(baseline,candidate), ...] for the three columns of a saved board."""
    with Image.open(path) as raw:
        image = raw.convert("RGB")
        width, height = image.size
        cell_w = width // 3
        # Board builders use 42 px header + two 600 px rows + 40 px tail.
        # Derive row height so this remains robust to a future board resize.
        cell_h = (height - 82) // 2
        if cell_w <= 0 or cell_h <= 0:
            raise RuntimeError(f"Unexpected comparison board size {image.size}: {path}")
        pairs = []
        for col in range(3):
            x0 = col * cell_w
            x1 = x0 + cell_w
            top = image.crop((x0, 42 + LABEL_CROP_TOP, x1, 42 + cell_h))
            bottom = image.crop((x0, 42 + cell_h + LABEL_CROP_TOP, x1, 42 + 2 * cell_h))
            top = top.resize((550, 540), Image.Resampling.LANCZOS)
            bottom = bottom.resize((550, 540), Image.Resampling.LANCZOS)
            pairs.append((
                np.asarray(top, dtype=np.float32),
                np.asarray(bottom, dtype=np.float32),
            ))
        return pairs

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
    if a.shape != b.shape:
        raise RuntimeError(f"Matched images have different shapes: {a.shape} vs {b.shape}")
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

def summarize(rows):
    primary_keys = ("open_palm", "open_back", "open_web", "fist_palm", "fist_back", "fist_side")
    silhouette_keys = ("open_palm", "open_back", "fist_palm", "fist_back", "fist_side")
    primary = [rows[k]["changed_subject_pct"] for k in primary_keys]
    silhouette = [rows[k]["silhouette_xor_pct"] for k in silhouette_keys]
    return {
        "primary_changed_subject_median_pct": float(np.median(primary)),
        "primary_changed_subject_max_pct": max(primary, default=0.0),
        "primary_silhouette_xor_max_pct": max(silhouette, default=0.0),
    }

def measure_v14_reference():
    missing = [str(p) for p in V14_BOARDS.values() if not p.is_file()]
    if missing:
        raise SystemExit("Missing V14e rejected calibration board(s):\n- " + "\n- ".join(missing))
    rows = {}
    for group, path in V14_BOARDS.items():
        pairs = board_pairs(path)
        for key, pair in zip(BOARD_KEYS[group], pairs):
            rows[key] = analyze(*pair)
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default=DEFAULT_VERSION)
    args = ap.parse_args()

    folder = ROOT / f"renders_{args.version}"
    v15_rows = {}
    for label, pose, view in VIEWS:
        base = folder / f"{pose}_baseline_{view}.png"
        cand = folder / f"{pose}_candidate_{view}.png"
        if not base.is_file() or not cand.is_file():
            raise SystemExit(f"Missing matched visual pair: {base.name} / {cand.name}")
        v15_rows[label] = analyze(load_render(base), load_render(cand))

    v14_rows = measure_v14_reference()
    v15 = summarize(v15_rows)
    v14 = summarize(v14_rows)

    # V14e is the known rejected "too little visible change" reference.
    # Require V15 to beat it by a meaningful relative AND absolute margin in
    # at least one of the two most robust signals. This is intentionally not
    # an anatomy score and cannot promote a candidate.
    changed_subject_target = max(
        v14["primary_changed_subject_median_pct"] * 1.25,
        v14["primary_changed_subject_median_pct"] + 0.20,
    )
    silhouette_target = max(
        v14["primary_silhouette_xor_max_pct"] * 1.25,
        v14["primary_silhouette_xor_max_pct"] + 0.15,
    )
    exceeds_v14 = (
        v15["primary_changed_subject_median_pct"] >= changed_subject_target
        or v15["primary_silhouette_xor_max_pct"] >= silhouette_target
    )

    gradient_delta = {
        k: v15_rows[k]["candidate_interior_gradient"] - v15_rows[k]["baseline_interior_gradient"]
        for k in v15_rows
    }
    report = {
        "baseline": "V13e",
        "candidate": args.version,
        "rejected_calibration_candidate": "V14e",
        "v15_views": v15_rows,
        "v14e_rejected_views": v14_rows,
        "v15_summary": v15,
        "v14e_rejected_summary": v14,
        "required_to_clearly_exceed_v14e": {
            "median_changed_subject_pct": changed_subject_target,
            "or_max_silhouette_xor_pct": silhouette_target,
        },
        "interior_gradient_delta_candidate_minus_baseline": gradient_delta,
        "change_signal_present": bool(exceeds_v14),
        "clearly_exceeds_rejected_v14e_change": bool(exceeds_v14),
        "interpretation": (
            "Heuristic only. false means V15 is not visibly changing the hand enough beyond "
            "the already-rejected V14e pass. true means the change is materially stronger "
            "than V14e, but does not mean the anatomy is correct or accepted."
        ),
    }
    out = ROOT / "reports" / f"{args.version}_visual_change_metrics.json"
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
