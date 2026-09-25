"""Create (if needed) and open a versioned prepared V15 hand candidate in Blender."""
from __future__ import annotations

import argparse
import glob
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VERSION = "v15a_deep_hand_rebuild"

def find_blender():
    explicit = os.environ.get("BLENDER_EXE")
    if explicit and Path(explicit).is_file():
        return explicit
    found = shutil.which("blender")
    if found:
        return found
    if os.name == "nt":
        hits = sorted(
            glob.glob(r"C:\Program Files\Blender Foundation\Blender *\blender.exe"),
            reverse=True,
        )
        if hits:
            return hits[0]
    raise SystemExit("Blender not found. Set BLENDER_EXE or add Blender to PATH.")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default=DEFAULT_VERSION)
    args = ap.parse_args()
    version = args.version
    out = ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.blend"

    # Fail before launching Blender if the branch, baselines, helper syntax or
    # local toolchain are not the expected V15 workspace.
    subprocess.run([
        sys.executable, ROOT / "scripts" / "preflight_v15.py",
    ], cwd=ROOT, check=True)

    exe = find_blender()

    if not out.is_file():
        env = os.environ.copy()
        env["V15_VERSION"] = version
        subprocess.run([
            exe, "--background", "--factory-startup",
            "--python", ROOT / "scripts" / "prepare_v15_deep_hand_blender.py",
        ], cwd=ROOT, env=env, check=True)

    if not out.is_file():
        raise SystemExit(f"V15 preparation did not create {out}")

    print("Opening prepared V15 candidate:", out, flush=True)
    subprocess.Popen([
        exe, str(out),
        "--python", str(ROOT / "scripts" / "register_v15_blender_tools.py"),
    ], cwd=ROOT)

if __name__ == "__main__":
    main()
