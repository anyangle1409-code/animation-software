#!/usr/bin/env bash
# Run the character-dependent gates of the full exercise library against one or
# more character GLBs, then tabulate them against the production character.
#
#   scripts/mesh-coordination-report.sh OUT_DIR NAME=path/to.glb [NAME=path/to.glb ...]
#
# Writes OUT_DIR/<name>.log per character (production first) and prints the
# tables docs/MESH_COORDINATION_REPORT.md is built from. Read-only: nothing in
# the repository or its assets is changed.
set -euo pipefail
out=$1; shift
mkdir -p "$out"
files="src/exercises/equipmentClearance.test.ts src/exercises/selfCollision.test.ts
  src/exercises/families/lunge.test.ts src/exercises/families/rotation.test.ts
  src/exercises/families/trunkFlexion.test.ts src/retargeting/mirroredHands.test.ts
  src/retargeting/palmMapping.test.ts src/retargeting/realCharacterDiagnostic.test.ts
  src/retargeting/unmappedBones.test.ts"
names=(production)
REAL_CHARACTER_GLB=review-assets/characters/HomeGymPT_Male_CORNER_FINAL_SHORTS.glb \
  npx vitest run $files > "$out/production.log" 2>&1 || true
for pair in "$@"; do
  name=${pair%%=*}; glb=${pair#*=}; names+=("$name")
  REAL_CHARACTER_GLB=$glb npx vitest run $files > "$out/$name.log" 2>&1 || true
done
for name in "${names[@]}"; do echo "$name: $(grep -E 'Tests ' "$out/$name.log" | tail -1)"; done
python3 "$(dirname "$0")/mesh-coordination-report.py" "$out" "${names[@]}"
