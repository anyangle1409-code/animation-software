"""Export a versioned V15 dressed GLB using the proven stable-ID hand packer."""
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

def run(cmd, env=None):
    print("+", " ".join(str(x) for x in cmd), flush=True)
    subprocess.run([str(x) for x in cmd], cwd=ROOT, env=env, check=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default=DEFAULT_VERSION)
    args = ap.parse_args()
    version = args.version

    blend = ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.blend"
    export_blend = ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}_EXPORT.blend"
    target = ROOT / f"HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_{version}.glb"
    report = ROOT / "reports" / f"build_{version}_glb.json"

    if not blend.is_file():
        raise SystemExit(f"Missing saved V15 Blend: {blend}")
    if target.exists():
        raise SystemExit(
            f"Refusing to overwrite existing {target.name}. "
            "Preserve the attempt and use a new candidate version if rebuilding."
        )

    exe = find_blender()

    run([
        exe, "--background", "--factory-startup",
        "--python", ROOT / "scripts" / "audit_v15_hand_blender.py",
        "--", str(blend),
    ])

    if export_blend.exists():
        export_blend.unlink()
    run([
        exe, "--background", "--factory-startup",
        "--python", ROOT / "scripts" / "prepare_v15_export_blender.py",
        "--", str(blend), str(export_blend),
    ])

    env = os.environ.copy()
    env["BLEND"] = str(export_blend)
    env["TARGET"] = str(target)
    env["REPORT"] = str(report)
    try:
        run([
            exe, "--background", "--factory-startup",
            "--python", ROOT / "scripts" / "pack_v11_hand_glb.py",
        ], env=env)
    finally:
        if export_blend.exists():
            export_blend.unlink()

    print("\nV15 DRESSED GLB EXPORTED:", target)
    print("Editable V15 Blend was not triangulated or otherwise altered by export prep.")
    print("Bare variant will be created by the finish workflow.")

if __name__ == "__main__":
    main()
