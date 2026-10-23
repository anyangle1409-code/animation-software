#!/usr/bin/env bash
# Rebuild W8/v13s, v14 (v14b: legs + feet + torso) and, SEPARATELY, the experimental R120, then verify and hash.
#
#   scripts/body_v2/rebuild_w8_v14_verified.sh <OUTROOT> [--skip-r120]
#
# Safety:  OUTROOT must not exist (nothing is ever overwritten).  Every output is made read-only at the end.
#          No existing .blend, ORIGINAL_v1, production asset or skeleton file is opened for writing; the Blender
#          scripts only read R41 and write copies under OUTROOT.  PT_MODEL_VERSION is not touched.
# Needs:   Python 3.13 with bpy 5.2 (the wheel), numpy, scipy, scikit-image, lazy_loader, packaging, Pillow; git.
#          Set PY=/path/to/python if it is not `python3.13`.  ~45 min on a laptop (15 W8 + 10 v14 + 15 R120).
# STATUS:  `bash -n` checked only.  Never executed end to end - the session that wrote it had no Blender.
set -euo pipefail
VERIFY_FAILED=0

OUTROOT="${1:?usage: $0 <OUTROOT (must not exist)> [--skip-r120]}"
SKIP_R120="${2:-}"
PY="${PY:-python3.13}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"          # .../scripts/body_v2
REPO="$(cd "$HERE/../.." && pwd)"
R57_COMMIT=025d5f28fa7eba2064fba565b1c9b60119cdd2cb
R41_SHA=4c44b1fe14aeefd9a976f45baada60b4b81aaaa7cd736a300ca7cede2b0aaf2e
R41_REL=ORIGINAL_V1_WORK/anatomy/candidates/codex_review_r41_20261017/HGPT_ORIGINAL_V1_REVIEW_R41_CODEX.blend

[ -e "$OUTROOT" ] && { echo "REFUSING: $OUTROOT already exists (never overwrite)."; exit 2; }
mkdir -p "$OUTROOT"/{W8,V14,R120_base,R120,verify,logs}
OUTROOT="$(cd "$OUTROOT" && pwd)"
step() { echo; echo "=== $(date -u +%FT%TZ)  $*"; }

step "R57SRC worktree at $R57_COMMIT (separate checkout; the current branch is not touched)"
git -C "$REPO" fetch origin codex/r57-local-s7-temporal-study-20261020 2>&1 | tail -1
R57SRC="$OUTROOT/r57src"
git -C "$REPO" worktree add --detach "$R57SRC" "$R57_COMMIT" >/dev/null
[ "$(git -C "$R57SRC" rev-parse HEAD)" = "$R57_COMMIT" ]
GOT="$(sha256sum "$R57SRC/$R41_REL" | cut -d' ' -f1)"
[ "$GOT" = "$R41_SHA" ] || { echo "R41 input hash mismatch: $GOT"; exit 3; }
echo "R41 input verified: $GOT"
"$PY" -c "import bpy;print('bpy',bpy.app.version_string)" | tee "$OUTROOT/verify/blender_version.txt"

step "offline evidence check"
"$PY" -I "$HERE/verify_offline_evidence.py" "$REPO" "$R57SRC" "$OUTROOT/verify/offline_evidence_check.json"
EXP="$OUTROOT/verify/offline_evidence_check.json"

cd "$HERE"
step "1/3  W8 / v13s  (about 15 min)"
V2_SAVE_BLEND=1 "$PY" build_body_v2_sculpt_blender.py -- "$R57SRC" "$OUTROOT/W8" 2.0 2>&1 | tee "$OUTROOT/logs/w8_build.log" | tail -3
"$PY" -I compare_rebuild_to_archive.py "$REPO" "$OUTROOT/W8" "$OUTROOT/verify/w8_vs_archive.json" || VERIFY_FAILED=1
"$PY" verify_body_v2_blend.py -- "$OUTROOT/W8/body_v2.blend" v13s_w8 "$EXP" "$OUTROOT/verify/w8_blend.json" || VERIFY_FAILED=1
mkdir -p "$OUTROOT/W8/renders"
"$PY" render_v2_blender.py -- "$OUTROOT/W8/body_v2.blend" "$R57SRC" "$OUTROOT/W8/renders" 2>&1 | tee "$OUTROOT/logs/w8_render.log" | tail -1 || VERIFY_FAILED=1

step "2/3  v14b  (legs + feet + torso, default settings; about 10 min)"
"$PY" legs_v2_blender.py -- "$OUTROOT/W8/body_v2.blend" "$R57SRC" "$OUTROOT/V14" 2>&1 | tee "$OUTROOT/logs/v14_build.log" | tail -3 || VERIFY_FAILED=1
"$PY" verify_body_v2_blend.py -- "$OUTROOT/V14/body_v2_legs.blend" draft_v14b_torso "$EXP" "$OUTROOT/verify/v14_blend.json" || VERIFY_FAILED=1
"$PY" -I - "$REPO" "$OUTROOT" <<'EOF' || VERIFY_FAILED=1
import json, sys
from pathlib import Path
repo, out = Path(sys.argv[1]), Path(sys.argv[2])
a = json.loads((repo / "review-assets/body_v2/draft_v14b_torso/legs_v2_report.json").read_text())
b = json.loads((out / "V14/legs_v2_report.json").read_text())
bad = {k: (a[k], b.get(k)) for k in a if a[k] != b.get(k)}
print("v14b report identical to archive" if not bad else f"v14b report differs: {bad}")
(out / "verify/v14_report_vs_archive.json").write_text(json.dumps({"identical": not bad, "differences": bad}, indent=1))
sys.exit(1 if bad else 0)
EOF

if [ "$SKIP_R120" != "--skip-r120" ]; then
  step "3/3  R120 - EXPERIMENTAL, kept separate (legs-only base, then the rebuild)"
  V2_TORSO_RELIEF=0 V2_PEC_JUNCTION=0 "$PY" legs_v2_blender.py -- "$OUTROOT/W8/body_v2.blend" "$R57SRC" "$OUTROOT/R120_base" 2>&1 | tee "$OUTROOT/logs/r120_base.log" | tail -1 || VERIFY_FAILED=1
  "$PY" rebuild_v2_blender.py -- "$OUTROOT/R120_base/body_v2_legs.blend" "$R57SRC" "$OUTROOT/R120" 2>&1 | tee "$OUTROOT/logs/r120_build.log" | tail -2 || VERIFY_FAILED=1
  "$PY" verify_body_v2_blend.py -- "$OUTROOT/R120/body_v2_rebuilt.blend" none "$EXP" "$OUTROOT/verify/r120_blend.json" || VERIFY_FAILED=1
fi

step "comparison sheets (front / side / back / three-quarter)"
"$PY" -I "$HERE/make_comparison_sheet.py" "$OUTROOT" "$OUTROOT/verify/comparison_new.jpg" || echo "sheet skipped (see message)"

step "hashes + manifest"
"$PY" -I - "$OUTROOT" "$REPO" "$R57_COMMIT" "$R41_SHA" <<'EOF'
import datetime, json, subprocess, sys
from pathlib import Path
out, repo = Path(sys.argv[1]), sys.argv[2]
header = {"date_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
          "repo_commit": subprocess.check_output(["git", "-C", repo, "rev-parse", "HEAD"], text=True).strip(),
          "r57_commit": sys.argv[3], "r41_sha256": sys.argv[4],
          "bpy": (out / "verify/blender_version.txt").read_text().strip()}
(out / "MANIFEST_HEADER.json").write_text(json.dumps(header, indent=2) + "\n")
EOF
( cd "$OUTROOT" && { find W8 V14 R120_base R120 verify logs -type f -print0; printf 'MANIFEST_HEADER.json\0'; } | sort -z | xargs -0 sha256sum > MANIFEST.sha256 )
git -C "$REPO" worktree remove --force "$R57SRC"
chmod -R a-w "$OUTROOT"
echo; echo "DONE. Outputs under $OUTROOT are now read-only. Hashes: $OUTROOT/MANIFEST.sha256"
echo "R120 is EXPERIMENTAL; do not treat it as W8 or v14."
exit "$VERIFY_FAILED"
