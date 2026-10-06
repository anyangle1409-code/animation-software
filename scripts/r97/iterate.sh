#!/bin/bash
# iterate.sh <tag> <params.json> <rig_blend_with_pivot>  -> solves weights, applies to rig blend, renders key poses, sheet
set -e
T=$1; PRM=$2; BASE=$3; R=/home/user/r97; PYS="PYTHONPATH=/tmp/claude-0/bpy52:/tmp/claude-0/sci python3.13"
[ -f $R/W_$T.npz ] || (cd $R && eval $PYS tools/solve_weights.py rest.npz mirror_idx.npy $PRM W_$T.npz)
cd /tmp && PYTHONPATH=/tmp/claude-0/bpy52 python3.13 $R/tools/apply_weights.py -- $BASE $R/W_$T.npz $R/r97_$T.blend 2>&1 | grep applied
PYTHONPATH=/tmp/claude-0/bpy52 timeout 1800 python3.13 $R/tools/matrix.py -- $R/r97_$T.blend $R/m_$T --poses $(cat $R/keyposes.txt) 2>&1 | grep -E '"(worst|edge_ratio_m|seconds)' || true
cd $R/m_$T && F=""; for p in $(tr ',' ' ' < $R/keyposes.txt); do for v in close_front close_axilla close_rear front_three_quarter; do F="$F ${p}__$v.png"; done; done
PYTHONPATH=/tmp/claude-0/pil313 python3.13 $R/tools/sheet.py $R/key_$T.png 8 230 $F
