$ErrorActionPreference = "Continue"
$SP = "C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
Set-Location C:\Users\Mark\Documents\animation-software\repo
$env:PATH = "C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin;" + $env:PATH
$B = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
$log = "$SP\build_r93.log"; Remove-Item $log -ErrorAction SilentlyContinue
$P = "ORIGINAL_V1_WORK/candidates/repair_preparation/r93_clavicle_top_shape_limits_declared"
$MASK = "$P/shoulder_corrective_mask_declared_before_solve.json"
$FMASK = "ORIGINAL_V1_WORK/candidates/repair_preparation/r89_flexion_volume_floor_declared/flexion_corrective_mask_declared_before_solve.json"
$base = "$SP\r92_base_wrist.blend"; $x = "$SP\r93_abd.blend"
Remove-Item $x, "$SP\r93_abd.json", "$SP\r93_abd_spec.json" -ErrorAction SilentlyContinue
"[1] apply the A3 abduction solution to the weights + wrist base" | Out-File $log -Append
& $B --background --factory-startup $base --python-exit-code 1 --python scripts\apply_original_v1_shoulder_corrective_blender.py -- "$SP\clavA3.npz" $MASK $x "$SP\r93_abd_spec.json" 2>&1 | Select-String "APPLIED|rror|Refus" | Out-File $log -Append
"[2] dump with squat arc for the flexion solve" | Out-File $log -Append
& $B --background --factory-startup $x --python-exit-code 1 --python scripts\dump_original_v1_arc_skinning_blender.py -- "$SP\r93_flex_dump.npz" "0.125,0.25,0.375,0.5,0.625,0.75,0.875" squat_bottom 2>&1 | Select-String "DUMP DONE|rror" | Out-File $log -Append
"[3] flexion solve (volume floor 0.9525)" | Out-File $log -Append
$fcommon = "--iters 450 --rounds 3 --abs-lo --lo 0.60 --hi 3.6 --p99-tail 1.95 --trunk-a0 0.06 --trunk-a1 0.22 --w-smooth 300 --w-fold 5000 --fold-floor 0.3 --w-area-rest 50000 --area-floor 0.35 --w-lap 50000 --lap-tol 0.2 --w-prox 3e6 --prox-d 0.02 --driver flexion --theta0 45 --theta1 120 --hold-region-min 0.02 --hold-region-max 0.1 --hold-scope region --w-hold 1e6 --w-vol 1e7 --vol-floor 0.9525"
Invoke-Expression "python scripts\optimize_original_v1_shoulder_corrective.py `"$SP\r93_flex_dump.npz`" `"$SP\r93_flex.npz`" $fcommon" 2>&1 | Select-String "SOLUTION|rror" | Out-File $log -Append
"[4] apply flexion keys -> r93" | Out-File $log -Append
& $B --background --factory-startup $x --python-exit-code 1 --python scripts\apply_original_v1_flexion_corrective_blender.py -- "$SP\r93_flex.npz" $FMASK ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r93.blend ORIGINAL_V1_WORK\flexion_corrective_r93.json 2>&1 | Select-String "APPLIED|rror|Refus" | Out-File $log -Append
"DONE" | Out-File $log -Append
