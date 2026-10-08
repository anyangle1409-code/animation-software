# Hyoid body axis review — 2026-10-08

CONFIRMED label correction; local body pose and whole hyoid geometry remain PROVISIONAL.

Primary DOI 10.1038/s41598-025-85518-w: Table 1 printed page 3 defines CC-prime as AP thickness. Figure 1A printed page 4 shows the BB-prime minor axis vertically across the body; Figure 1B shows separate CC-prime thickness. Results printed page 6 provide the male means. The old `body_AP_length=11.32` mapping was incorrect. Source numbers are unchanged; map local X width=24.3, Y AP thickness=6.99, Z minor-axis extent=11.32 mm. Local Z is an orientation convention for this dimension check; neutral tilt is still unresolved.

The retained pre-fix run demonstrates that positive-size/topology tests passed while missing the axis swap. `hyoid_axis_before_fix.txt` contains its regression failure. Six dimension extent markers were saved/reloaded in Blender 5.2.1 LTS. They are neither anatomical landmarks nor a whole-bone envelope. `blender_verification.json` records errors and hashes. No canonical candidate, osseous joint, global placement or completed gate is claimed.

Reproduce from repository root with fresh immutable output paths:

```bash
python -m unittest scripts.test_canonical_hyoid_geometry
/tmp/hgpt-bpy/bin/python scripts/anatomy_fit/check_hyoid_body_axes_blender.py --scratch-blend /tmp/hyoid_axes_review_002.blend --out /tmp/hyoid_axes_review_002.json
```

126 relevant tests passed: 79 canonical and 47 source/scapula/rib/shoulder tests. Target-selection, atlas and carpal-axis validators passed their limited scopes; freeze_ready=false. The known earlier whole-project legacy fixture failures remain documented in work_bpy_preflight_20261008_001. Production geometry, weights, runtime and a003 are unchanged.

Essential hyoid blockers: independently matched measurements/stature context; body/cornu landmark shape and neutral tilt; canonical cervical placement. C3 level alone does not determine AP position. Source means do not uniquely determine a full 3D hyoid. Other regional gates remain open as recorded in current readiness and target selection. Historical preflight reports remain immutable.
