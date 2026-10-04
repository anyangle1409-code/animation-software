param([string]$tag, [string]$sol)
$SP = "C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
Set-Location C:\Users\Mark\Documents\animation-software\repo
$env:PATH = "C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin;" + $env:PATH
$B = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
$D = "ORIGINAL_V1_WORK/candidates/repair_preparation/r88_abduction_region_floor_declared/shoulder_corrective_mask_declared_before_solve.json"
$blend = "$SP\ap_$tag.blend"
Remove-Item $blend, "$SP\ap_$tag.json", "$SP\ap_${tag}_spec.json" -ErrorAction SilentlyContinue
& $B --background --factory-startup $SP\r81_weights_intermediate.blend --python-exit-code 1 --python scripts\apply_original_v1_shoulder_corrective_blender.py -- $sol $D $blend "$SP\ap_${tag}_spec.json" 2>&1 | Select-String "APPLIED|rror|Refus"
Remove-Item -Recurse -Force "$SP\apt_$tag" -ErrorAction SilentlyContinue
& $B --background --factory-startup $blend --python-exit-code 1 --python scripts\pose_test_original_v1_o4_candidate_blender.py -- "$SP\apt_$tag" '""' --metrics-only 2>&1 | Select-String "rror|DONE"
python scripts\compare_original_v1_deformation_reports.py ORIGINAL_V1_WORK\candidates\pose_test_report_p3b1.json "$SP\apt_$tag\pose_test_report.json" --baseline-grip-report ORIGINAL_V1_WORK\candidates\pose_test_report_p3b1.json --candidate-grip-report "$SP\apt_$tag\pose_test_report.json" --profile development_blocker --report-only --json-out "$SP\acmp_${tag}_P3B1.json" | Select-Object -First 1
python scripts\compare_original_v1_deformation_reports.py ORIGINAL_V1_WORK\candidates\repair_checks\full_r83_merged_pose_report.json "$SP\apt_$tag\pose_test_report.json" --baseline-grip-report ORIGINAL_V1_WORK\candidates\repair_checks\full_r83_merged_pose_report.json --candidate-grip-report "$SP\apt_$tag\pose_test_report.json" --profile development_blocker --report-only --json-out "$SP\acmp_${tag}_r83.json" | Select-Object -First 1
python -c "
import json
d=json.load(open(r'$SP/acmp_${tag}_P3B1.json'))
print('vs P3B1 (squat items are expected without the flexion keys):')
for r in d['regressions']: print('  ',r['name'],r['region'],r['metric'],r['baseline'],'->',r['candidate'])
d=json.load(open(r'$SP/acmp_${tag}_r83.json'))
print('vs r83:')
for r in d['regressions']: print('  ',r['name'],r['region'],r['metric'],r['baseline'],'->',r['candidate'])
r=json.load(open(r'$SP/apt_$tag/pose_test_report.json'));r={x['pose']:x for x in r}
print({p:r[p]['self_intersecting_face_pairs'] for p in ('press_top','press_top_rhythm','pullup_hang','pullup_hang_rhythm','squat_bottom','pushup_bottom')})"
