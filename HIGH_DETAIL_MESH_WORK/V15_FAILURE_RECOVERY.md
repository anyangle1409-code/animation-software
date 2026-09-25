# V15 failure recovery decision tree

This is a **repair guide**, not permission to loosen a guard.

If a V15 command stops, fix the first failing stage and rerun from that stage.
Do not compensate by changing exercises, grips, equipment, retargeting, the
frozen hierarchy or validation thresholds.

## 1. START_V15_HAND cannot find Blender

Symptom:
- `Blender not found. Set BLENDER_EXE...`

Action:
- point `BLENDER_EXE` at the installed `blender.exe`, or add Blender to PATH;
- rerun `START_V15_HAND.bat`.

Do not change project files.

## 2. V15 preparation refuses to overwrite the Blend

Symptom:
- prepared V15 Blend already exists.

Meaning:
- an attempt is already preserved.

Action:
- open that existing attempt if it is the one being continued;
- if starting a genuinely new attempt, use a new candidate version rather than
  deleting/overwriting the old one.

## 3. Blender invariant audit fails

Read:

`reports/audit_<version>_blender.json`

### Missing original source IDs

Meaning:
- a topology operation deleted one or more established V13e/V8-source vertices.

Action:
- restore/rebuild that local region so every original tracked vertex survives;
- rebuild faces/edge flow around retained vertices and add new vertices instead.

Do **not** invent replacement IDs after deletion.

### Protected push-up vertex moved / weight changed

Meaning:
- one of the authoritative contact anchors was altered.

Action:
- restore the exact protected position and deform row from V13e;
- reshape around the anchor.

Do not adjust push-up motion or floor height.

### Non-digit geometry moved

Meaning:
- the edit leaked into palm/thumb/wrist/body outside the V15 scope.

Action:
- restore the affected source vertices from V13e;
- keep this candidate limited to index/middle/ring/little shaft/joint surfaces.

### Original digit displacement exceeds the allowed envelope

Meaning:
- this is no longer a controlled local rebuild.

Action:
- reduce the local shape change or start a fresh candidate.
- Do not raise the envelope simply to pass.

### Degenerates / >2-face nonmanifold edges / extra digit boundaries

Action:
- repair topology locally in Blender;
- preserve the stable vertex IDs and protected anchors;
- rerun the audit before export.

## 4. Export-prep failure

Read:

`reports/prepare_<version>_export_blender.json` if it exists.

### Baseline tracking ID missing or duplicated after resolution

Meaning:
- topology editing destroyed/duplicated an established starting vertex in a way
  the export preparation cannot safely distinguish.

Action:
- repair that local topology in the editable Blend.
- Do not patch tracking IDs by hand to conceal a deleted source vertex.

### New vertex is more than 12 mm from V13e surface

Meaning:
- likely stray/accidental geometry or an excessive departure from the local hand.

Action:
- inspect that vertex/region;
- delete stray geometry or bring the local rebuild back inside the hand surface envelope.

Do not increase the 12 mm repair envelope just to export.

### UV/weight interpolation fails

Meaning:
- the new geometry cannot be mapped safely to a nearby V13e triangle.

Action:
- inspect only the reported new vertices.
- If the topology is legitimate, assign sensible UVs/normalised DEF weights
  locally and rerun.

Do not repaint unrelated V13e vertices.

## 5. Stable-ID GLB packer fails

Typical causes:
- original source vertex missing;
- UV topology cannot map;
- new vertex has unusable skin data;
- non-triangular export copy survived unexpectedly.

Action:
- fix the specific exported local topology/metadata issue.
- Do not change the production GLB container, rig or materials.

## 6. Protected floor GLB guard fails

Read the generated `hand_floor_guard_*.json`.

Required:
- 682 protected positions unchanged;
- protected joint rows unchanged;
- protected weight rows unchanged.

Any failure is a candidate failure. Restore the hand geometry/weights; do not
change the guard.

## 7. Frozen 614033b guard/exercise failure

Read:
- `reports/<version>_rig63_guards.log`
- `reports/<version>_rig63_exercises.log`

Rules:
- bone/equipment matrix changes are not allowed for a mesh-only hand candidate;
- technique failures are not fixed by editing exercise definitions;
- push-up floor difference must remain exact.

If the failure is caused by V15 geometry, fix/reject V15.
If the frozen harness itself is unexpectedly unavailable/corrupt, restore the
known `614033b` validation checkout; do not substitute current source for the
historical comparison lane.

## 8. Seam/fold audit worsens

Compare V13e and V15 in `reports/hand_seam_audit.json`.

A deeper rebuild must not create:
- new fingertip holes;
- more open seam behaviour;
- new severe folds.

Fix the topology in the affected digit. Do not hide it with camera, material or
normal changes.

## 9. Visual-change gate does not exceed rejected V14e

Read:

`reports/<version>_visual_change_metrics.json`

This gate is calibrated against the actual V13e/V14e boards.

Meaning:
- V15 repeated the V14e problem: the topology operation may be technically
  substantial but the visible hand has not changed enough.

Action:
- **do not add another generic smoothing/subdivision pass**;
- return to the actual shaft/joint patch;
- redirect the silhouette/cross-section/longitudinal edge flow;
- use the per-digit `*_SHARP`, `*_PIP_ZONE`, `*_DIP_ZONE` and
  `*_CORE` selections;
- preserve the anchors and contacts.

A false result is not permission to lower the calibration target.

## 10. Latest-source integration finds a new regression

Read:

`reports/current_source_<version>/integration_report.json`

Look for:
- new failing gate files relative to V13e;
- increased failed-test count;
- missing measurement coverage;
- >0.05 mm change to body/equipment measurements that should be identical for
  a hand-only edit.

Action:
- determine whether the changed hand is actually involved.
- If V15 caused it, fix/reject V15.
- If source HEAD advanced and changed the baseline itself, rerun V13e and V15
  on the **same fetched HEAD** and compare again.

Do not merge current source into the mesh branch and do not modify current
exercise mechanics to accommodate V15.

## 11. Everything technical passes but anatomy still looks wrong

This is a valid rejection.

Preserve the candidate and start the next version from V13e or the explicitly
chosen accepted hand source.

Do not refit grips merely because the tests are green.

## 12. Everything passes and the hand visibly improves

Stop.

Record:
- candidate hashes;
- source HEAD used for integration;
- V13e/V15 boards;
- seam/fold result;
- visual-change metrics;
- remaining visible defects.

Only after explicit visual acceptance should `PHASE_C_GRIP_REFIT_PLAN.md`
be activated.
