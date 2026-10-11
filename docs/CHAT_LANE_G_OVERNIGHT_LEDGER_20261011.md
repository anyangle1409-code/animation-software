# Home Gym PT — Chat Lane G overnight execution ledger
**Started Sunday 11 October 2026; review target Monday 12 October 2026 (UK).**
**Purpose:** Answer a morning "update" with exact work, source PRs, tests, known blockers and the next executable task. This is not a claim of uninterrupted execution.

**Owner tasking:** Run Chat-owned software tasks when available, move to the next genuinely unblocked task after verified completion, preserve Work anatomical/Blender branch heads, do not infer correctness from synthetic tests, and keep the existing hourly continuation task enabled. The laptop battery/usage reset cannot be observed reliably from GitHub.

## Verified work already completed; don't repeat

| Lane | PR | Last audited result | Current release status |
| --- | --- | --- | --- |
| G4 | [#59](https://github.com/anyangle1409-code/animation-software/pull/59) | Source GLB SHA-256 and explicit rig/rest/rights handoff, CI success | Draft, prototype only |
| G4b | [#60](https://github.com/anyangle1409-code/animation-software/pull/60) | Authored bounded source pose-frame clip preflight, CI success | Draft, diagnostic only |
| G1e–G1f | [#61](https://github.com/anyangle1409-code/animation-software/pull/61), [#62](https://github.com/anyangle1409-code/animation-software/pull/62) | First-party embedded source PNG/GLB intake and real native Chromium PNG pixel proof | Draft, synthetic |
| G2d–G2e | [#63](https://github.com/anyangle1409-code/animation-software/pull/63), [#64](https://github.com/anyangle1409-code/animation-software/pull/64) | GPU four-influence skinned/textured original mesh and glTF sRGB transfer, exact-head CI green | Draft, synthetic |
| G4c–G4d | [#65](https://github.com/anyangle1409-code/animation-software/pull/65), [#66](https://github.com/anyangle1409-code/animation-software/pull/66) | Offline first-party movement intent and exact pose/equipment/side/grip/candidate identity guard, CI green | Draft, no real motion generation |
| G4e | [#67](https://github.com/anyangle1409-code/animation-software/pull/67) | Original GLB SHA/rest/PNG material handoff to true WebGL2, 3/3 CI green | Draft, synthetic |
| G4f | [#70](https://github.com/anyangle1409-code/animation-software/pull/70) | Explicit small 18–24-mesh pilot **synthetic** GLB decode/rest screen. Actual exact-head CI run 38157829464 SUCCESS | Draft; real Work GLB not yet accepted |
| App bridge | [PT-App #2](https://github.com/anyangle1409-code/PT-App/pull/2) | Source/PT exercise ID, diagnostic pose claim and untouched .webm fallback gate, exact-head CI 38174266587 2/2 GREEN | Draft; no live 3D PT UI |

## 11 October — real original Work asset intake (NEW)

A complete actual W1 **PROVISIONAL SHOULDER ONLY** CI ZIP has been retrieved from **[Work #68 exact-run artifact 11706909894](https://github.com/anyangle1409-code/animation-software/actions/runs/38153765790/artifacts/11706909894)**. This is an original Blender-produced project asset, not the final full-body human.

- ZIP contains 1 authentic **`PROVISIONAL_FUNCTIONAL_SHOULDER_v1.glb`**, 20 actual Blender PNG renders, `pilot_manifest.json`.
- Original GLB on this **precisely pinned** artifact is 280,956 bytes, SHA-256 **`fda9c5e653044988fd1e5c58fe352f074071c4be008eceba702bbbef96a4ea5f`**; matches the authored ZIP's `files_sha256`. Older Work PR description mentions a different file SHA (`90bc99...`) and size: do not reuse that earlier hash. The specific artifact is self-consistent.
- GLB has 18 meshes and 18 indexed triangle primitives, 4,572 source vertices, one shared skin, **six actual glTF joint nodes** (clavicle/scapula/humerus, left and right), 25 nodes overall, six source materials, seven author-labelled native pose records at 0/45/90/135/160/90/0.
- This Blender export uses a real **hierarchical glTF scene** with 18 mesh nodes beneath a named root and six TRS-transformed joint controls; source materials are `doubleSided:true`, `roughnessFactor:0.4`, and some untextured blade surfaces have no UV0.
- Existing G4f strict importer still requires all mesh nodes to be direct root nodes and flat one-sided roughness=1. Work's genuine Blender hierarchy and material parameters must **not** be destroyed to make synthetic tests pass.
- Source `pilot_manifest.json` explicitly marks anatomy, motion and production **UNAPPROVED**; native +Z/row-major source records and glTF exported Y-up/column-major source matrices require an independently checked basis and hierarchy transformation. Do not blindly relabel them.

**G4g current task:** `scripts/audit-original-work-shoulder-pilot.mjs` with dedicated GitHub workflow downloads the original exact CI artifact, verifies every authored source file SHA, executes the current first-party pilot importer against the **actual** untouched Work GLB and publishes **JSON diagnostics only** (never re-uploads Work's native/GLB model or images). [G4g draft branch](https://github.com/anyangle1409-code/animation-software/tree/codex/g4g-real-work-shoulder-glb-audit-20261011) based on verified G4f #70. Status at ledger creation: code committed, CI verification pending. Mark it complete only after run PASS.

## Next executable Chat-side tasks, in priority order

1. **Finish G4g real-file audit and CI**, correct actual test/manifest issues, record exact SHA and authentic first-party parser rejection; do not treat a known importer blocker as clinical error.
2. **G4h** fix bounded, standard glTF parent-child scene/world transform handling without relocating source joints or flattening skeleton geometry. Require exact reversible source hierarchy, cycle/double-parent protection, correct source skin palette with real Blender GLB; independently verify source world matrices vs inverse binds.
3. **G4i** support actual Work pilot's source `doubleSided`, original source roughness 0.4 and optional UV0 only for untextured material in the diagnostic renderer; no fake PBR approval, and do not change historical strict default importer behaviour.
4. Verify **all 18 original primitive draws** in actual Chromium using source Work GLB and first-party GPU bone palettes, capturing real native PNG and GPU/CPU parity. No synthetic-only signoff for a real character.
5. **App experimental viewer** behind explicit owner-gated preview and independent runtime SHA/rig/clip verification; no current PT media/prescriptions/304 videos replaced until proven rights, human movement/deformation and owner signoff.
6. **Review/edit completion ledger on every successful work run**; include exact commit SHA/PR/CI, per-stage status and next pending task. When Work #72+ produces a newer original GLB, recheck the source hash and update only genuinely changed asset-sensitive tests.

## Work lane boundary

Latest Work [#72](https://github.com/anyangle1409-code/animation-software/pull/72) at `f29fb92542430279e822ba4d2baa7d19ae406a67` supplies **authored costal scapula curvature** atop shoulder reach #71; documented author constraints remain provisional, no actual accepted whole-body muscle/skin mesh. This is **not a Chat-generated anatomy approval**. Historical full-source atlas 0 READY / 9 PARTIAL / 3 BLOCKED remains open; do not run duplicative CT research to fill Chat tasks. Skeleton is the source of truth, mesh fitted around it.

**Hard limits:** This conversation or automation cannot see laptop battery charge, ensure Windows never sleeps, or force OpenAI/Claude Work sessions to resume once their own usage ends. Hourly Chat task can continue through supported runs; record actual runs and never invent activity during gaps.
