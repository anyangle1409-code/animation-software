"""Prepare isolated validation from frozen 63-bone canonical source."""

from __future__ import annotations
import io,json,os,shutil,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parent
TARGET=ROOT/"validation_63"
LEGACY=ROOT/"validation"
RIG_SHA="614033b256d869230ea273522620467401b0bc71"
MARKER=TARGET/".rig_source_commit"
ARCHIVE_CANDIDATES=[
 "src","package.json","package-lock.json","pnpm-lock.yaml","tsconfig.json","vite.config.ts",
 "HOME_GYM_PT_GPT_MESH_HANDOFF/harnesses",
]

def git(*args,check=True,capture=True):
    kwargs=dict(cwd=REPO,check=check)
    if capture:kwargs.update(stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    return subprocess.run(["git",*args],**kwargs)

def has_commit():
    return git("cat-file","-e",f"{RIG_SHA}^{{commit}}",check=False).returncode==0

def ensure_commit():
    if has_commit():return
    print("current v3 runtime source commit not present locally; fetching source branch...")
    fetch=git("fetch","origin","chatgpt/absolute-retarget-imports",check=False,capture=False)
    if fetch.returncode!=0 or not has_commit():
        raise SystemExit("Could not obtain current v3 runtime source commit. Fetch origin/chatgpt/absolute-retarget-imports and rerun.")

def exists_at_commit(path):
    return git("cat-file","-e",f"{RIG_SHA}:{path}",check=False).returncode==0

def extract_source():
    paths=[p for p in ARCHIVE_CANDIDATES if exists_at_commit(p)]
    if "src" not in paths or "package.json" not in paths:raise SystemExit("Current v3 runtime source missing required paths")
    blob=subprocess.check_output(["git","archive","--format=tar",RIG_SHA,*paths],cwd=REPO)
    if TARGET.exists():shutil.rmtree(TARGET)
    TARGET.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(blob),mode="r:") as archive:archive.extractall(TARGET)

def copy_review_harness():
    source=LEGACY/"scratchpad"/"repair"/"review_v3.test.mts"
    if not source.is_file():raise SystemExit(f"Missing mesh review harness: {source}")
    repair=TARGET/"scratchpad"/"repair";repair.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,repair/source.name)
    harness=TARGET/"HOME_GYM_PT_GPT_MESH_HANDOFF"/"harnesses"
    for name in ("sagittal.test.mts","dressed_equivalence.test.mts","gripmetric.test.mts","overlap.test.mts","gripagree.test.mts","vitest.config.mts"):
        src=harness/name
        if not src.is_file():raise SystemExit(f"Missing rig-63 harness: {src}")
        shutil.copyfile(src,repair/name)

def same_package():
    old=LEGACY/"package.json";new=TARGET/"package.json"
    return old.is_file() and new.is_file() and json.loads(old.read_text())==json.loads(new.read_text())

def deps():
    target_modules=TARGET/"node_modules";old_modules=LEGACY/"node_modules"
    if target_modules.exists():return
    if old_modules.is_dir() and same_package():
        try:
            if os.name=="nt":
                r=subprocess.run(["cmd","/c","mklink","/J",str(target_modules),str(old_modules.resolve())],cwd=TARGET,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
                if r.returncode==0 and target_modules.exists():
                    print("Reused validation node_modules via junction");return
            else:
                target_modules.symlink_to(old_modules.resolve(),target_is_directory=True);return
        except Exception as exc:print("Could not reuse node_modules:",exc)
    npm=shutil.which("npm")
    if not npm:raise SystemExit("No reusable node_modules and npm unavailable")
    subprocess.run([npm,"ci"],cwd=TARGET,check=True)

def main():
    ensure_commit()
    if MARKER.is_file() and MARKER.read_text().strip()==RIG_SHA and (TARGET/"src"/"rig"/"frozen.test.ts").is_file():
        print("validation_63 already prepared at",RIG_SHA);deps();return
    extract_source();copy_review_harness();MARKER.write_text(RIG_SHA+"\n");deps()
    print("Prepared isolated v3 validation source:",TARGET)
    print("Source commit:",RIG_SHA)

if __name__=="__main__":main()
