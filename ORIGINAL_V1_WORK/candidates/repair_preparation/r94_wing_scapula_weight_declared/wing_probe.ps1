param([string]$beta)
$SP = "C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
Set-Location C:\Users\Mark\Documents\animation-software\repo
$env:PATH = "C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin;" + $env:PATH
$B = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
$D = "ORIGINAL_V1_WORK/candidates/repair_preparation/r94_wing_scapula_weight_declared/shoulder_corrective_mask_declared_before_solve_b$beta.json"
$tag = "wb$beta"
$blend = "$SP\wp_$tag.blend"
Remove-Item $blend, "$SP\wp_$tag.json", "$SP\wp_${tag}_spec.json" -ErrorAction SilentlyContinue
& $B --background --factory-startup "$SP\wb_b$beta.blend" --python-exit-code 1 --python scripts\apply_original_v1_shoulder_corrective_blender.py -- "$SP\wing_abd_b$beta.npz" $D $blend "$SP\wp_${tag}_spec.json" 2>&1 | Select-String "APPLIED|rror|Refus"
Remove-Item -Recurse -Force "$SP\wpt_$tag" -ErrorAction SilentlyContinue
& $B --background --factory-startup $blend --python-exit-code 1 --python scripts\pose_test_original_v1_o4_candidate_blender.py -- "$SP\wpt_$tag" '""' --metrics-only 2>&1 | Select-String "rror|DONE"
python scripts\evaluate_original_v1_deformation_report.py "$SP\wpt_$tag\pose_test_report.json" --grip-report "$SP\wpt_$tag\pose_test_report.json" --profile development_blocker --report-only --markdown-out "$SP\wpt_${tag}_eval.md" | Select-Object -First 1
python scripts\compare_original_v1_deformation_reports.py ORIGINAL_V1_WORK\candidates\pose_test_report_p3b1.json "$SP\wpt_$tag\pose_test_report.json" --baseline-grip-report ORIGINAL_V1_WORK\candidates\pose_test_report_p3b1.json --candidate-grip-report "$SP\wpt_$tag\pose_test_report.json" --profile development_blocker --report-only --json-out "$SP\wcmp_${tag}_P3B1.json" | Select-Object -First 1
python scripts\compare_original_v1_deformation_reports.py ORIGINAL_V1_WORK\candidates\repair_checks\full_r93_merged_pose_report.json "$SP\wpt_$tag\pose_test_report.json" --baseline-grip-report ORIGINAL_V1_WORK\candidates\repair_checks\full_r93_merged_pose_report.json --candidate-grip-report "$SP\wpt_$tag\pose_test_report.json" --profile development_blocker --report-only --json-out "$SP\wcmp_${tag}_r93.json" | Select-Object -First 1
python -c "
import json
d=json.load(open(r'$SP/wcmp_${tag}_P3B1.json'))
print('vs P3B1 (squat items expected: this screening copy has no flexion keys):')
for r in d['regressions']: print('  ',r['name'],r['region'],r['metric'],r['baseline'],'->',r['candidate'])
d=json.load(open(r'$SP/wcmp_${tag}_r93.json'))
print('vs r93:')
for r in d['regressions']: print('  ',r['name'],r['region'],r['metric'],r['baseline'],'->',r['candidate'])
r={x['pose']:x for x in json.load(open(r'$SP/wpt_$tag/pose_test_report.json'))}
print('SI',{p:r[p]['self_intersecting_face_pairs'] for p in ('press_top','press_top_rhythm','pullup_hang','pullup_hang_rhythm','squat_bottom','pushup_bottom')},'(P3B1 95/54/4/0/108/158)')
print('press_top p99',r['press_top']['edge_ratio_p99'],'vol',r['press_top']['volume_ratio'])"
& $B --background --factory-startup $blend --python-exit-code 1 --python scripts\dump_original_v1_arc_skinning_blender.py -- "$SP\wp_${tag}_dump.npz" "0.25,0.375,0.5,0.625,0.75,0.875" 2>&1 | Select-String "rror" | Select-Object -First 1
foreach ($p in "press_top", "press_top_rhythm", "pullup_hang") {
    & $B --background --factory-startup $blend --python-exit-code 1 --python scripts\render_original_v1_pose_closeup_blender.py -- "$SP\wpr_${tag}\$p" $p spine_03 0.75 $tag 2>&1 | Select-String "rror" | Select-Object -First 1
}
