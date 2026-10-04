$SP = "C:\Users\Mark\AppData\Local\Temp\claude\C--Users-Mark-Documents-animation-software\a03a00a6-7deb-42cf-83e5-afef93e56c83\scratchpad"
Set-Location C:\Users\Mark\Documents\animation-software\repo
$B = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
foreach ($l in "0.25", "0.50", "0.60", "0.70", "1.00") {
    $bl = "$SP\wr_l$l.blend"
    Remove-Item $bl, "$SP\wr_l$l.json" -ErrorAction SilentlyContinue
    & $B --background --factory-startup ORIGINAL_V1_WORK\candidates\HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r90.blend --python-exit-code 1 --python scripts\apply_original_v1_o4_weight_solution_blender.py -- "$SP\wrist_sol_l$l.npz" $bl 2>&1 | Select-String "rror|Refus|Expected" | Select-Object -First 2
    & $B --background --factory-startup $bl --python-exit-code 1 --python scripts\diagnose_original_v1_pair_list_blender.py -- "$SP\wr_pl_l$l.json" pushup_bottom 2>&1 | Select-String "PAIR LIST|rror" | ForEach-Object { "lambda $l -> " + $_.Line.Substring(0, 16) }
}
