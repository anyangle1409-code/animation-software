"""Build V15 visual difference maps and one self-contained local review HTML."""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VERSION = "v15a_deep_hand_rebuild"

VIEWS = [
    ("open_palm", "Open palm", "open_hand_review", "hand"),
    ("open_back", "Open back", "open_hand_review", "hand_back"),
    ("open_web", "Thumb-index web", "open_hand_review", "hand_web"),
    ("fist_palm", "Fist palm", "closed_fist_review", "hand"),
    ("fist_back", "Fist back", "closed_fist_review", "hand_back"),
    ("fist_side", "Fist side", "closed_fist_review", "hand_side"),
    ("curl", "Curl grip", "dumbbell_bicep_curl_bottom", "hand"),
    ("pushup", "Push-up contact", "push_up_bottom", "hand"),
    ("pullup", "Pull-up grip", "pull_up_peak", "hand"),
]

def read_json(path):
    try:
        return json.loads(path.read_text()) if path.is_file() else None
    except Exception:
        return None

def label_for(version):
    m = re.match(r"v(\d+)([a-z]?)", version, re.I)
    return f"V{m.group(1)}{m.group(2)}" if m else version.upper()

def diff_image(a_path, b_path, out_path):
    with Image.open(a_path) as a_raw, Image.open(b_path) as b_raw:
        a = a_raw.convert("RGB")
        b = b_raw.convert("RGB")
        if a.size != b.size:
            b = b.resize(a.size, Image.Resampling.LANCZOS)
        aa = np.asarray(a, dtype=np.int16)
        bb = np.asarray(b, dtype=np.int16)
        d = np.max(np.abs(aa - bb), axis=2).astype(np.uint8)
        # Amplify subtle geometry/shading differences while staying grayscale.
        amplified = np.clip(d.astype(np.int16) * 5, 0, 255).astype(np.uint8)
        Image.fromarray(amplified, mode="L").save(out_path)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default=DEFAULT_VERSION)
    args = ap.parse_args()
    version = args.version
    label = label_for(version)

    renders = ROOT / f"renders_{version}"
    diff_dir = renders / "diffs_vs_v13e"
    diff_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for key, title, pose, view in VIEWS:
        base = renders / f"{pose}_baseline_{view}.png"
        cand = renders / f"{pose}_candidate_{view}.png"
        if not base.is_file() or not cand.is_file():
            continue
        diff = diff_dir / f"{key}_difference.png"
        diff_image(base, cand, diff)
        rows.append((key, title, base, cand, diff))

    audit = read_json(ROOT / "reports" / f"audit_{version}_blender.json")
    visual = read_json(ROOT / "reports" / f"{version}_visual_change_metrics.json")
    integration = read_json(ROOT / "reports" / f"current_source_{version}" / "integration_report.json")
    frozen = read_json(ROOT / "reports" / f"{version}_frozen_pipeline_status.json")

    summary_path = ROOT / f"V15_POST_EDIT_REPORT_{version}.md"
    summary_text = summary_path.read_text() if summary_path.is_file() else "Summary not generated yet."

    def rel(path):
        return path.relative_to(ROOT).as_posix()

    cards = []
    for key, title, base, cand, diff in rows:
        cards.append(f"""
        <section class="view">
          <h3>{html.escape(title)}</h3>
          <div class="triple">
            <figure><img src="{rel(base)}"><figcaption>V13e baseline</figcaption></figure>
            <figure><img src="{rel(cand)}"><figcaption>{html.escape(label)}</figcaption></figure>
            <figure><img src="{rel(diff)}"><figcaption>Difference ×5</figcaption></figure>
          </div>
        </section>
        """)

    facet_rows = ""
    if audit:
        for item in audit.get("remaining_faceting_priority", []):
            facet_rows += (
                "<tr>"
                f"<td>{html.escape(str(item['digit']))}</td>"
                f"<td>{item['candidate_sharp_ratio_gt_35']:.4f}</td>"
                f"<td>{item['candidate_sharp_ratio_gt_50']:.4f}</td>"
                f"<td>{item['delta_gt_35_vs_v13e']:+.4f}</td>"
                "</tr>"
            )

    v15_summary = visual.get("v15_summary", {}) if visual else {}
    v14_summary = visual.get("v14e_rejected_summary", {}) if visual else {}

    page = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{html.escape(label)} hand review</title>
<style>
body{{font-family:Arial,sans-serif;margin:24px;background:#181b20;color:#eee}}
h1,h2,h3{{margin-top:1.2em}} .status{{padding:12px;border:1px solid #555}}
.triple{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}}
figure{{margin:0;background:#222;padding:8px}} img{{width:100%;height:auto;display:block}}
figcaption{{padding-top:6px}} table{{border-collapse:collapse;width:100%;max-width:900px}}
th,td{{border:1px solid #555;padding:7px;text-align:left}} pre{{white-space:pre-wrap;background:#111;padding:12px}}
.pass{{font-weight:bold}} @media(max-width:900px){{.triple{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<h1>{html.escape(label)} vs V13e — hand review</h1>
<div class="status">
<p><strong>Frozen pipeline:</strong> {html.escape(str(frozen.get('pass') if frozen else 'missing'))}</p>
<p><strong>Clears rejected V14e visual-change magnitude:</strong>
{html.escape(str(visual.get('clearly_exceeds_rejected_v14e_change') if visual else 'missing'))}</p>
<p><strong>Latest-source no regression:</strong>
{html.escape(str(integration.get('integration_no_regression') if integration else 'missing'))}</p>
<p><strong>Latest source HEAD:</strong> {html.escape(str(integration.get('source_head') if integration else 'missing'))}</p>
</div>

<h2>Rejected-V14e calibration</h2>
<table>
<tr><th>Metric</th><th>Rejected V14e</th><th>{html.escape(label)}</th></tr>
<tr><td>Median changed subject %</td>
<td>{v14_summary.get('primary_changed_subject_median_pct','—')}</td>
<td>{v15_summary.get('primary_changed_subject_median_pct','—')}</td></tr>
<tr><td>Max silhouette XOR %</td>
<td>{v14_summary.get('primary_silhouette_xor_max_pct','—')}</td>
<td>{v15_summary.get('primary_silhouette_xor_max_pct','—')}</td></tr>
</table>

<h2>Remaining faceting priority</h2>
<table>
<tr><th>Digit</th><th>&gt;35° sharp-length ratio</th><th>&gt;50° ratio</th><th>Δ &gt;35° vs V13e</th></tr>
{facet_rows or '<tr><td colspan="4">Audit not available</td></tr>'}
</table>

<h2>Matched views and difference maps</h2>
{''.join(cards) if cards else '<p>Matched renders not available yet.</p>'}

<h2>Consolidated report</h2>
<pre>{html.escape(summary_text)}</pre>

<p><strong>Important:</strong> numerical and image-change checks do not approve anatomy.
The matched views still require a visual call before grip refitting.</p>
</body>
</html>
"""
    out = ROOT / f"V15_REVIEW_{version}.html"
    out.write_text(page, encoding="utf-8")
    if version == DEFAULT_VERSION:
        (ROOT / "V15_REVIEW.html").write_text(page, encoding="utf-8")
    print(out)

if __name__ == "__main__":
    main()
