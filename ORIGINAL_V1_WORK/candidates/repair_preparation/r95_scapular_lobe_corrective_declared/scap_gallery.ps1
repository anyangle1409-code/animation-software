$SP = "C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
Set-Location C:\Users\Mark\Documents\animation-software\repo
$B = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
$G = "$SP\sgal"
$states = @(@("r93", "ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r93.blend"), @("L0.045", "$SP\sp_L0.045.blend"), @("L0.035", "$SP\sp_L0.035.blend"), @("wonly", "$SP\r92_base_wrist.blend"))
foreach ($s in $states) {
    $t = $s[0]; $bl = $s[1]
    foreach ($p in "press_top", "press_top_rhythm", "pullup_top", "pullup_hang", "press_bottom") {
        & $B --background --factory-startup $bl --python-exit-code 1 --python scripts\render_original_v1_pose_closeup_blender.py -- "$G\$t\$p" $p spine_03 0.75 $t 2>&1 | Select-String "rror" | Select-Object -First 1
    }
    foreach ($p in "press_top", "pullup_hang") {
        & $B --background --factory-startup $bl --python-exit-code 1 --python scripts\render_original_v1_pose_closeup_blender.py -- "$G\$t\${p}_scapula" $p scapula_l 0.40 $t 2>&1 | Select-String "rror" | Select-Object -First 1
        & $B --background --factory-startup $bl --python-exit-code 1 --python scripts\render_original_v1_pose_closeup_blender.py -- "$G\$t\${p}_lateral" $p spine_02 0.45 $t 2>&1 | Select-String "rror" | Select-Object -First 1
        & $B --background --factory-startup $bl --python-exit-code 1 --python scripts\render_original_v1_pose_closeup_blender.py -- "$G\$t\${p}_axilla" $p upperarm_l 0.30 $t 2>&1 | Select-String "rror" | Select-Object -First 1
        & $B --background --factory-startup $bl --python-exit-code 1 --python scripts\render_original_v1_pose_closeup_blender.py -- "$G\$t\${p}_clavicle" $p clavicle_l 0.35 $t 2>&1 | Select-String "rror" | Select-Object -First 1
    }
    foreach ($f in "0.5", "0.625", "0.75") {
        & $B --background --factory-startup $bl --python-exit-code 1 --python scripts\render_original_v1_pose_closeup_blender.py -- "$G\$t\press_top_f$f" press_top spine_03 0.75 $t --fraction $f 2>&1 | Select-String "rror" | Select-Object -First 1
    }
}
"GALLERY DONE" | Out-File "$SP\scap_gallery.done"
