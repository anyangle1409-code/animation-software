#!/usr/bin/env python3
"""Independent camera/scale check for annotated renders (pure Python; reads the PNGs and render manifest).

Each annotated view contains a red probe sphere at a known world point. Red pixels are labelled into connected components;
the probe is the component that is compact (bounding-box aspect <= 1.5 and fill >= 0.5), which separates it from the red
X-axis line WITHOUT using the expected position (so the check is not circular). Its centroid is compared with the analytic
orthographic projection of the probe's world point; the error is reported in pixels and millimetres.

  render_camera_check.py --dir DIR [--out JSON]
"""
import argparse, json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


def basis(direction, up):
    z = np.asarray(direction, float); z /= np.linalg.norm(z)
    x = np.cross(up, z); x /= np.linalg.norm(x); y = np.cross(z, x)
    return x, y


def check(png, view):
    im = np.asarray(Image.open(png).convert('RGB')).astype(float) / 255
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    mask = (r > 0.3) & (r > 3 * g) & (r > 3 * b)
    lab, n = ndimage.label(mask)
    blobs = []
    for k in range(1, n + 1):
        ys, xs = np.nonzero(lab == k)
        h, w = np.ptp(ys) + 1, np.ptp(xs) + 1
        if len(xs) >= 20 and max(h, w) / min(h, w) <= 1.5 and len(xs) / (h * w) >= 0.5:
            blobs.append((len(xs), xs.mean(), ys.mean()))
    res = im.shape[1]; s = view['ortho_scale_m']
    x, y = basis(view['direction'], view['up'])
    d = np.asarray(view['probe_world_m']) - np.asarray(view['target_world_m'])
    exp = ((d @ x / s + 0.5) * res, (0.5 - d @ y / s) * res)
    if len(blobs) != 1:
        return {'probe_blobs_found': len(blobs), 'pass': False}
    _, cx, cy = blobs[0]
    err = float(np.hypot(cx - exp[0], cy - exp[1]))
    return {'probe_blobs_found': 1, 'pixel_centroid': [round(cx, 2), round(cy, 2)], 'expected_pixel': [round(exp[0], 2), round(exp[1], 2)],
            'error_px': round(err, 3), 'error_mm': round(err * s * 1000 / res, 3), 'mm_per_px': round(s * 1000 / res, 4), 'pass': err <= 2.0}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--dir', required=True); ap.add_argument('--out')
    o = ap.parse_args(); D = Path(o.dir)
    m = json.loads((D / 'manifest.json').read_text())
    out = {k: check(D / f'{k}.png', v) for k, v in m['views'].items() if (D / f'{k}.png').exists()}
    if o.out:
        Path(o.out).write_text(json.dumps({'criterion': 'probe centroid within 2 px of analytic projection (2 px ~ blob centroid quantisation)', 'views': out}, indent=1) + '\n')
    for k, v in out.items():
        print(k, v.get('error_px'), v.get('error_mm'), v['pass'])


if __name__ == '__main__':
    main()
