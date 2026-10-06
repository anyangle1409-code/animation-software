#!/bin/bash
# local98.sh <tag> <src_tag_with_geo_and_Wsolve> <blend_params.json>  (reuses <src>_geo.blend, W_<src>.npz)
set -e
T=$1; SRC=$2; BP=$3; R=/home/user/r98; R7=/home/user/r97/tools; B="env PYTHONPATH=/tmp/claude-0/bpy52:/tmp/claude-0/sci python3.13"
cd /tmp
cp $R/${SRC}_geo.json $R/${T}_geo.json; cp $R/${SRC}_geo_mirror_idx.npy $R/${T}_geo_mirror_idx.npy
$B $R/tools/blend_local.py $R/${SRC}_rest.npz /home/user/r97/rest.npz $R/W_${SRC}.npz /home/user/r97/W_v28.npz $R/${T}_geo_mirror_idx.npy $BP $R/W_${T}.npz
$B $R7/scapula_pivot.py -- $R/${SRC}_geo.blend $R/${T}_c1.blend >/dev/null 2>&1; $B $R7/add_gh_helper.py -- $R/${T}_c1.blend $R/${T}_c2.blend >/dev/null 2>&1; $B $R7/helper_swing_half2.py -- $R/${T}_c2.blend $R/${T}_c3.blend >/dev/null 2>&1
$B $R7/apply_weights.py -- $R/${T}_c3.blend $R/W_${T}.npz $R/${T}.blend 2>&1 | grep applied
$B $R/tools/finalize98.py -- $R/${T}.blend $R/${T}.blend /home/user/r98/s_v28.json $R7/solve_weights.py $R/${T}_geo.json 2>&1 | grep saved
rm -f $R/${T}_c1.blend $R/${T}_c2.blend
MIRROR=$R/${T}_geo_mirror_idx.npy $B $R7/matrix.py -- $R/${T}.blend $R/m_${T} --no-render --poses $(cat /home/user/r97/keyposes.txt),flexion_060_external,horizontal_adduction_90,arm_behind_torso,flexion_030_external,abduction_000_external 2>&1 | grep worst
$R/tools/pt.sh $R/${T}.blend $R/pt_${T} | grep -E "press_top |squat|pullup_hang|pullup_top|REGR"
