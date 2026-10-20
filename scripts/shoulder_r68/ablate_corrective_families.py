# R68 ablation (exec'd by diagnose_shoulder_skinning_blender.py with R68_MODE=ablate): at each angle, switch ONE shoulder
# corrective family off (LBS) and report the right rear-shoulder pinch, to find which family flattens the rear deltoid.
FAMS = {"SHOULDER_CORR/FLEX/SCAP": ("SHOULDER_CORR", "SHOULDER_FLEX", "SHOULDER_SCAP"), "S1": ("_S1_",), "S3": ("_S3_",),
        "H1": ("_H1_",), "S5": ("_S5_",), "S7": ("_S7_",), "C1_ARMTRUNK": ("C1_ARMTRUNK",)}
abl = {}
arm_mod.use_deform_preserve_volume = False
for ht in (120.0, 135.6, 156.0, 166.0):
    row = {}
    for fam, pats in [("none_off", ())] + list(FAMS.items()):
        pose(ht)
        active = {k.name: round(k.value, 3) for k in shoulder_keys if k.value > 1e-3 and any(p in k.name for p in pats)} if pats else {}
        for k in shoulder_keys:
            if pats and any(p in k.name for p in pats):
                k.value = 0.0
        bpy.context.view_layer.update()
        m = metrics(evaluated())
        row[fam] = {"rear_pinched": m["r_rear"]["pinched_lt_0.5"], "rear_p5": m["r_rear"]["area_p5"],
                    "shoulder_pinched": m["r_shoulder"]["pinched_lt_0.5"], "active_keys": active}
        print("R68A", ht, fam, json.dumps(row[fam]), flush=True)
    abl[f"{ht:g}"] = row
(OUT / "r68_family_ablation.json").write_text(json.dumps(abl, indent=1))
print("R68A_DONE", flush=True)
