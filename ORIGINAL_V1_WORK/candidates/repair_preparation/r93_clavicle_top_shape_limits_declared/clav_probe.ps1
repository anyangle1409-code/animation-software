param([string]$tag, [string]$sol)
$SP = "C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
Set-Location C:\Users\Mark\Documents\animation-software\repo
$env:PATH = "C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin;" + $env:PATH
$B = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
$D = "ORIGINAL_V1_WORK/candidates/repair_preparation/r93_clavicle_top_shape_limits_declared/shoulder_corrective_mask_declared_before_solve.json"
$blend = "$SP\cp_$tag.blend"
Remove-Item $blend, "$SP\cp_$tag.json", "$SP\cp_${tag}_spec.json" -ErrorAction SilentlyContinue
& $B --background --factory-startup $SP\r92_base_wrist.blend --python-exit-code 1 --python scripts\apply_original_v1_shoulder_corrective_blender.py -- $sol $D $blend "$SP\cp_${tag}_spec.json" 2>&1 | Select-String "APPLIED|rror|Refus"
Remove-Item -Recurse -Force "$SP\cpt_$tag" -ErrorAction SilentlyContinue
& $B --background --factory-startup $blend --python-exit-code 1 --python scripts\pose_test_original_v1_o4_candidate_blender.py -- "$SP\cpt_$tag" '""' --metrics-only 2>&1 | Select-String "rror|DONE"
python scripts\evaluate_original_v1_deformation_report.py "$SP\cpt_$tag\pose_test_report.json" --grip-report "$SP\cpt_$tag\pose_test_report.json" --profile development_blocker --report-only --markdown-out "$SP\cpt_${tag}_eval.md" | Select-Object -First 1
python scripts\compare_original_v1_deformation_reports.py ORIGINAL_V1_WORK\candidates\pose_test_report_p3b1.json "$SP\cpt_$tag\pose_test_report.json" --baseline-grip-report ORIGINAL_V1_WORK\candidates\pose_test_report_p3b1.json --candidate-grip-report "$SP\cpt_$tag\pose_test_report.json" --profile development_blocker --report-only --json-out "$SP\ccmp_${tag}_P3B1.json" | Select-Object -First 1
python scripts\compare_original_v1_deformation_reports.py ORIGINAL_V1_WORK\candidates\repair_checks\full_r92_merged_pose_report.json "$SP\cpt_$tag\pose_test_report.json" --baseline-grip-report ORIGINAL_V1_WORK\candidates\repair_checks\full_r92_merged_pose_report.json --candidate-grip-report "$SP\cpt_$tag\pose_test_report.json" --profile development_blocker --report-only --json-out "$SP\ccmp_${tag}_r92.json" | Select-Object -First 1
python $SP\clav_summarize.py $tag
& $B --background --factory-startup $blend --python-exit-code 1 --python scripts\dump_original_v1_arc_skinning_blender.py -- "$SP\cp_${tag}_dump.npz" "0.25,0.375,0.5,0.625,0.75,0.875" 2>&1 | Select-String "rror" | Select-Object -First 1
foreach ($p in "press_top", "press_top_rhythm", "pullup_hang") {
    & $B --background --factory-startup $blend --python-exit-code 1 --python scripts\render_original_v1_pose_closeup_blender.py -- "$SP\cpr_${tag}\$p" $p spine_03 0.75 $tag 2>&1 | Select-String "rror" | Select-Object -First 1
    & $B --background --factory-startup $blend --python-exit-code 1 --python scripts\render_original_v1_pose_closeup_blender.py -- "$SP\cpr_${tag}\${p}_cl" $p clavicle_l 0.35 $tag 2>&1 | Select-String "rror" | Select-Object -First 1
}
