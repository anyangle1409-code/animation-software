"""Character profiles for the Body v2 pipeline (male and female on one exercise system).

Each character (review-assets/body_v2/characters/<id>/profile.json) carries its own Blender object names, stature,
landmarks and the region values scripts used to hard-code for the male body.  New scripts, and old ones when next
touched, read them here instead of naming HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE / HGPT_CANONICAL_V4_ORIGINAL directly.
The default is the manifest's default character (the male), so existing commands behave exactly as before.

Rules enforced by validate() (docs/CHARACTER_ARCHITECTURE_MALE_FEMALE_20261103.md):
  * approved_appearance / approved_movement / production_ready need owner approval entries; production_ready needs
    both an appearance and a movement approval.  A passing test or workflow is not approval;
  * a character is never derived from another character's mesh by scaling (the female is not a scaled male);
  * bone names are the canonical set: skeletons are fitted per character, the names and conventions are shared.

No bpy import: usable from Blender scripts, tests and plain Python.
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "review-assets" / "body_v2" / "characters"
STATES = ("not_started", "in_development", "candidate", "owner_review",
          "approved_appearance", "approved_movement", "production_ready")
NEEDS_APPROVAL = {"approved_appearance": {"appearance"},
                  "approved_movement": {"appearance", "movement"},
                  "production_ready": {"appearance", "movement", "production"}}
SCALING_WORDS = ("scale", "scaled", "scaling", "resize", "shrink")


class ProfileError(ValueError):
    pass


def manifest(root=ROOT):
    return json.loads((Path(root) / "manifest.json").read_text())


def validate(p, others=()):
    """Raise ProfileError when a profile breaks the character rules; return the profile."""
    cid = p.get("id")
    if p.get("schema") != "hgpt-character-profile/1":
        raise ProfileError(f"{cid}: unknown schema {p.get('schema')!r}")
    st = p.get("status")
    if st not in STATES:
        raise ProfileError(f"{cid}: unknown status {st!r}")
    need = NEEDS_APPROVAL.get(st, set())
    have = set()
    for a in p.get("owner_approvals") or []:
        if not (a.get("date") and a.get("by") and a.get("what") and a.get("evidence")):
            raise ProfileError(f"{cid}: an owner approval entry needs date, by, what and evidence: {a}")
        if a.get("by") != "owner":
            raise ProfileError(f"{cid}: approvals are recorded only for the owner, not {a.get('by')!r}")
        have.add(a["what"])
    if need - have:
        raise ProfileError(f"{cid}: status {st!r} needs owner approval of {sorted(need - have)}; has {sorted(have)}")
    # A base mesh may start from a shared topology or another character's mesh only as an independent re-fit to this
    # character's own references (declared with independent_fit: true); scaling another character is refused.
    src = (p.get("base_mesh") or {}).get("derived_from")
    if src:
        other = src.get("character") if isinstance(src, dict) else str(src)
        scaled = any(w in json.dumps(src).lower() for w in SCALING_WORDS)
        independent = isinstance(src, dict) and src.get("independent_fit") is True
        if other in others and (scaled or not independent):
            raise ProfileError(f"{cid}: base mesh derived from {other!r} ({src}); each character is built "
                               "independently, never by scaling another character's mesh")
    if (p.get("skeleton") or {}).get("bone_names") != "canonical":
        raise ProfileError(f"{cid}: skeleton.bone_names must be 'canonical' (shared names, per-character fit)")
    return p


def load(cid=None, root=ROOT):
    """The profile of character `cid` (default: $V2_CHARACTER, else the manifest's default), validated."""
    m = manifest(root)
    cid = cid or os.environ.get("V2_CHARACTER") or m["default_character"]
    ids = [c["id"] for c in m["characters"]]
    entry = next((c for c in m["characters"] if c["id"] == cid), None)
    if entry is None:
        raise ProfileError(f"unknown character {cid!r}; known: {ids}")
    p = json.loads((Path(root) / entry["profile"]).read_text())
    if p.get("id") != cid:
        raise ProfileError(f"{entry['profile']} holds {p.get('id')!r}, expected {cid!r}")
    if p.get("status") != entry.get("status"):
        raise ProfileError(f"{cid}: manifest status {entry.get('status')!r} != profile status {p.get('status')!r}")
    return validate(p, others=[i for i in ids if i != cid])


def blender_names(cid=None, root=ROOT):
    """(body object name, rig object name) for character `cid`; raises when the character has no Blender assets."""
    p = load(cid, root)
    b = p.get("blender") or {}
    if not (b.get("body_object") and b.get("rig_object")):
        raise ProfileError(f"{p['id']}: no Blender assets yet (status {p['status']!r})")
    return b["body_object"], b["rig_object"]


def region(script, key, default, cid=None, root=ROOT):
    """A region value a script used to hard-code, from the character's profile, else `default`."""
    return (load(cid, root).get("regions") or {}).get(script, {}).get(key, default)


if __name__ == "__main__":
    for c in manifest()["characters"]:
        p = load(c["id"])
        print(c["id"], p["sex"], p["status"], (p.get("blender") or {}).get("body_object"))
