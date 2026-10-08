# Contact clearance validation fixtures

Synthetic geometry only. No anatomical bone/contact target is created or accepted. A centre and four cardinal points miss the diagonal intersection in the adversarial fixture. The analytic minimum covers the whole common ellipse; Blender independently samples its rim at 128 points including the known minimum direction. This does not establish curved anatomical contact or actual overlapping footprint domains.

```sh
python scripts/anatomy_fit/build_endplate_clearance_sensitivity.py
python -m unittest scripts/test_canonical_endplate_clearance.py scripts/test_shoulder_target_constraints.py scripts/test_shoulder_target_invalid_geometry.py
/tmp/hgpt-bpy/bin/python scripts/anatomy_fit/check_endplate_clearance_blender.py --scratch-blend /tmp/HGPT_synthetic_endplate_clearance_20261008_002.blend --out /tmp/endplate_clearance_blender_002.json
```

Use fresh immutable output paths. `shoulder_invalid_before_fix.txt` retains three real initial validator failures; the final validator rejects these inputs. Neither sweep footprint radii nor fixture centre gaps are selected anatomy.
