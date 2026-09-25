"""Final isolated acceptance runner for the self-sufficient exercise studio.

Usage:
  python scripts/run_final_system_acceptance.py final_character.glb
  python scripts/run_final_system_acceptance.py final_character.glb --allow-blocked

No merge, promotion or production-asset edit is performed.
"""
from __future__ import annotations

import argparse
import hashlib
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
WORKTREE=REPO.parent/f"{REPO.name}-final-system-acceptance"
MANIFEST=ROOT/"PROMPT_FAMILY_CERTIFICATION_MANIFEST.json"

CHARACTER_TESTS=[
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
GENERATOR_TESTS=[
    "src/generation/parse.test.ts",
    "src/generation/generate.test.ts",
]

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def clean_ansi(text):
    return re.sub(r"\x1b\[[0-9;]*m","",text)

def test_counts(text):
    clean=clean_ansi(text)
    lines=[line for line in clean.splitlines() if "Tests" in line]
    line=lines[-1] if lines else ""
    def n(label):
        m=re.search(r"(\d+)\s+"+label,line)
        return int(m.group(1)) if m else 0
    return {"failed":n("failed"),"passed":n("passed"),"skipped":n("skipped"),"line":line.strip()}

def run(cmd,cwd,env=None,check=False,log=None):
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

def git(*args,check=False):
    return run(["git",*args],REPO,check=check)

def resolve_source():
    fetched=git("fetch","origin",SOURCE_BRANCH)
    if fetched.returncode==0:
        ref="FETCH_HEAD"
    else:
        remote=f"origin/{SOURCE_BRANCH}"
        probe=subprocess.run(["git","rev-parse","--verify",remote],cwd=REPO,
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        ref=remote if probe.returncode==0 else SOURCE_BRANCH
    sha=subprocess.check_output(["git","rev-parse",ref],cwd=REPO,text=True).strip()
    message=subprocess.check_output(["git","show","-s","--format=%s",sha],cwd=REPO,text=True).strip()
    return ref,sha,message,fetched.returncode

def remove_worktree():
    if WORKTREE.exists():
        git("worktree","remove","--force",str(WORKTREE))
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
                target.symlink_to(source,target_is_directory=True)
                return "symlink-to-primary-node_modules"
        except OSError:
            pass
    p=run(["npm","ci"],WORKTREE,log=None)
    if p.returncode:raise SystemExit("npm ci failed in final acceptance worktree")
    return "npm-ci"

def vitest_cmd():
    local=WORKTREE/"node_modules"/".bin"/("vitest.cmd" if os.name=="nt" else "vitest")
    return [str(local),"run"] if local.is_file() else ["npx","--no-install","vitest","run"]

def write_markdown(report,out):
    lines=[
        "# Final system acceptance",
        "",
        f"**Result:** {'PASS' if report['pass'] else 'FAIL'}",
        "",
        "## Frozen inputs",
        f"- final character: {report['character']['path']}",
        f"- character SHA-256: {report['character']['sha256']}",
        f"- source branch: {report['source']['branch']}",
        f"- source HEAD: {report['source']['head']}",
        f"- source commit: {report['source']['message']}",
        "",
        "## Prompt family certification",
        f"- certified: {report['prompt_certification']['certified']}",
        f"- unresolved: {report['prompt_certification']['unresolved']}",
        f"- allow blocked: {report['prompt_certification']['allow_blocked']}",
        "",
        "## Stages",
    ]
    for name,item in report["stages"].items():
        lines.append(
            f"- {'PASS' if item.get('pass') else 'FAIL'} — {name}"
            + (f" — tests {item['tests']}" if item.get("tests") else "")
        )
    if report["failures"]:
        lines += ["","## Failures"]
        lines += [f"- {x}" for x in report["failures"]]
    lines += [
        "",
        "## Interpretation",
        "A PASS proves the integrated current release target against the exact source HEAD and character hash above.",
        "It does not certify exercises outside the declared family/equipment model.",
        "Generated candidates remain review-only until explicitly promoted.",
    ]
    out.write_text("\n".join(lines)+"\n",encoding="utf-8")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("character",type=Path)
    ap.add_argument("--allow-blocked",action="store_true")
    ap.add_argument("--keep-worktree",action="store_true")
    args=ap.parse_args()
    character=args.character.resolve()
    if not character.is_file():raise SystemExit(f"Missing final character: {character}")
    if not MANIFEST.is_file():raise SystemExit(f"Missing prompt certification manifest: {MANIFEST}")

    manifest=json.loads(MANIFEST.read_text())
    certified=sorted(f["id"] for f in manifest["families"] if f["status"]=="CERTIFIED")
    unresolved=[
        {"id":f["id"],"status":f["status"]}
        for f in manifest["families"] if f["status"]!="CERTIFIED"
    ]

    out=ROOT/"reports"/"final_system_acceptance"
    out.mkdir(parents=True,exist_ok=True)
    report={
        "character":{"path":str(character),"sha256":sha256(character)},
        "source":{"branch":SOURCE_BRANCH,"head":None,"message":None},
        "prompt_certification":{
            "certified":certified,
            "unresolved":unresolved,
            "allow_blocked":args.allow_blocked,
        },
        "dependency_mode":None,
        "stages":{},
        "failures":[],
        "pass":False,
    }

    invalid_status=[x for x in unresolved if x["status"] not in {"BLOCKED"}]
    if unresolved and not args.allow_blocked:
        report["failures"].append(
            "Not all prompt families are CERTIFIED: "
            +", ".join(f"{x['id']}={x['status']}" for x in unresolved)
        )
    elif invalid_status:
        report["failures"].append(
            "--allow-blocked permits only explicit BLOCKED families, not: "
            +", ".join(f"{x['id']}={x['status']}" for x in invalid_status)
        )

    # Certification is a cheap prerequisite. Do not spend a fresh source
    # checkout/full-suite run when the declared release scope is already known
    # to be incomplete.
    if report["failures"]:
        json_path=out/"FINAL_SYSTEM_ACCEPTANCE.json"
        md_path=ROOT/"FINAL_SYSTEM_ACCEPTANCE.md"
        json_path.write_text(json.dumps(report,indent=2),encoding="utf-8")
        write_markdown(report,md_path)
        print(md_path.read_text())
        raise SystemExit(1)

    ref,sha,message,fetch_code=resolve_source()
    report["source"].update({"resolved_ref":ref,"head":sha,"message":message,"fetch_returncode":fetch_code})
    remove_worktree()
    git("worktree","add","--detach",str(WORKTREE),sha,check=True)

    try:
        report["dependency_mode"]=link_dependencies()
        runner=vitest_cmd()

        def stage(name,cmd,env=None,is_tests=False):
            log=out/(re.sub(r"[^a-z0-9]+","_",name.lower()).strip("_")+".log")
            p=run(cmd,WORKTREE,env=env,log=log)
            item={"returncode":p.returncode,"log":str(log.relative_to(ROOT))}
            if is_tests:item["tests"]=test_counts(p.stdout)
            item["pass"]=p.returncode==0
            report["stages"][name]=item
            if p.returncode:
                report["failures"].append(f"{name} failed; see {log.relative_to(ROOT)}")
            return p

        stage("source suite — normal reference",["npm","test"],is_tests=True)
        stage("typecheck",["npm","run","typecheck"])
        stage("production build",["npm","run","build"])

        final_env=os.environ.copy()
        final_env["REAL_CHARACTER_GLB"]=str(character)
        stage("source suite — final character",["npm","test"],env=final_env,is_tests=True)
        stage("prompt parser/generator tests",runner+GENERATOR_TESTS,env=final_env,is_tests=True)
        stage("focused final-character integration",runner+CHARACTER_TESTS,env=final_env,is_tests=True)

        coverage_path=out/"prompt_generation_coverage.json"
        coverage=run([
            sys.executable,
            ROOT/"scripts"/"audit_prompt_generation_coverage.py",
            "--source-root",str(WORKTREE),
            "--report",str(coverage_path),
        ],ROOT,log=out/"prompt_generation_coverage.log")
        report["stages"]["prompt family coverage"]={
            "returncode":coverage.returncode,
            "log":str((out/"prompt_generation_coverage.log").relative_to(ROOT)),
            "report":str(coverage_path.relative_to(ROOT)),
            "pass":coverage.returncode==0,
        }
        if coverage.returncode:
            report["failures"].append("Prompt family coverage audit failed.")

        report["pass"]=not report["failures"] and all(x.get("pass") for x in report["stages"].values())
    finally:
        json_path=out/"FINAL_SYSTEM_ACCEPTANCE.json"
        md_path=ROOT/"FINAL_SYSTEM_ACCEPTANCE.md"
        json_path.write_text(json.dumps(report,indent=2),encoding="utf-8")
        write_markdown(report,md_path)
        print(md_path.read_text())
        if not args.keep_worktree:remove_worktree()

    if not report["pass"]:raise SystemExit(1)

if __name__=="__main__":
    main()
