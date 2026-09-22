"""Build an isolated local validation copy from the pinned repository files."""

import hashlib
import json
import os
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
repository = Path(os.environ["CANDIDATE_REPO_ROOT"]).resolve() if "CANDIDATE_REPO_ROOT" in os.environ else root.parent
snapshot = root / "reference/anyangle1409-code-animation-software-f9cca7c"
hashes = json.loads((root / "reports/reference_hashes.json").read_text())

for relative_name, expected_hash in hashes.items():
    relative = Path(relative_name)
    source = repository / relative
    if not source.is_file():
        raise FileNotFoundError(f"Pinned source file missing: {source}")
    actual_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    if actual_hash != expected_hash:
        raise ValueError(f"Pinned source changed: {relative_name}")
    destination = snapshot / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file():
        if hashlib.sha256(destination.read_bytes()).hexdigest() != expected_hash:
            raise ValueError(f"Local reference differs: {destination}")
    else:
        shutil.copyfile(source, destination)

validation = root / "validation"
validation.mkdir(exist_ok=True)
for relative_name in ("package.json", "package-lock.json", "tsconfig.json", "vite.config.ts"):
    destination = validation / relative_name
    if not destination.exists():
        shutil.copyfile(snapshot / relative_name, destination)

for source in (snapshot / "src").rglob("*"):
    if not source.is_file():
        continue
    destination = validation / "src" / source.relative_to(snapshot / "src")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        shutil.copyfile(source, destination)

handoff = snapshot / "HOME_GYM_PT_GPT_MESH_HANDOFF"
for source in (handoff / "harnesses").glob("*"):
    if not source.is_file():
        continue
    destination = validation / "scratchpad/repair" / source.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        shutil.copyfile(source, destination)

print(f"Verified and copied {len(hashes)} pinned files into {snapshot}")
print(f"Validation copy ready at {validation}; install its package dependencies before running tests")

