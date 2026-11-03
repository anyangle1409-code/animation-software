"""Unit test (no Blender needed): the R121_ARMBAND and R121_GRIP drive rules in scripts/body_v2/r121_drives.py.

bpy and the r57 drive module are replaced by stubs; the joint readings (elevation, elbow flexion, finger curl) are fed
in directly, so only the gating arithmetic is tested:
  * R121_ARMBAND_<s> = value of its parent lockout key R121_ARM_<s>_<parent> x (1 - smoothstep over elbow e0..e1);
  * R121_GRIP_<s> = smoothstep from half the authored finger curl to the full curl;
  * a blend without these keys is left alone.
usage: python3 scripts/body_v2/tests/test_r121_drive_gates.py   (exit 1 on a failure)
"""
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.modules["bpy"] = types.SimpleNamespace(context=types.SimpleNamespace(view_layer=types.SimpleNamespace(update=lambda: None)))
STATE = {"elev": 0.0, "elbow": 0.0, "curl": 0.0}
sys.modules["original_v1_review_candidate_drives"] = types.SimpleNamespace(elevation_deg=lambda rig, s: STATE["elev"])
import r121_drives as R  # noqa: E402

R.plane_factor = lambda rig, s: 0.0
R.ext_factor = lambda rig, s: 0.0
R.hip_flex_deg = lambda rig, s: 0.0
R.knee_flex_deg = lambda rig, s: 0.0
R.wrist_ext_deg = lambda rig, s: 0.0
R.elbow_flex_deg = lambda rig, s: STATE["elbow"]
R.finger_curl_deg = lambda rig, s: STATE["curl"]


class Key:
    def __init__(self, name):
        self.name, self.value = name, 0.0


class Keys(dict):
    def __iter__(self):
        return iter(list(self.values()))


def body_with(*names):
    kb = Keys({n: Key(n) for n in ("Basis",) + names})
    return types.SimpleNamespace(data=types.SimpleNamespace(shape_keys=types.SimpleNamespace(key_blocks=kb))), kb


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


FAIL = []


def check(label, got, want, tol=1e-9):
    ok = abs(got - want) <= tol
    print(f"{'ok  ' if ok else 'FAIL'} {label}: {got:.6f} (want {want:.6f})")
    if not ok:
        FAIL.append(label)


rig = {f"{R.PROP}_{s}": [153.35] for s in ("l", "r")}
rig.update({f"{R.ARMBAND_PROP}_{s}": [153.0, 20.0, 50.0] for s in ("l", "r")})
rig.update({f"{R.GRIP_PROP}_{s}": 230.0 for s in ("l", "r")})
body, kb = body_with("R121_ARM_l_153", "R121_ARM_r_153", "R121_ARMBAND_l", "R121_ARMBAND_r", "R121_GRIP_l", "R121_GRIP_r")

for elev, elbow in ((153.35, 0.0), (153.35, 14.0), (153.35, 35.0), (153.35, 50.0), (153.35, 130.0), (120.0, 0.0), (10.0, 0.0)):
    STATE.update(elev=elev, elbow=elbow)
    R.drive(rig, body)
    parent = kb["R121_ARM_l_153"].value
    check(f"lockout key at elevation {elev}", parent, smooth(1.0) if elev >= 153.35 else max(0.0, (elev - R.START) / (153.35 - R.START)))
    check(f"ARMBAND at elevation {elev}, elbow {elbow}", kb["R121_ARMBAND_l"].value, parent * (1.0 - smooth((elbow - 20.0) / 30.0)))
    check(f"ARMBAND right side equals left", kb["R121_ARMBAND_r"].value, kb["R121_ARMBAND_l"].value)

for curl, want in ((0.0, 0.0), (115.0, 0.0), (172.5, 0.5), (230.0, 1.0), (300.0, 1.0)):
    STATE.update(curl=curl)
    R.drive(rig, body)
    check(f"GRIP at finger curl {curl}", kb["R121_GRIP_l"].value, want)

# a blend without the new keys (or without their rig data) is left alone
body2, kb2 = body_with("R121_ARM_l_153", "R121_ARMBAND_l")
STATE.update(elev=153.35, elbow=0.0)
kb2["R121_ARMBAND_l"].value = 0.25
R.drive({f"{R.PROP}_l": [153.35]}, body2)
check("ARMBAND without its rig data is not driven", kb2["R121_ARMBAND_l"].value, 0.25)

print("FAILED:" if FAIL else "all checks passed", FAIL if FAIL else "")
sys.exit(1 if FAIL else 0)
