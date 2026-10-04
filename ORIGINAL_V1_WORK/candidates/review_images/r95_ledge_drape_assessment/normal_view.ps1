$SP = "C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
Set-Location C:\Users\Mark\Documents\animation-software\repo
$B = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
$G = "$SP\nv"
$states = @(@("r95", "ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r95.blend"), @("r93", "ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r93.blend"), @("wonly", "$SP\r92_base_wrist.blend"), @("P3B1", "ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r42.blend"))
foreach ($s in $states) {
    foreach ($p in "press_top", "pullup_hang", "press_top_rhythm") {
        # normal viewing distance: whole figure (ortho scale 2.3), then a bust-level framing (scale 1.0)
        & $B --background --factory-startup $s[1] --python-exit-code 1 --python scripts\render_original_v1_pose_closeup_blender.py -- "$G\$($s[0])\${p}_body" $p spine_03 2.3 $s[0] 2>&1 | Select-String "rror" | Select-Object -First 1
        & $B --background --factory-startup $s[1] --python-exit-code 1 --python scripts\render_original_v1_pose_closeup_blender.py -- "$G\$($s[0])\${p}_bust" $p spine_03 1.1 $s[0] 2>&1 | Select-String "rror" | Select-Object -First 1
    }
}
"NV DONE" | Out-File "$SP\nv.done"
