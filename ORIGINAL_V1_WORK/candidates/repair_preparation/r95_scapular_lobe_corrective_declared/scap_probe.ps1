param([string]$tag, [string]$sol)
$SP = "C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
Set-Location C:\Users\Mark\Documents\animation-software\repo
$env:PATH = "C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin;" + $env:PATH
$B = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
$D = "ORIGINAL_V1_WORK/candidates/repair_preparation/r95_scapular_lobe_corrective_declared/scapular_lobe_mask_declared_before_solve.json"
$blend = "$SP\sp_$tag.blend"
Remove-Item $blend, "$SP\sp_$tag.json", "$SP\sp_${tag}_spec.json" -ErrorAction SilentlyContinue
& $B --background --factory-startup ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r93.blend --python-exit-code 1 --python scripts\apply_original_v1_scapular_corrective_blender.py -- $sol $D $blend "$SP\sp_${tag}_spec.json" 2>&1 | Select-String "APPLIED|rror|Refus"
Remove-Item -Recurse -Force "$SP\spt_$tag" -ErrorAction SilentlyContinue
& $B --background --factory-startup $blend --python-exit-code 1 --python scripts\pose_test_original_v1_o4_candidate_blender.py -- "$SP\spt_$tag" '""' --metrics-only 2>&1 | Select-String "rror|DONE"
python scripts\evaluate_original_v1_deformation_report.py "$SP\spt_$tag\pose_test_report.json" --grip-report "$SP\spt_$tag\pose_test_report.json" --profile development_blocker --report-only --markdown-out "$SP\spt_${tag}_eval.md" | Select-Object -First 1
python scripts\compare_original_v1_deformation_reports.py ORIGINAL_V1_WORK\candidates\pose_test_report_p3b1.json "$SP\spt_$tag\pose_test_report.json" --baseline-grip-report ORIGINAL_V1_WORK\candidates\pose_test_report_p3b1.json --candidate-grip-report "$SP\spt_$tag\pose_test_report.json" --profile development_blocker --report-only --json-out "$SP\scmp_${tag}_P3B1.json" | Select-Object -First 1
python scripts\compare_original_v1_deformation_reports.py ORIGINAL_V1_WORK\candidates\repair_checks\full_r93_merged_pose_report.json "$SP\spt_$tag\pose_test_report.json" --baseline-grip-report ORIGINAL_V1_WORK\candidates\repair_checks\full_r93_merged_pose_report.json --candidate-grip-report "$SP\spt_$tag\pose_test_report.json" --profile development_blocker --report-only --json-out "$SP\scmp_${tag}_r93.json" | Select-Object -First 1
python $SP\scap_summarize.py $tag
& $B --background --factory-startup $blend --python-exit-code 1 --python scripts\dump_original_v1_arc_skinning_blender.py -- "$SP\sp_${tag}_dump.npz" "0.125,0.25,0.375,0.5,0.625,0.75,0.875" press_top,press_top_rhythm,pullup_hang,pullup_hang_rhythm,pullup_top,press_bottom 2>&1 | Select-String "rror" | Select-Object -First 1
foreach ($p in "press_top", "press_top_rhythm", "pullup_hang") {
    & $B --background --factory-startup $blend --python-exit-code 1 --python scripts\render_original_v1_pose_closeup_blender.py -- "$SP\spr_${tag}\$p" $p spine_03 0.75 $tag 2>&1 | Select-String "rror" | Select-Object -First 1
}
& $B --background --factory-startup $blend --python-exit-code 1 --python scripts\render_original_v1_pose_closeup_blender.py -- "$SP\spr_${tag}\press_top_scapula" press_top scapula_l 0.40 $tag 2>&1 | Select-String "rror" | Select-Object -First 1
