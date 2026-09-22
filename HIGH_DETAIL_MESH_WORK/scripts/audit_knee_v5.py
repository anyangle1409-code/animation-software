"""Locate high-curvature knee vertices in the fixed-rig squat peak."""
import json
from pathlib import Path

import numpy as np

root = Path(__file__).resolve().parents[1]
ref = json.loads((root / 'reports/squat_sculpt_reference_v5.json').read_text())
points = np.asarray(ref['points'])
faces = np.asarray(ref['indices']).reshape(-1, 3)
adj = [set() for _ in points]
for a, b, c in faces:
    adj[a].update((int(b), int(c)))
    adj[b].update((int(a), int(c)))
    adj[c].update((int(a), int(b)))

report = {'knees': {}}
for side, centre_list in ref['knees'].items():
    centre = np.asarray(centre_list)
    distance = np.linalg.norm(points - centre, axis=1)
    region = np.flatnonzero((distance < .18) & (points[:, 2] > centre[2] - .05))
    records = []
    for index in region:
        neighbours = list(adj[index])
        if len(neighbours) < 3:
            continue
        residual = points[index] - points[neighbours].mean(axis=0)
        records.append({'vertex': int(index), 'residual_mm': float(np.linalg.norm(residual)*1000),
                        'offset_mm': ((points[index]-centre)*1000).round(1).tolist(),
                        'valence': len(neighbours)})
    records.sort(key=lambda row: row['residual_mm'], reverse=True)
    report['knees'][side] = {'centre': centre_list, 'region_vertices': len(region),
                             'median_residual_mm': float(np.median([r['residual_mm'] for r in records])),
                             'p95_residual_mm': float(np.quantile([r['residual_mm'] for r in records], .95)),
                             'top': records[:30]}
    print(side, {key: value for key, value in report['knees'][side].items() if key != 'top'})
    print('top', records[:8])

(root / 'reports/knee_audit_v5.json').write_text(json.dumps(report, indent=2))
