"""Fast laptop resume preflight for the isolated high-detail mesh workspace."""

from __future__ import annotations
import glob,hashlib,json,os,shutil,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parent
RIG_SHA="614033b256d869230ea273522620467401b0bc71"
EXPECTED={
 "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam.glb":"ff39e07735697d5423968a8ec1c05f2c6c68fced0d757ea1b4047096bc7a5306",
 "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam_BARE.glb":"0170b3673d7a050e8aacd2683347cfa6dd000719dba0a6862c16bd7a4a5723e0",
 "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam.blend":"2a2d0326129ce5c2555c596a49a281d655f33acfd7bbd9514cad3e759586a0df",
 "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.glb":"a7655f689e141686bbbbb146826bc78121edbe8edbb57f3152b5d5978bc756cb",
 "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy_BARE.glb":"1edb5f37a89e782b35ad82696892932edbb8b51da7f8484f1e7838b7d8d890b1",
 "HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v8_knee_anatomy.blend":"704cb5f9bf1ef53a4c1bda1100f261844d8153034b18ef2ad045a75adb37c9ef",
}
REQUIRED=[
 "CURRENT_STATE.md","RIG_63_FREEZE.md","LAPTOP_CONTINUATION_HANDOFF.md","NEXT_ACTION.md",
 "REVIEW_V6_KNEE_SEAM.md","reports/final_integrity_v6_knee_seam.json",
 "reports/hand_contact_guard_v5.json","scripts/prepare_rig63_validation.py",
 "scripts/run_candidate_gates.py","scripts/finish_candidate.py"
]

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def git_ok(*args):
    return subprocess.run(["git",*args],cwd=REPO,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0

errors=[]
print("HOME GYM PT mesh-work preflight")
print("="*34)
for relative in REQUIRED:
    if not (ROOT/relative).is_file():errors.append(f"missing required file: {relative}")
for name,expected in EXPECTED.items():
    path=ROOT/name
    if not path.is_file():errors.append(f"missing preserved/accepted baseline artifact: {name}");continue
    actual=sha256(path);print(f"{'OK' if actual==expected else 'MISMATCH':8} {name}")
    if actual!=expected:errors.append(f"hash mismatch: {name}")

print("Current v3 runtime source local:", "YES" if git_ok("cat-file","-e",f"{RIG_SHA}^{{commit}}") else "NO (resume will fetch it)")
integrity=ROOT/"reports/final_integrity_v6_knee_seam.json"
if integrity.is_file():
    data=json.loads(integrity.read_text())
    print("V6 body:",data.get("body_vertices"),"vertices /",data.get("body_triangles"),"triangles")

blender=os.environ.get("BLENDER_EXE") or shutil.which("blender")
if not blender and os.name=="nt":
    matches=sorted(glob.glob(r"C:\Program Files\Blender Foundation\Blender *\blender.exe"),reverse=True)
    blender=matches[0] if matches else None
print("Blender:",blender or "not found; set BLENDER_EXE")

if errors:
    print("\nPRE-FLIGHT FAILED")
    for error in errors:print("-",error)
    raise SystemExit(1)
print("\nPRE-FLIGHT PASS")
