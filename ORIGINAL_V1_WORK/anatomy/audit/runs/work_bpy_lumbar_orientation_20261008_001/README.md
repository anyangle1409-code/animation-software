# Lumbar local orientation fixture

This contains no whole skeleton, vertebral positions or thicknesses. Source body/disc angle semantics, closure and independent trapezoid sign are checked by `scripts/test_canonical_lumbar_wedge_decomposition.py`. All local helpers are labelled not canonical; their common fixture origin is not an anatomical centre.

Reproduce with Blender bpy Python (use a fresh output path):

```sh
python scripts/anatomy_fit/lumbar_wedge_decomposition.py
python -m unittest scripts/test_canonical_lumbar_wedge_decomposition.py
/tmp/hgpt-bpy/bin/python scripts/anatomy_fit/check_lumbar_frames_blender.py --scratch-blend /tmp/HGPT_lumbar_orientation_only_20261008_002.blend --out /tmp/lumbar_orientation_verification_002.json
```

The initial test design used the wrong inferior-slope expectation (−11.44°), corrected before implementation verification by the posterior-positive frame and independent trapezoid calculation. It is not an anatomical failed candidate or discarded Blender run.
