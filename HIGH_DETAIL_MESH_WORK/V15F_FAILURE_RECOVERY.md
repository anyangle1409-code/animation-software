# V15f failure recovery — local ring/pinky reconstruction

Use this only for V15f. General export/runtime failures still use
`V15_FAILURE_RECOVERY.md`.

The rule is: fix the owning topology problem; do not weaken the gate.

## 1. General invariant failure

Symptoms:
- `general_invariants_pass = false`
- stable/source ID failure
- protected contact movement
- non-digit movement
- original digit weight-row change
- new nonmanifold/degenerate/boundary regression

Action:
1. stop propagation immediately;
2. read `reports/audit_v15f_deep_hand_rebuild_blender.json`;
3. restore the last good checkpoint if the failing operation is not trivially local;
4. keep every original tracked vertex;
5. never repair this by reassigning/remaking tracking IDs to new geometry;
6. never change protected contacts or source weights;
7. rerun the same incremental gate before continuing.

## 2. Scope leak — another finger moved

Symptoms:
- `only_ring_L_original_positions_changed = false`
- `only_approved_sequence_digits_changed = false`
- Stage A says index/middle moved

Action:
1. do not accept the edit even if the target finger looks better;
2. inspect selection/proportional-edit/mirror settings;
3. restore the unintended fingers exactly from the last checkpoint/V13e-derived state;
4. disable any tool setting that crosses the intended local selection;
5. rerun the target digit gate.

Do not expand the allowed scope merely to make the operation pass.

## 3. >100° severe-fold regression

Symptoms:
- total >100° folds exceed V13e;
- selected digit >100° fold count increases.

Action:
1. use the V15f sidebar `>100°` selection for that digit;
2. toggle hotspot guides;
3. inspect face orientation/edge flow around each severe edge;
4. prefer a small face/edge reconstruction around retained original vertices;
5. remove accidental razor creases/pinched triangles;
6. preserve intended knuckle volume;
7. rerun the incremental gate.

Do not flatten the entire joint to eliminate a single fold.

## 4. >35° / >50° sharp-length ratio worsens

Symptoms:
- selected digit fold count may be acceptable;
- >35° or >50° sharp-length ratio is higher than V13e.

Action:
1. inspect `Cross-band >35°` first;
2. inspect `Longitudinal >35°` separately;
3. if cross-band concentration is high, rebuild the local circumferential band
   into cleaner longitudinal/circumferential flow;
4. if longitudinal concentration is high, inspect for a side ridge/facet rather
   than adding joint loops;
5. use PIP/DIP hotspot groups to determine whether the issue is joint-local;
6. add only the minimum local support geometry required;
7. rerun the same digit gate.

Do not repeat V15e's broad joint subdivision strategy.

## 5. Metrics pass but the local surface still looks segmented

Action:
1. checkpoint the metric-passing state;
2. inspect the solid surface from palm/back/oblique views;
3. use cross-band hotspot groups as a guide, not as an automatic verdict;
4. make only a further small local topology improvement;
5. rerun the digit gate;
6. keep the prior passing checkpoint if the visual attempt makes metrics worse.

Metrics are no-regression guards, not visual acceptance.

## 6. Ring-left proof repeatedly fails

After two materially different **local topology** attempts fail on ring_L:

1. preserve both attempts/checkpoints;
2. do not propagate either strategy;
3. do not fall back to whole-core radial smoothing/subdivision;
4. write the exact failing metrics and hotspot pattern into the session handoff;
5. if safe, try a third approach only if it is genuinely different in topology;
6. otherwise stop this topology branch for a subjective/technical reassessment.

The objective is to avoid spending the whole Work window repeating the same
failed geometry idea.

## 7. Ring-left passes but mirrored/right attempt fails

Do not assume perfect source symmetry.

Action:
1. keep the left passing checkpoint;
2. work the right source surface independently using the same topology principle;
3. inspect right-side hotspot orientation/counts;
4. do not force exact coordinate mirroring if it creates a right-side fold;
5. preserve bilateral appearance, but let local triangulation/edge flow follow
   the actual source surface.

## 8. Pinky fails after rings pass

Keep the passing ring checkpoint.

Pinky has the highest inherited >35° sharp-length ratio, so a visually rough
pinky is not automatically a new regression. The gate asks it to be no worse
than V13e while the local silhouette improves.

Do not disturb passing rings while solving pinky.

## 9. Stage A fails after all four incremental gates passed

This means the combined state exposes a global/per-digit issue not caught at the
individual checkpoint sequence.

Action:
1. read `reports/v15f_stage_a_gate.json`;
2. identify only the failing digit(s);
3. preserve all passing digits;
4. repair the failing digit(s);
5. rerun their individual gate(s);
6. rerun Stage A.

Do not move to index/middle until Stage A passes.

## 10. Stage A passes

Immediately:
1. save a checkpoint;
2. record Stage A as passed;
3. run `V15F_STATUS.bat`;
4. inspect index/middle only;
5. do not rework passing ring/pinky without new evidence.

## Hard prohibition

Never respond to a V15f failure by changing:
- V13e/V8 baselines;
- frozen hierarchy;
- collision/contact thresholds;
- exercise mechanics;
- grip solution;
- equipment transform;
- retargeting;
- production reference.

V15f is a mesh-topology phase.
