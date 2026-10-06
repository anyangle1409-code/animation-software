#!/bin/bash
# pt.sh <blend> <outdir>  -> repo pose test + compact SI table vs r95/r97
B=$1; O=$2; rm -rf $O; mkdir -p $O; cd /tmp
PYTHONPATH=/tmp/claude-0/bpy52 timeout 3000 python3.13 /home/user/r97/tools/run_repo_script.py -- $B /home/user/wb/scripts/pose_test_original_v1_o4_candidate_blender.py $O > $O/pose_test.log 2>&1
python3 - $O <<'PY'
import json,sys
O=sys.argv[1]
a={r['pose']:r for r in json.load(open('/home/user/r97/pt_r95_weights_only/pose_test_report.json'))}
b={r['pose']:r for r in json.load(open('/home/user/wb/ORIGINAL_V1_WORK/candidates/repair_checks/r97_pose_test_weights_only/pose_test_report.json'))}
c={r['pose']:r for r in json.load(open(O+'/pose_test_report.json'))}
print('pose'.ljust(20),'SI r95/r97/new'.ljust(18),'stretch>1.6 r95/r97/new'.ljust(26),'p99 r95/r97/new')
bad=[]
for p in a:
    s=[x[p]['self_intersecting_face_pairs'] for x in (a,b,c)]
    print(p.ljust(20),('%d/%d/%d'%tuple(s)).ljust(18),('%d/%d/%d'%tuple(x[p]['stretched_edges_gt_1_6'] for x in (a,b,c))).ljust(26),'%.3f/%.3f/%.3f'%tuple(x[p]['edge_ratio_p99'] for x in (a,b,c)))
    if s[2]>s[0]+5: bad.append(p)
print('REGRESSIONS vs r95 (SI tol 5):',bad)
PY
