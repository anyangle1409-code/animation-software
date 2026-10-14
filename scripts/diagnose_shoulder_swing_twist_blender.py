"""W3 feasibility: swing-twist decomposition of the upper arm relative to the scapula along the coupled 0-160 motion.

Prints, per 10 deg of humerothoracic elevation and side, the total rotation of the upper arm relative to its scapula
(relative to rest), its swing (about an axis perpendicular to the humeral long axis) and its twist (about it).
With the hanging (A-pose) rest, swing approaches 166 deg near overhead, where the twist is ill defined and wraps.
Diagnostic only; nothing is changed or approved.
"""
import sys, math
from mathutils import Quaternion
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))
import build_functional_shoulder_correction_blender as correction
res = correction.build_corrected_scene(); rig = res["runtime"]
def rel(n, parent):
    pb, pp = rig.pose.bones[n], rig.pose.bones[parent]
    b, bp = rig.data.bones[n], rig.data.bones[parent]
    return ((bp.matrix_local.inverted() @ b.matrix_local).inverted() @ (pp.matrix.inverted() @ pb.matrix)).to_quaternion()
for a in range(0, 161, 10):
    correction.apply_corrected_pose(res, a)
    for s in ("r", "l"):
        q = rel(f"upperarm_{s}", f"scapula_{s}")
        tw = Quaternion((q.w, 0.0, q.y, 0.0)); tw.normalize()
        sw = q @ tw.inverted()
        ta = 2 * math.degrees(math.atan2(q.y, q.w))
        print("TW", a, s, "total", round(math.degrees(q.angle), 1), "swing", round(math.degrees(sw.angle), 1), "twist", round(ta, 1))
