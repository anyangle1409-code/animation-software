#!/bin/bash
# usage: sheets_matrix.sh <matrix_dir> <prefix>
M=$1; X=$2; S="PYTHONPATH=/tmp/claude-0/pil313 python3.13 /home/user/r97/tools/sheet.py"
cd $M
for plane in abduction flexion; do
  F=""; for th in 030 060 090 120 150 170; do for v in front close_front close_axilla close_rear rear; do F="$F ${plane}_${th}_neutral__$v.png"; done; done
  eval $S /home/user/r97/${X}_${plane}_arc.png 5 260 $F
done
F=""; for th in 090 150; do for a in internal neutral external; do for v in close_front close_axilla close_rear; do F="$F abduction_${th}_${a}__$v.png"; done; done; done
eval $S /home/user/r97/${X}_axial_abd.png 3 300 $F
F=""; for p in horizontal_adduction_90 horizontal_abduction_90 arm_behind_torso bent_elbow_elevation_120 press_bottom_like press_top_like pullup_hang_like pullup_top_like bench_bottom_like pushup_bottom_like row_top_like curl_top_like; do for v in front_three_quarter close_front close_rear; do F="$F ${p}__$v.png"; done; done
eval $S /home/user/r97/${X}_compound.png 6 230 $F
