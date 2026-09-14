from pathlib import Path

path = Path('AI_CHANGELOG.md')
text = path.read_text(encoding='utf-8')
marker = '## Unreleased\n'
entry = r'''

### ChatGPT — 2026-09-14 — functional muscle paths and whole-body biomechanics gate

Audited the entire current muscle subsystem instead of limiting validation to the bicep curl. The audit confirmed **22 trainer-level muscle groups** and found a real engine defect: `forearm_flexors` and `forearm_extensors` declared that they act on the hands/wrists, but both endpoints were attached to the forearm bone. Their measured length change across every current exercise was effectively zero (floating-point noise around `2e-15`), so the overlay could highlight them but wrist motion could not make them contract or lengthen. The same audit exposed two straight-chord limitations worth fixing before scaling the library: the triceps path could shorten during elbow flexion instead of lengthening, and the quadriceps chord could cut across a deeply flexed knee instead of following the anterior/patellar route.

Validated feature commit `bbb6600a0e30b062925e763e592e192b70a8e0fc` adds optional anatomical `via` / wrap points to `MuscleDefinition`, constructs a full functional origin -> via point(s) -> insertion path, and drives `restLength`, stretch and bulge from that path while retaining the inexpensive fitted ellipsoid as the visible belly. Mirroring now includes via points and the containment fit includes every bone used by the path. This is intentionally an incremental biomechanics upgrade: curved functional paths are now correct enough to drive contraction, while the rendered overlay remains the existing inexpensive fitted form rather than becoming a general muscle-mesh simulator.

The forearm flexors/extensors now cross onto `hand_l`/`hand_r`, with a 0.72 belly taper so the visible mass remains primarily in the forearm while the functional tendon crosses the wrist. Triceps now has a posterior elbow via point (`upperarm_l`, approximately `[0.002, 0.292, -0.035]` before mirroring), and quadriceps has an anterior-knee via point (`thigh_l`, approximately `[0, 0.415, 0.05]`). A first 0.68 forearm taper trial was **rejected by the existing geometry invariant** because the visible belly ended about 2.4 mm too far from its functional insertion tolerance; no engine change was committed from that failed run. The 0.72 calibration was rerun through the complete gate rather than weakening the invariant.

Added permanent `src/muscles/functions.test.ts` coverage that requires every muscle group to physically span every joint listed in its `actsOn` metadata; verifies isolated elbow flexion shortens biceps while lengthening triceps; verifies wrist flexion/extension makes forearm flexors and extensors oppose one another; and verifies deep knee flexion lengthens quadriceps while shortening hamstrings. Existing all-exercise skin-containment, belly attachment, mirroring, biceps contraction, rig, retarget, equipment, export and movement-certification tests remain intact. Final Node 22 validation: `npm run typecheck` passed; `npm test` passed **211 tests with 1 optional real-character diagnostic skipped (212 total) across 21 files**; `npm run build` passed with only the pre-existing >500 kB Vite chunk advisory.

Added `docs/STUDIO_CAPABILITY_ROADMAP.md` to define the end target as a specialist **exercise-animation authoring studio with Blender-like control**, not a general Blender clone. Priorities are: biomechanical core, rig/pose controls, exercise timeline, hand/grip workspace, equipment/contact authoring, bounded corrective deformation, live diagnostics/approval, and template-driven scale. Sculpting, UV editing, texture painting, particles, compositing and arbitrary scene modelling remain deliberately out of scope. No exercise definition, retained bicep-curl motion, grip default, imported character asset, skin weights, retargeting algorithm, equipment attachment or candidate GLB was changed by this muscle-engine pass.
'''
if entry.strip() in text:
    raise SystemExit('handover entry already present')
if marker not in text:
    raise SystemExit('Unreleased marker missing')
text = text.replace(marker, marker + entry, 1)
path.write_text(text, encoding='utf-8')
