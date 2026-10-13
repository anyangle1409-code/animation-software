# Claude: first Blender session, prepared without model edits

Start with the latest live `docs/CLAUDE_ORIGINAL_V1_HANDOFF_20261013.md` and owner plan PR48. Native files come from the verified handoff archive; code comes from a full repository clone. Do not run supplement scripts alone: imports and candidate source records need the repository. Do not begin from the rejected DQ scene as the selected solution.

## 1. Establish identity before editing

Check live PR105/106/107/108 successors and Claude's own branch. Make an isolated new branch and fresh BLEND copy; choose a genuinely unused candidate revision. Historical assets already include r96–r102 work, so do not assume r97 is available. Preserve all comparators.

Verify the selected file SHA against `docs/CLAUDE_ORIGINAL_V1_ARTIFACT_MAP_20261013.json`. The declaration/readiness validator checks hash **format**, not the selected file bytes. Independently hash the actual file before using it; a `ready:true` schema result alone does not prove parent identity or anatomy.

In the full repository, first run the existing unfilled declaration preflight:

```bash
python scripts/original_v1_shoulder_foundation_readiness.py ORIGINAL_V1_SHOULDER_FOUNDATION_DECLARATION_TEMPLATE.json --out new_template_preflight.json
```

Expected: exit1 / `ready:false` / `STOP` with seven missing declaration fields. This was executed on13October; contract/ledger/human-manifest validators added no other errors in this invocation. That is validation behavior, not acceptance of source evidence. Do not reuse an existing output path: the tool refuses output collisions.

Fill a new candidate-specific declaration with: target revision, actual parent revision/hash/path, allowed regions/bones, topology intent, weight intent, protected regions and stop conditions. Explicitly protect the original206source and original67runtime; copied runtime or influence permissions do not authorize edits to source anatomy. Use exact vertices/repair masks and source Git SHA in a companion scope record; the legacy validator does not enforce all those fields. Keep it a draft until Claude has actually selected the parent/scope; no prefilled `ready:true` claim is supplied.

## 2. Reproduce the precise foot failure

Open `HomeGymPT_ORIGINAL_v1_INDIVIDUAL_TOE_TRIAL.blend`, SHA256 `5eab3dad1338b90e98f27076f4ed181785029d35e0066312f2d0511031e46316`.

| Item | Exact current value |
| --- | --- |
| Trial skin | `HGPT_BODY_TOE_SEGMENT_TRIAL` |
| Trial rig | `HGPT_TOE_SEGMENT_RUNTIME_TRIAL`,95controls |
| Failed movement | `trial_toe1_01_l`,+15°localX implementation probe |
| Anatomical side | Right, because native suffix_l maps anatomical right−X |
| Reversed-orientation triangle |15123 |
| Vertex IDs |1921,15350,8310 |
| Neutral forward range |207.221–214.090mm |
| Influence pattern | Two corners blend foot_l/digit2; one corner foot_l/hallux. Exact values in failure JSON. |

This mapping was freshly verified on the final40mm-root candidate, not merely copied from the25mm intermediate. The native file SHA remains unchanged. See `docs/reviews/CLAUDE_FINAL_TOE_FAILURE_LOCATIONS_20261013.json`.

The mixed digital ownership is a hypothesis for the web/root refit. Web skin can legitimately share digit influences: do not assign all three vertices to hallux just to pass one triangle. Inspect one-ring neighbours, root topology and neutral volume; preserve individual movement isolation and neutral grounding. No further blind root-taper sweep.

For selection only, on a fresh copy in Blender's Python Console:

```python
import bpy
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
obj = bpy.data.objects['HGPT_BODY_TOE_SEGMENT_TRIAL']
bpy.ops.object.select_all(action='DESELECT')
obj.hide_set(False)
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
for v in obj.data.vertices:
    v.select = v.index in {1921, 15350, 8310}
bpy.ops.object.mode_set(mode='EDIT')
```

Then use Frame Selected in the viewport. This selects vertices; it does not move geometry. Do not save selection over the comparator. The IDs are bound to the pinned input topology; after an intentional topology change regenerate candidate-bound neighbourhood/landmark mappings rather than claim these old indices still identify the same surface.

Run the current preserved regression from the repository with Blender `--python-exit-code 1` and `scripts/test_original_toe_articulation_blender.py`. Baseline expectation remains4PASS/1FAIL. Fix rest shape/root transitions in a declared local candidate around unchanged source stations. The280mm shortening remains blocked; shape repair and individual controls are separate deliverables.

## 3. Use the actual source station map

`docs/reviews/CLAUDE_NATIVE_FOOT_STATIONS_20261013.json` captures52actual unchanged native foot reference controls and28toe trial controls, world heads/tails, parent names and control→reference correspondence. All28control endpoints match their native references exactly in captured float32 coordinates;52native reference endpoints match the existing c004 record within0.0000151mm. This establishes implementation correspondence, **not** anatomical validity.

All52reference controls retain low-confidence status. These are control stations, not independently segmented bone surfaces, functional axes or cartilage centres. The map is useful for avoiding accidental source movement and checking bilateral edits. Do not turn coordinate agreement into a280mm target permission.

## 4. Inspect shoulder failure before choosing a repair

Open `HomeGymPT_ORIGINAL_v1_SHOULDER_JOINT_REFIT_TRIAL.blend`, SHA256 `a48ee389a064927f740b5ea294b7afed3ef1616cbe8ac6c121867b86581680c2`. Trial skin `HGPT_BODY_SHOULDER_REFIT_TRIAL`; copied rig `HGPT_SHOULDER_JOINT_REFIT_TRIAL`. Source markers are fitted-unverified. Verify SC/AC/GH mechanics, scapular motion and axial-rotation states before accepting this provisional rig as a repair foundation.

Primary scan clarification: the ISB scapular **segment frame** origin is AA, distinct from the current AC **control pivot**. Keep both explicitly named; no automatic source/control relocation. See the reference brief and page-bound source review.

| Region | Triangle vertex IDs | Baseline fact |
| --- | --- | --- |
| Front shoulder |4647,13572,4773 | Linear trial at authored160°area ratio0.009709; native guard FAIL. |
| Rear shoulder |4865,13619,4748 | DQ experiment at same pose0.014285; rear guard FAIL. |

Select these IDs on the shoulder trial body using the selection-only pattern above. Refer to `docs/reviews/ORIGINAL_V1_SHOULDER_SKIN_DISTORTION_20261013.json` and `ORIGINAL_V1_SHOULDER_VOLUME_DISTORTION_20261013.json` for actual locations/influences. Preserve both guards and check stretch, volume and actual views; the0.1area guard is an engineering severe-collapse check, not physiological authority.

Weights-only foundation first, with test-path shape-key states explicitly recorded. Do not indiscriminately zero the Basis key (its Blender value1 is normal), silently disable unrelated correctives or add a large shoulder morph to conceal failed mechanics/topology/weights. Preserve original key data. Only after foundation acceptance consider rotation-aware deformation and minimal residual soft-tissue correctives.

## 5. First reviewable output

Make one bounded foot or shoulder correction at a time, not a combined untraceable replacement. Record changed vertex/group/bone/key counts, exact parent/source/export hashes, source protection comparisons and known defects. Produce actual neutral and movement before/after phone images at matching camera scale. Show rest stance separately from deliberate toe-lift or overhead probes.

For shoulders, begin debugging neutral/early/mid/peak/return, then meet the existing full flexion/abduction and internal/neutral/external rotation matrix using reference-supported states. Endpoint-only160°and short-arc direction matching do not validate human movement. Include front/three-quarter/side/rear/axilla views, check deltoid/pec/neck/back continuity and unrelated body regions. No arbitrary numerical axial-rotation ROM target is supplied.

Post the new candidate/actual images and exact remaining failures to PR26. Keep original/model production, scientific readiness and owner acceptance flags unchanged. Codex supplies reference/checkpoint support without competing Blender edits.
