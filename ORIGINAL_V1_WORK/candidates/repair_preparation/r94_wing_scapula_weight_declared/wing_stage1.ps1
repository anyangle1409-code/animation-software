param([string]$beta)
$SP = "C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
Set-Location C:\Users\Mark\Documents\animation-software\repo
$env:PATH = "C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin;" + $env:PATH
$B = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
$D = "ORIGINAL_V1_WORK/candidates/repair_preparation/r94_wing_scapula_weight_declared"
python $SP\wing_mksol.py $beta
$bl = "$SP\wb_b$beta.blend"
Remove-Item $bl, "$SP\wb_b$beta.json" -ErrorAction SilentlyContinue
& $B --background --factory-startup $SP\r92_base_wrist.blend --python-exit-code 1 --python scripts\apply_original_v1_o4_weight_solution_blender.py -- "$SP\wing_sol_b$beta.npz" $bl 2>&1 | Select-String "APPLIED|rror"
& $B --background --factory-startup $bl --python-exit-code 1 --python scripts\dump_original_v1_arc_skinning_blender.py -- "$SP\wb_b${beta}_dump.npz" 2>&1 | Select-String "DUMP DONE|rror" | ForEach-Object { $_.Line.Substring(0, 30) }
python scripts\optimize_original_v1_shoulder_corrective.py "$SP\wb_b${beta}_dump.npz" x.npz --declare-mask "$D/shoulder_corrective_mask_declared_before_solve_b$beta.json"
