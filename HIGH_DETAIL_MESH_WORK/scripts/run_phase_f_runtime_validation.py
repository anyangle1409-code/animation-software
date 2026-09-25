"""Validate a Phase F source-rig candidate through the latest real-character retarget path.

Creates a detached worktree of the newest chatgpt/absolute-retarget-imports,
runs the clean source suite, then compares the accepted reference character and
Phase F candidate on every character-dependent integration gate listed here.

No source merge or production-asset modification occurs.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parent
SOURCE_BRANCH="chatgpt/absolute-retarget-imports"
WORKTREE=REPO.parent/f"{REPO.name}-phase-f-runtime-validation"

FILES=[
    "src/exercises/equipmentClearance.test.ts",
    "src/exercises/selfCollision.test.ts",
    "src/exercises/families/lunge.test.ts",
    "src/exercises/families/rotation.test.ts",
    "src/exercises/families/trunkFlexion.test.ts",
    "src/retargeting/mirroredHands.test.ts",
    "src/retargeting/palmMapping.test.ts",
    "src/retargeting/realCharacterDiagnostic.test.ts",
    "src/retargeting/unmappedBones.test.ts",
]

def run(cmd,cwd,env=None,check=True,log=None):
    print("+"," ".join(str(x) for x in cmd),flush=True)
    p=subprocess.run([str(x) for x in cmd],cwd=cwd,env=env,
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,
        encoding="utf-8",errors="replace")
    sys.stdout.write(p.stdout)
    if log:
        Path(log).parent.mkdir(parents=True,exist_ok=True)
        Path(log).write_text(p.stdout,encoding="utf-8")
    if check and p.returncode:
        raise subprocess.CalledProcessError(p.returncode,cmd)
    return p

def git(*args,check=True):
    return run(["git",*args],REPO,check=check)

def resolve_source():
    fetched=git("fetch","origin",SOURCE_BRANCH,check=False)
    ref="FETCH_HEAD" if fetched.returncode==0 else f"origin/{SOURCE_BRANCH}"
    sha=subprocess.check_output(["git","rev-parse",ref],cwd=REPO,text=True).strip()
    message=subprocess.check_output(["git","show","-s","--format=%s",sha],cwd=REPO,text=True).strip()
    return ref,sha,message,fetched.returncode

def remove_worktree():
    if WORKTREE.exists():
        git("worktree","remove","--force",str(WORKTREE),check=False)
        if WORKTREE.exists():shutil.rmtree(WORKTREE,ignore_errors=True)

def link_dependencies():
    target=WORKTREE/"node_modules";source=REPO/"node_modules"
    if target.exists():return "existing"
    if source.is_dir():
        try:
            if os.name=="nt":
                p=subprocess.run(["cmd","/c","mklink","/J",str(target),str(source)],
                    cwd=WORKTREE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
                if p.returncode==0:return "junction-to-primary-node_modules"
            else:
                target.symlink_to(source,target_is_directory=True);return "symlink-to-primary-node_modules"
        except OSError:
            pass
    run(["npm","ci"],WORKTREE)
    return "npm-ci"

def vitest_cmd():
    local=WORKTREE/"node_modules"/".bin"/("vitest.cmd" if os.name=="nt" else "vitest")
    return [str(local),"run"] if local.is_file() else ["npx","--no-install","vitest","run"]

def test_counts(text):
    clean=re.sub(r"\x1b\[[0-9;]*m","",text)
    lines=[x for x in clean.splitlines() if "Tests" in x]
    line=lines[-1] if lines else ""
    def n(label):
        m=re.search(r"(\d+)\s+"+label,line)
        return int(m.group(1)) if m else 0
    return {"failed":n("failed"),"passed":n("passed"),"skipped":n("skipped"),"line":line.strip()}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--reference",type=Path,required=True)
    ap.add_argument("--candidate",type=Path,required=True)
    ap.add_argument("--label",default="phase_f")
    ap.add_argument("--keep-worktree",action="store_true")
    ap.add_argument("--skip-full-suite",action="store_true")
    args=ap.parse_args()
    reference=args.reference.resolve();candidate=args.candidate.resolve()
    for p in (reference,candidate):
        if not p.is_file():raise SystemExit(f"Missing GLB: {p}")

    out=ROOT/"reports"/f"phase_f_runtime_{args.label}"
    out.mkdir(parents=True,exist_ok=True)
    ref,sha,message,fetch_code=resolve_source()
    remove_worktree()
    git("worktree","add","--detach",str(WORKTREE),sha)

    try:
        dep=link_dependencies();runner=vitest_cmd()
        suite=None
        if not args.skip_full_suite:
            p=run(["npm","test"],WORKTREE,check=False,log=out/"full_source_suite.log")
            suite={"returncode":p.returncode,"tests":test_counts(p.stdout)}
            if p.returncode:
                raise SystemExit("Latest source full suite is not clean; see full_source_suite.log")

        results={}
        for file in FILES:
            per={}
            for name,glb in (("reference",reference),("candidate",candidate)):
                env=os.environ.copy();env["REAL_CHARACTER_GLB"]=str(glb)
                p=run(runner+[file],WORKTREE,env=env,check=False,
                      log=out/f"{name}__{Path(file).stem}.log")
                per[name]={"returncode":p.returncode,"tests":test_counts(p.stdout)}
            results[file]=per

        new_failing=[
            file for file,x in results.items()
            if x["reference"]["returncode"]==0 and x["candidate"]["returncode"]!=0
        ]
        increased_failures=[
            file for file,x in results.items()
            if x["candidate"]["tests"]["failed"]>x["reference"]["tests"]["failed"]
        ]

        # Also run the current mesh-coordination group as a single reportable set.
        combined={}
        for name,glb in (("reference",reference),("candidate",candidate)):
            env=os.environ.copy();env["REAL_CHARACTER_GLB"]=str(glb)
            p=run(runner+FILES,WORKTREE,env=env,check=False,log=out/f"{name}_combined.log")
            combined[name]={"returncode":p.returncode,"tests":test_counts(p.stdout)}

        passed=not new_failing and not increased_failures
        report={
            "reference":str(reference),
            "candidate":str(candidate),
            "label":args.label,
            "source_branch":SOURCE_BRANCH,
            "source_head":sha,
            "source_commit_message":message,
            "fetch_returncode":fetch_code,
            "dependency_mode":dep,
            "full_suite":suite,
            "per_file":results,
            "combined":combined,
            "new_failing_gate_files":new_failing,
            "gate_files_with_increased_failed_test_count":increased_failures,
            "runtime_no_regression":passed,
            "required_manual_reads":[
                "candidate__palmMapping.test.log",
                "candidate__unmappedBones.test.log",
                "candidate__realCharacterDiagnostic.test.log",
                "candidate__mirroredHands.test.log",
            ],
            "note":(
                "This validates the source-rig character through the canonical retarget runtime. "
                "The raw Phase F asset audit remains a separate prerequisite."
            ),
        }
        (out/"runtime_report.json").write_text(json.dumps(report,indent=2))
        print(json.dumps(report,indent=2))
        if not passed:raise SystemExit(1)
    finally:
        if not args.keep_worktree:remove_worktree()

if __name__=="__main__":
    main()
