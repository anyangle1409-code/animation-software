param([string]$tag, [string]$sol)
$SP = "C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
Set-Location C:\Users\Mark\Documents\animation-software\repo
$env:PATH = "C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin;" + $env:PATH
$B = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
$D = "ORIGINAL_V1_WORK/candidates/repair_preparation/r92_overhead_dent_limit_declared/shoulder_corrective_mask_declared_before_solve.json"
$blend = "$SP\dp_$tag.blend"
Remove-Item $blend, "$SP\dp_$tag.json", "$SP\dp_${tag}_spec.json" -ErrorAction SilentlyContinue
& $B --background --factory-startup $SP\r81_weights_intermediate.blend --python-exit-code 1 --python scripts\apply_original_v1_shoulder_corrective_blender.py -- $sol $D $blend "$SP\dp_${tag}_spec.json" 2>&1 | Select-String "APPLIED|rror|Refus"
Remove-Item -Recurse -Force "$SP\dpt_$tag" -ErrorAction SilentlyContinue
& $B --background --factory-startup $blend --python-exit-code 1 --python scripts\pose_test_original_v1_o4_candidate_blender.py -- "$SP\dpt_$tag" '""' --metrics-only 2>&1 | Select-String "rror|DONE"
python scripts\compare_original_v1_deformation_reports.py ORIGINAL_V1_WORK\candidates\pose_test_report_p3b1.json "$SP\dpt_$tag\pose_test_report.json" --baseline-grip-report ORIGINAL_V1_WORK\candidates\pose_test_report_p3b1.json --candidate-grip-report "$SP\dpt_$tag\pose_test_report.json" --profile development_blocker --report-only --json-out "$SP\dcmp_${tag}_P3B1.json" | Select-Object -First 1
python scripts\evaluate_original_v1_deformation_report.py "$SP\dpt_$tag\pose_test_report.json" --grip-report "$SP\dpt_$tag\pose_test_report.json" --profile development_blocker --report-only --markdown-out "$SP\dpt_${tag}_eval.md" | Select-Object -First 1
python scripts\compare_original_v1_deformation_reports.py ORIGINAL_V1_WORK\candidates\repair_checks\full_r91_merged_pose_report.json "$SP\dpt_$tag\pose_test_report.json" --baseline-grip-report ORIGINAL_V1_WORK\candidates\repair_checks\full_r91_merged_pose_report.json --candidate-grip-report "$SP\dpt_$tag\pose_test_report.json" --profile development_blocker --report-only --json-out "$SP\dcmp_${tag}_r91.json" | Select-Object -First 1
python -c "
import json
d=json.load(open(r'$SP/dcmp_${tag}_P3B1.json'))
print('vs P3B1 (squat and push-up items are expected: no flexion keys / no wrist patch in this screening copy):')
for r in d['regressions']: print('  ',r['name'],r['region'],r['metric'],r['baseline'],'->',r['candidate'])
d=json.load(open(r'$SP/dcmp_${tag}_r91.json'))
print('vs r91:')
for r in d['regressions']: print('  ',r['name'],r['region'],r['metric'],r['baseline'],'->',r['candidate'])
r=json.load(open(r'$SP/dpt_$tag/pose_test_report.json'));r={x['pose']:x for x in r}
print('SI',{p:r[p]['self_intersecting_face_pairs'] for p in ('press_top','press_top_rhythm','pullup_hang','pullup_hang_rhythm','squat_bottom')})
print('press_top p99',r['press_top']['edge_ratio_p99'],'vol',r['press_top']['volume_ratio'])"
& $B --background --factory-startup $blend --python-exit-code 1 --python scripts\dump_original_v1_arc_skinning_blender.py -- "$SP\dp_${tag}_dump.npz" "0.25,0.375,0.5,0.625,0.75,0.875" 2>&1 | Select-String "rror" | Select-Object -First 1
& $B --background --factory-startup $blend --python-exit-code 1 --python scripts\render_original_v1_pose_closeup_blender.py -- "$SP\dpr_$tag" press_top spine_03 0.75 $tag 2>&1 | Select-String "rror" | Select-Object -First 1
& $B --background --factory-startup $blend --python-exit-code 1 --python scripts\render_original_v1_pose_closeup_blender.py -- "$SP\dpr_${tag}_cl" press_top clavicle_l 0.35 $tag 2>&1 | Select-String "rror" | Select-Object -First 1
