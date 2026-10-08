# Relative glenoid rim fixture

No global thorax placement or GH centre is inferred. These helpers mark measured rim centroids and orientations only, with outward normals on both sides and determinant +1 rotations.

```sh
python scripts/anatomy_fit/glenoid_rim_frame.py
python -m unittest scripts/test_canonical_glenoid_rim_frame.py
/tmp/hgpt-bpy/bin/python scripts/anatomy_fit/check_glenoid_frames_blender.py --scratch-blend /tmp/HGPT_relative_glenoid_rim_20261008_002.blend --out /tmp/glenoid_rim_verification_002.json
```

Use fresh output paths. `ambiguous_plane_before_fix.txt` records a real false-pass weakness: the initial fitter accepted isotropic tetrahedral rim points with no unique plane. The final fitter rejects that ambiguity. This failure is a synthetic validator test, not a rejected anatomical bone candidate.
