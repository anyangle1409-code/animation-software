"""Create a new editable candidate Blender file from reviewed V6.

This does not create a git branch, alter V6, or export/promote anything. It
uses the V6 review-region tagging helper so the working .blend starts with
AUDIT_* selection groups.

Usage:
    python scripts/start_candidate.py --version v7_knee_retopology
"""

from __future__ import annotations
import argparse,glob,hashlib,json,os,shutil,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v6_knee_seam.blend"

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def find_blender():
    explicit=os.environ.get("BLENDER_EXE")
    if explicit and Path(explicit).is_file():return explicit
    found=shutil.which("blender")
    if found:return found
    if os.name=="nt":
        matches=sorted(glob.glob(r"C:\Program Files\Blender Foundation\Blender *\blender.exe"),reverse=True)
        if matches:return matches[0]
    return None

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--version",required=True);args=ap.parse_args()
    version=args.version.strip()
    if not version or any(c in version for c in r'\/:*?"<>| '):
        raise SystemExit("Use a simple version suffix such as v7_knee_retopology")
    target=ROOT/f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.blend"
    if target.exists():
        raise SystemExit(f"Refusing to overwrite existing candidate: {target}")
    blender=find_blender()
    if not blender:raise SystemExit("Blender not found. Set BLENDER_EXE or add Blender to PATH.")
    helper=ROOT/"scripts"/"tag_v6_review_regions.py"
    subprocess.run([blender,"--background","--factory-startup","--python",str(helper),"--",str(BASE),str(target)],cwd=ROOT,check=True)
    report={
      "version":version,
      "base":BASE.name,
      "base_sha256":digest(BASE),
      "candidate_blend":target.name,
      "candidate_sha256":digest(target),
      "note":"AUDIT_* groups are selection helpers only; candidate remains review-only."
    }
    out=ROOT/"reports"/f"start_{version}.json";out.write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    print("\nOpen this in Blender:",target)

if __name__=="__main__":
    main()
