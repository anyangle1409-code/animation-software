"""Run candidate-only validation against the frozen 63-bone source baseline.

Run from HIGH_DETAIL_MESH_WORK:
    python scripts/run_candidate_gates.py --version v7_example

The exact source commit is 19ca602 (hgpt_canonical_v3). The source is extracted
into validation_63 without merging it into the mesh-review branch.
"""

from __future__ import annotations
import argparse,os,shutil,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VALIDATION=ROOT/"validation_63"
REPAIR=VALIDATION/"scratchpad"/"repair"
RIG_SHA="19ca602ca2f2a821237dcf5b1b50c7906d86b0fe"

GUARDS=[
 "sagittal.test.mts",
 "dressed_equivalence.test.mts",
 "gripmetric.test.mts",
 "overlap.test.mts",
 "gripagree.test.mts",
]

def run(cmd,cwd=None,env=None,log=None):
    print("+"," ".join(str(x) for x in cmd),flush=True)
    proc=subprocess.Popen([str(x) for x in cmd],cwd=str(cwd) if cwd else None,env=env,
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors="replace")
    chunks=[]
    assert proc.stdout is not None
    for line in proc.stdout:
        print(line,end="");chunks.append(line)
    code=proc.wait()
    if log:
        log.parent.mkdir(parents=True,exist_ok=True);log.write_text("".join(chunks))
    if code:raise SystemExit(code)

def ensure_rig63_source():
    marker=VALIDATION/".rig_source_commit"
    if not marker.is_file() or marker.read_text().strip()!=RIG_SHA:
        run([sys.executable,ROOT/"scripts"/"prepare_rig63_validation.py"],cwd=ROOT)
    if not (VALIDATION/"src"/"rig"/"frozen.test.ts").is_file():
        raise SystemExit("validation_63 is not the frozen 63-bone source")

def vitest_command():
    local=VALIDATION/"node_modules"/".bin"/("vitest.cmd" if os.name=="nt" else "vitest")
    if local.is_file():return [str(local),"run"]
    pnpm=shutil.which("pnpm")
    if pnpm:return [pnpm,"exec","vitest","run"]
    npx=shutil.which("npx")
    if npx:return [npx,"--no-install","vitest","run"]
    raise SystemExit("Vitest is unavailable in validation_63")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--version",required=True)
    ap.add_argument("--task",choices=("knee","hand","material","shoulder"),default="knee")
    ap.add_argument("--skip-exercise",action="store_true")
    args=ap.parse_args()
    version=args.version
    dressed=ROOT/f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.glb"
    bare=ROOT/f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}_BARE.glb"
    if not dressed.is_file():raise SystemExit(f"Missing candidate: {dressed}")
    if not bare.is_file():raise SystemExit(f"Missing bare candidate: {bare}")

    quick=[sys.executable,ROOT/"scripts"/"candidate_quick_check.py",dressed]
    if args.task=="material":quick.append("--allow-materials")
    run(quick,cwd=ROOT)
    ensure_rig63_source()

    for name in GUARDS+["vitest.config.mts","review_v3.test.mts"]:
        if not (REPAIR/name).is_file():raise SystemExit(f"Missing rig-63 harness: {REPAIR/name}")

    config=REPAIR/"vitest.config.mts"
    runner=vitest_command()
    env=os.environ.copy()
    env.update({
      "GLB":str(dressed.resolve()),
      "ASSETS":str(dressed.resolve()),
      "DRESSED":str(dressed.resolve()),
      "BARE":str(bare.resolve()),
      "CANDIDATE_VERSION":version,
    })

    guard_files=[str((REPAIR/name).relative_to(VALIDATION)) for name in GUARDS]
    run(runner+["--config",str(config.relative_to(VALIDATION)),*guard_files],
        cwd=VALIDATION,env=env,log=ROOT/"reports"/f"{version}_rig63_guards.log")

    if not args.skip_exercise:
        review=str((REPAIR/"review_v3.test.mts").relative_to(VALIDATION))
        run(runner+["--config",str(config.relative_to(VALIDATION)),review],
            cwd=VALIDATION,env=env,log=ROOT/"reports"/f"{version}_rig63_exercises.log")

    print("\nCANDIDATE GATES PASS AGAINST",RIG_SHA)
    print("skeleton: hgpt_canonical_v3 / 63 bones")
    print("guards:",ROOT/"reports"/f"{version}_rig63_guards.log")
    if not args.skip_exercise:print("exercises:",ROOT/"reports"/f"{version}_rig63_exercises.log")

if __name__=="__main__":
    main()
