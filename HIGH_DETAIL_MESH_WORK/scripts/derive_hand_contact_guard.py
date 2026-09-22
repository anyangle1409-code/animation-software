"""Mark original hand vertices near the frozen push-up floor-contact surface."""
import json
from pathlib import Path

import numpy as np

root = Path(__file__).resolve().parents[1]
reference = json.loads((root / 'reports/sculpt_reference.json').read_text())
hand = np.asarray([row['hand'] > .001 for row in reference['ownership']])
guard = np.zeros(len(hand), dtype=bool)
summary = {}
for phase in ('bottom', 'sample_12', 'peak', 'return'):
    path = root / f'reports/poses_v4b/push_up_{phase}_baseline.json'
    points = np.asarray(json.loads(path.read_text())['meshes'][0]['positions'])[:len(hand)]
    minimum = float(points[hand, 1].min())
    near = hand & (points[:, 1] <= minimum + .030)
    guard |= near
    summary[phase] = {'minimum_y': minimum, 'near_vertices': int(near.sum())}
destination = root / 'reports/hand_contact_guard_v5.json'
destination.write_text(json.dumps({'threshold_mm': 30, 'original_vertex_ids': np.flatnonzero(guard).tolist(), 'phases': summary}, indent=2))
print({'guard_vertices': int(guard.sum()), 'phases': summary})
