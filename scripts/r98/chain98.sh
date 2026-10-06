#!/bin/bash
# chain98.sh <tag> <geo_params.json> <solve_params.json>  -> /home/user/r98/<tag>.blend + key-pose matrix /home/user/r98/m_<tag>
set -e
T=$1; G=$2; S=$3; R=/home/user/r98; R7=/home/user/r97/tools; PAR=/home/user/wb/ORIGINAL_V1_WORK/candidates/repair_preparation/r97_shoulder_foundation_declared/r95_reconstructed.blend
B="env PYTHONPATH=/tmp/claude-0/bpy52:/tmp/claude-0/sci python3.13"
cd /tmp
$B $R/tools/build98.py -- $PAR $G $R/${T}_geo.blend $R/${T}_geo.json 2>&1 | grep BUILD
$B $R/tools/dump_rest98.py -- $R/${T}_geo.blend $R/${T}_rest.npz 2>&1 | grep DUMP
$B $R7/scapula_pivot.py -- $R/${T}_geo.blend $R/${T}_c1.blend >/dev/null 2>&1
$B $R7/add_gh_helper.py -- $R/${T}_c1.blend $R/${T}_c2.blend >/dev/null 2>&1
$B $R7/helper_swing_half2.py -- $R/${T}_c2.blend $R/${T}_c3.blend >/dev/null 2>&1
cd $R && $B $R7/solve_weights.py $R/${T}_rest.npz $R/${T}_geo_mirror_idx.npy $S $R/W_${T}.npz | tail -1
cd /tmp && $B $R7/apply_weights.py -- $R/${T}_c3.blend $R/W_${T}.npz $R/${T}.blend 2>&1 | grep applied
cd /tmp && $B $R/tools/finalize98.py -- $R/${T}.blend $R/${T}.blend $S /home/user/r97/tools/solve_weights.py $R/${T}_geo.json 2>&1 | grep saved
rm -f $R/${T}_c1.blend $R/${T}_c2.blend
if [ -z "$NOMATRIX" ]; then
MIRROR=$R/${T}_geo_mirror_idx.npy timeout 1800 $B $R7/matrix.py -- $R/${T}.blend $R/m_${T} --res 420 --poses $(cat /home/user/r97/keyposes.txt),flexion_060_external,horizontal_adduction_90,arm_behind_torso,flexion_030_external,abduction_000_external 2>&1 | grep -E '"(worst|edge_ratio_m|seconds)' || true
fi
