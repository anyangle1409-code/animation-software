# Source-separated orientation fixtures

No centres, surfaces, disc gaps or skeleton candidate. Reproduce with a fresh output path:

```sh
python scripts/anatomy_fit/build_lumbar_orientation_sensitivity.py
python -m unittest scripts/test_canonical_lumbar_orientation_sensitivity.py
/tmp/hgpt-bpy/bin/python scripts/anatomy_fit/check_lumbar_frames_blender.py --source ORIGINAL_V1_WORK/anatomy/canonical_lumbar_orientation_sensitivity_p1.json --scratch-blend /tmp/HGPT_lumbar_sensitivity_only_20261008_002.blend --out /tmp/lumbar_sensitivity_verification_002.json
```

The paired source families preserve their different populations; they are not averaged or selected. All helper origins are synthetic, not anatomical positions.
