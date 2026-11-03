"""Unit test for scripts/body_v2/character_profile.py (no Blender needed).

Checks the shipped manifest and profiles, and that validate() enforces the character rules:
owner approval before approved / production-ready states, no character derived from another by scaling,
canonical bone names.
"""
import copy
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import character_profile as cp  # noqa: E402

fails = []


def check(name, ok):
    print(("PASS " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


def raises(fn):
    try:
        fn()
    except cp.ProfileError:
        return True
    return False


# shipped data
m = cp.manifest()
ids = [c["id"] for c in m["characters"]]
check("manifest lists the male and the female", {"hgpt_male_v2", "hgpt_female_v2"} <= set(ids))
check("default character is the male", m["default_character"] == "hgpt_male_v2")
male, female = cp.load("hgpt_male_v2"), cp.load("hgpt_female_v2")
check("male is a candidate, not approved", male["status"] == "candidate" and not male["owner_approvals"])
check("female is not started", female["status"] == "not_started" and not female["owner_approvals"])
check("no character is production-ready", all(cp.load(i)["status"] != "production_ready" for i in ids))
check("male Blender names unchanged", cp.blender_names("hgpt_male_v2") ==
      ("HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE", "HGPT_CANONICAL_V4_ORIGINAL"))
check("default load is the male", cp.load()["id"] == "hgpt_male_v2")
check("female has no Blender assets yet", raises(lambda: cp.blender_names("hgpt_female_v2")))
check("region value for the male leg cut", cp.region("legs_v2_blender.py", "V2_LEGS_CUT", None) == 0.45)
check("region default when absent", cp.region("legs_v2_blender.py", "V2_LEGS_CUT", 0.5, cid="hgpt_female_v2") == 0.5)
check("unknown character refused", raises(lambda: cp.load("nobody")))
for c in m["characters"]:
    check(f"approval record exists for {c['id']}", (cp.ROOT / c["approval"]).is_file())

# approval rules
others = ["hgpt_male_v2"]
base = copy.deepcopy(female)
appr = lambda what: {"date": "2026-12-01", "by": "owner", "what": what, "evidence": "review-assets/..."}


def with_(status, approvals=(), derived=None):
    p = copy.deepcopy(base)
    p["status"] = status
    p["owner_approvals"] = list(approvals)
    p["base_mesh"]["derived_from"] = derived
    return p


check("approved_appearance without approval refused", raises(lambda: cp.validate(with_("approved_appearance"), others)))
check("approved_appearance with owner approval accepted",
      not raises(lambda: cp.validate(with_("approved_appearance", [appr("appearance")]), others)))
check("approved_movement needs appearance too",
      raises(lambda: cp.validate(with_("approved_movement", [appr("movement")]), others)))
check("production_ready needs appearance, movement and production",
      raises(lambda: cp.validate(with_("production_ready", [appr("appearance"), appr("movement")]), others)))
check("production_ready with all three accepted", not raises(lambda: cp.validate(
    with_("production_ready", [appr("appearance"), appr("movement"), appr("production")]), others)))
check("approval not by the owner refused", raises(lambda: cp.validate(
    with_("approved_appearance", [dict(appr("appearance"), by="claude")]), others)))
check("approval without evidence refused", raises(lambda: cp.validate(
    with_("approved_appearance", [dict(appr("appearance"), evidence="")]), others)))
check("unknown status refused", raises(lambda: cp.validate(with_("approved"), others)))

# no scaled copies
check("female as scaled male refused", raises(lambda: cp.validate(
    with_("in_development", derived={"character": "hgpt_male_v2", "transform": "uniform scale 0.93"}), others)))
check("female from male without independent fit refused", raises(lambda: cp.validate(
    with_("in_development", derived="hgpt_male_v2"), others)))
check("independent fit flagged but scaled still refused", raises(lambda: cp.validate(
    with_("in_development", derived={"character": "hgpt_male_v2", "independent_fit": True, "method": "non-uniform scaling"}), others)))
check("shared topology re-fitted independently accepted", not raises(lambda: cp.validate(
    with_("in_development", derived={"character": "hgpt_male_v2", "independent_fit": True,
                                     "method": "topology only; re-sculpted to her own reference sheet"}), others)))
check("independent base mesh accepted", not raises(lambda: cp.validate(with_("in_development"), others)))
p = with_("in_development")
p["skeleton"]["bone_names"] = "own"
check("non-canonical bone names refused", raises(lambda: cp.validate(p, others)))

# manifest / profile status mismatch is caught
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    mm = copy.deepcopy(m)
    mm["characters"][1]["status"] = "candidate"
    (td / "manifest.json").write_text(json.dumps(mm))
    for c in m["characters"]:
        (td / c["profile"]).parent.mkdir(parents=True, exist_ok=True)
        (td / c["profile"]).write_text((cp.ROOT / c["profile"]).read_text())
    check("manifest/profile status mismatch refused", raises(lambda: cp.load("hgpt_female_v2", root=td)))

print(f"{'FAILED' if fails else 'OK'}: {len(fails)} failure(s)")
sys.exit(1 if fails else 0)
