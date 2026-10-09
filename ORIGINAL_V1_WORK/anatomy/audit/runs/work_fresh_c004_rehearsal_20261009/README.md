# Fresh c004 skeleton-only rehearsal — 9 October 2026

Diagnostic replay, not new anatomy, c005, canonical promotion or character acceptance.
Blender 5.2.1 LTS / Python 3.13.16 / NumPy 2.5.3. Empty scene: no skin/body mesh.

Commands executed from repository root:
```
/tmp/hgpt-bpy/bin/python scripts/anatomy_fit/cp3_rehearsal_blender.py build --record ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json --out-blend /tmp/hgpt-c004-work-20261009.blend
/tmp/hgpt-bpy/bin/python scripts/anatomy_fit/cp3_rehearsal_blender.py capture --blend /tmp/hgpt-c004-work-20261009.blend --out /tmp/hgpt-c004-work-capture-20261009.json
python scripts/anatomy_fit/cp3_roundtrip_compare.py --record ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json --capture /tmp/hgpt-c004-work-capture-20261009.json --out /tmp/hgpt-c004-work-roundtrip-20261009.json
/tmp/hgpt-bpy/bin/python scripts/anatomy_fit/run_isolated_tests_blender.py --source-blend /tmp/hgpt-c004-work-20261009.blend --record /tmp/hgpt-c004-work-movement-record-20261009.json --out-blend /tmp/hgpt-c004-work-movement-20261009.blend --out-dir /tmp/hgpt-c004-work-isolated-20261009
python scripts/anatomy_fit/solver_blender_agreement.py --record /tmp/hgpt-c004-work-movement-record-20261009.json --samples /tmp/hgpt-c004-work-isolated-20261009/isolated_samples.json --label work_c004_fresh_bpy_20261009 --out /tmp/hgpt-c004-fresh-solver-agreement-20261009.json
```

The scratch movement record changes ONLY the generated blend hash in provenance and adds a diagnostic label; bones, skeleton inputs and markers remain exactly c004. All original assets remain unchanged. Gzip files retain raw inputs, construction and animated blends, fresh capture, movement report and all frame samples; manifest binds raw/compressed SHA256.

Construction roundtrip PASS: 206 bones/427 markers, endpoint error 5.872660896281533e-8 m; centre error 1.9924837642947718e-7 m; frame component error 6.282479495800519e-7. Storage tolerances only. Roll mismatch remains reported, not anatomically accepted.

135/135 movement implementation integrity checks PASS; 41 Blender mirror pairs PASS and two side-specific-amplitude pairs solver-only. Independent agreement AGREE: 9,575 frames, 13,509 composed deltas, 49,991 channels; zero series drift/evaluation/measurement failures; worst delta component 1.4471605316312974e-6.

CP2 still FAIL (8 PASS, 1 FAIL, 1 UNVERIFIED, 1 INFO): legacy spine gaps and contact envelopes remain unresolved. These tests do not accept bone dimensions, articular surfaces, physiological amplitudes, contacts or production skinning.
