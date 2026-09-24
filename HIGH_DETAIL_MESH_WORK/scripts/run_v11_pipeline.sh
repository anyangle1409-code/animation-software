#!/usr/bin/env bash
# Rebuild and validate the V11 hand cleanup candidate end to end.
#
#   BLENDER_PY  Python that can `import bpy` (Blender 5.2.1), e.g.
#               "blender --background --python-exit-code 1 --python" on a desktop
#               install, or "python3.13" with the bpy wheel on PYTHONPATH.
#   PIL_PATH    optional extra PYTHONPATH holding Pillow, for the review boards.
#
# Run from HIGH_DETAIL_MESH_WORK. The pinned runtime `614033b` must be checked
# out at validation_63/ with node_modules installed (see V11_HAND_CLEANUP.md).
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${BLENDER_PY:-python3.13}
V=v11_hand_cleanup
C=HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_$V

rm -f "$C.glb" "${C}_BARE.glb"
$PY scripts/build_v11_hand_cleanup_blender.py | grep V11_HAND_BLENDER
$PY scripts/pack_v11_hand_glb.py | grep V11_HAND_GLB
$PY scripts/make_bare_variant.py $V
$PY scripts/candidate_quick_check.py "$C.glb" | grep -q '"quick_guard": "PASS"'
$PY scripts/guard_hand_floor_vertices.py "$C.glb" --strict > /dev/null

# The harnesses run inside the pinned runtime, as V10's did.
mkdir -p validation_63/scratchpad/repair
cp harnesses/review_hand_geometry_v11.test.mts harnesses/v11_hand_studies.test.mts validation_63/scratchpad/repair/
cp validation_63/HOME_GYM_PT_GPT_MESH_HANDOFF/harnesses/vitest.config.mts validation_63/scratchpad/repair/

# The five focused guards (sagittal, bare/dressed equivalence, grip metric,
# overlap, grip agreement), through the V10-era runner unchanged.
$PY scripts/run_candidate_gates.py --version $V --task hand --skip-exercise | tail -3

# Exercise gate against accepted V8, as V10's was.
(cd validation_63 && CANDIDATE_VERSION=$V npx vitest run --config scratchpad/repair/vitest.config.mts \
  scratchpad/repair/review_hand_geometry_v11.test.mts)

# Review boards against V10.
(cd validation_63 && CANDIDATE_VERSION=$V BASELINE_GLB=../HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v10_hand_retopology.glb \
  REPORT_NAME=board_poses_v11_vs_v10 npx vitest run --config scratchpad/repair/vitest.config.mts \
  scratchpad/repair/review_hand_geometry_v11.test.mts scratchpad/repair/v11_hand_studies.test.mts)
for mode in hand_studies hands_compare; do RENDER_VERSION=$V $PY scripts/render_candidate_review.py -- $mode | grep -c RENDER; done
PYTHONPATH=${PIL_PATH:-${PYTHONPATH:-}} $PY scripts/make_v11_hand_review_sheets.py
echo "V11 pipeline complete"
