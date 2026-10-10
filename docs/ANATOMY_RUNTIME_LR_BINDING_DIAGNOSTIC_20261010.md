# Home Gym PT — anatomical/runtime side-binding preflight (2026-10-10)

## Independent read-only result

The original anatomical fit's own `conventions.world` defines anatomical LEFT
as **+X** in r95 Blender world metres (+Z up, face -Y), while its
`conventions.runtime_side_binding` states that anatomy left corresponds to
the existing `_r` legacy runtime suffix.

Independent source coordinates confirm this: a003 `humerus_left` lies near
+0.217 m X; the runtime rev2c `upperarm_l` lies at -0.215 m X and
`upperarm_r` at +0.215 m. Clavicle and femur likewise corroborate the
left/right side inversion. This is a mismatch in the **name-based alias
table**, not proof that anyone's visible current character is physically
mirrored; a future adapter may already perform a remapping.

### What the new report measures

- The full set of **206** unique anatomical IDs and the legacy **67** rig
  bone names are integrity-checked against pinned source records.
- **122 anatomical records** have sided runtime aliases, accounting for **130 separate alias links**; each link is tested against the actual
  endpoint X-coordinates in the canonical rig, plus their individual
  anatomical a003 bone endpoint X-coordinates. The current names are
  inverse-sided for all 130 links. Other aliases are explicitly absent or
  collapsed rather than assigned imaginary individual controls.
- Six independent anchor checks (clavicle, humerus, femur, both sides)
  verify that the inverse-name candidates lie on the correct physical side.
- For all 86 anatomical paired bones, bilateral pairing of single sided
  runtime mappings is checked.
- A name-only production mapping is **explicitly blocked**. The report
  provides candidate inverse runtime names only for *review*, not
  registration/retargeting.

### Execute without Blender

```bash
python scripts/anatomy_fit/runtime_side_binding_preflight.py --out /tmp/side_binding_report.json
python -m unittest -v scripts/test_runtime_side_binding_preflight.py
```

An optional **negative-control** call must exit **2** with the currently
unsafe direct name mapping:

```bash
python scripts/anatomy_fit/runtime_side_binding_preflight.py --require-name-safe --out /tmp/side_binding_report.json
```

Successful report production is *not* anatomical approval. These tests use
Python's standard library and do not consume Claude or Blender resources.

### Handoff to active laptop Work session

Do **not** rename canonical bones, invert any rig's geometry, remap mesh
weights, or merge this draft branch into production. Inspect the draft PR
and its JSON evidence; when Work reaches the separate runtime retargeting
stage, use an explicit source/anatomy-side to runtime-bone mapping table
built from the actual coordinates. Independently validate:

1. Complete world-axis coordinate conversion and its determinant/chirality;
   X-side agreement alone is insufficient to register the frames.
2. Both sides' anatomical centres and articulated transforms over motion
   sequences (not merely static endpoints).
3. Whether the existing runtime engine uses suffixes anatomically,
   geometrically, or through an already-existing side adapter.
4. Later Blender pose and skinning equivalence before any transfer or
   production freeze.

### Preservation and limits

Source a003, c001/c002/c003/c004, c005 approval state, 206-bone atlas,
production character, mesh, all Blender scene files and Work's branches
remain unchanged. A passed CI run means the static diagnostic and its
negative control are reproducible; it **does not validate 3D anatomical
fit or 427 articulations**.

Tracker readiness remains **0 READY / 9 PARTIAL / 3 BLOCKED**, with
pelvis source features pending actual reviewer bone identity and registration.
