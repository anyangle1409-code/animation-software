"""Check paired knee seam gaps throughout saved exercise poses."""
import json
from pathlib import Path

import numpy as np

root = Path(__file__).resolve().parents[1]
seams = json.loads((root / 'reports/knee_seam_v5.json').read_text())['knees']
report = {'candidate': 'v6_knee_seam', 'poses': {}, 'max_gap_mm': 0.0}
for file in sorted((root / 'reports/poses_v6_knee_seam').glob('*_candidate.json')):
    pose = json.loads(file.read_text())
    points = np.asarray(pose['meshes'][0]['positions'])
    by_side = {}
    for side, entry in seams.items():
        first, second = entry['paths']
        gap = float(np.linalg.norm(points[first] - points[second], axis=1).max() * 1000)
        by_side[side] = gap
        report['max_gap_mm'] = max(report['max_gap_mm'], gap)
    report['poses'][file.stem] = by_side
assert len(report['poses']) == 20
assert report['max_gap_mm'] < 1e-4
(root / 'reports/knee_seam_audit_v6.json').write_text(json.dumps(report, indent=2))
print({'saved_poses': len(report['poses']), 'max_gap_mm': report['max_gap_mm']})
