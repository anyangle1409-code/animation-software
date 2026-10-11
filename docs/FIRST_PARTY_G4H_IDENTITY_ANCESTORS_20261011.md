# G4h — retain Work glTF scene grouping, allow only verified identity mesh ancestors

**11 October 2026; Chat Lane G Work-original format support; prototype-only and not anatomy approved.**

## Finding from REAL Work W1 pilot asset

The authored Blender source GLB at [PR #68 artifact 11706909894](https://github.com/anyangle1409-code/animation-software/actions/runs/38153765790/artifacts/11706909894) has 18 skinned primitive meshes and six real source clavicle/scapula/humerus controls. Every mesh is nested in Blender's ordinary `functional_shoulder_controls` glTF scene group, a **zero-transform / identity-only** wrapper. The original #70 pilot GLB adapter incorrectly requires every skinned mesh node to appear directly in `scene.nodes`, preventing even mathematically identical grouped geometry. Work's joint hierarchy is real source data; the Blender asset must not be edited or bones recentered to satisfy this artificial software limit.

## First-party fix, strict pilot only

- New `src/viewer/firstPartyGlbIdentityAncestorGate.mjs` independently checks the entire glTF parent graph: one parent per node, no cycles, no invalid/self/duplicate child pointers, scene roots themselves not nested and every skinned mesh reachable from an explicit scene root.
- A mesh may be nested **only if every parent between it and the active scene root has identity transform** (zero translation, [0,0,0,1] quaternion, unit scale or exactly identity matrix) and no mesh/skin or unsupported fields. Nonidentity transforms **fail closed** instead of being silently applied or ignored. Distinct multi-skin and actual model asset body transforms are deliberately not accepted here.
- Only while checking one primitive through the pre-existing strict GLB accessor/weights/indices loader, the adapter moves this verified identity-grouped mesh node to the root of a **temporary structured-cloned validation GLB**. All original GLB bytes, source mesh coordinates, original skin nodes, inverseBindMatrices and actual source joint parent/child hierarchy remain untouched. This changes no original Blender model.
- The original non-pilot strict importer still enforces direct scene-root meshes. The new scope is behind existing `allowProvisionalPilot:true` with the unchanged ≤1 MiB, 24-mesh diagnostic budget and no clinical/production sign-off.
- Acceptance metadata explicitly reports verified identity-only source grouping and `sourceBoneHierarchyChanged:false`. This flag **does not prove glTF/Y-up source motion-world registration, valid anatomical clavicle rhythm or real human appearance**.

## Verification

Node tests use a freshly authored full **18-mesh source pilot GLB** behind an identity-only scene wrapper, check every original mesh survives, verified source bytes remain unchanged, old strict mode rejects it and nonidentity translation/rotation/scale/matrix, double parents, hidden cycles, unreachable nodes and forged validation graphs fail closed. Existing G4f, source GLB/rig checks run alongside.

CI additionally downloads the **same exact real original Work artifact** (run 38153765790), verifies each publicly released GLB/PNG source hash (private .blend file intentionally excluded), and re-runs the first-party importer. This stage does not promise **full acceptance of real Work GLB**, which also declares double-sided materials, roughness=0.4 and missing UV0 for untextured surfaces. The actual returned current next reject/error is recorded as machine JSON so future Chat tasks can address genuine source needs in order.

See [Chat overnight verified ledger](https://github.com/anyangle1409-code/animation-software/blob/codex/g4g-real-work-shoulder-glb-audit-20261011/docs/CHAT_LANE_G_OVERNIGHT_LEDGER_20261011.md) and [Work's W1 source PR #72](https://github.com/anyangle1409-code/animation-software/pull/72). No final human model, soft-tissue deformation, real load dynamics or independently reviewed rights are yet ready.
