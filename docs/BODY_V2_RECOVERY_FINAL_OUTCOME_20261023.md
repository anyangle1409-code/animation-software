# Body v2 recovery — verified outcome, 2026-10-23

Status: **RECOVERED AND ACCESSIBLE; VERIFICATION FAILED; MUSCLE ATTACHMENT BLOCKED.**

This is a blocker handover, not anatomical or production approval. The final native measurement run [39927465329](https://github.com/anyangle1409-code/animation-software/actions/runs/39927465329) finished on 2026-10-23 at 10:09 BST (09:09 UTC). Its record job succeeded and committed results at `1decd3d663cdb62c54e42832dad40ab3ba203bb2`. Measurement code commit: `bd397362ff90323d66f3205cf78f943116f722a0`. W8 measurements are preserved from run39923681466 at `7c03e31307224d4b0224e5db354b663cdc8311a8`. Native environment: Blender 5.2.0 LTS, bpy5.2.0, Python3.13; historical benchmark source remains pinned `025d5f28fa7eba2064fba565b1c9b60119cdd2cb`.

## Completed

- Actual W8/v13s, v14 and separate experimental R120 Blender files reconstructed, source inventories inspected, and actual Blender front/back/side/three-quarter renders archived.
- Separately packaged accessible models, SHA256 manifest and discrepancy/render evidence: [download index](BODY_V2_RECOVERED_ACCESS_20261023.md), [machine-readable provenance](BODY_V2_RECOVERED_ACCESS_20261023.json). Access run39922636070 passed; v14 native bytes and render/evidence ZIP were independently downloaded and SHA256 verified.
- Native candidate diagnostics attempted all13paths for each candidate. Each measured12paths x9frames =108frames; grip failed for all3. These are attempted diagnostics, not13passing movements.
- V14/R120 nontriangle measurement blocker resolved without changing source polygons/coordinates. Native rest loop-triangle indices were frozen across every pose; evaluated topology changes reject. V14:419870source polygons/476126measurement triangles; R120:645944/695524. All13path rest tessellation hashes agree within each candidate.
- 18combined diagnostic, recovery and artifact-access regression guards passed locally and in cloud. Actual source-byte preservation is true for all candidates. No rest-bone-change errors occurred on12completed paths; grip terminates before the final per-path rest check and therefore is not claimed to have passed that check.
- Logs confirm only grip raised a path exception in the final run. Actual per-frame metrics exist for all12other paths. V14/R120 ZIPs were independently retrieved, their published SHA256 digests checked, and full108-frame reports inspected.

## Exact failed and blocked gates

| Gate | W8/v13s | v14 | R120 experimental |
|---|---|---|---|
| Native source inventory | PASS | PASS | PASS, measurement only |
| Structural archive counts | 5PASS/0FAIL | 6PASS/1FAIL:238065 vs238067 vertices | 4PASS/0FAIL, measurement only |
| Archive equivalence | FAIL:0PASS/4FAIL | FAIL/discrepancies retained | No approved archive equivalence |
| Measured movements | 12of13,9frames each | 12of13,9frames each | 12of13,9frames each |
| Grip solver | FAIL: no thumb placement within pair limit | Same FAIL | Same FAIL |
| Per-frame quality-failure records | 253 | 256 | 282 |
| Maximum collapsed triangles | 229 | 433 | 625 |
| Maximum stretched triangles | 3509 | 4261 | 9171 |
| Maximum intersecting pairs | 3499 | 3488 | 4648 |
| Zero-collapse/stretch/intersection gate | FAIL | FAIL | FAIL |
| Exact source bytes unchanged | PASS | PASS | PASS |
| Original67-bone production bridge | INCOMPATIBLE with77-bone authoring rig | Same | Same |
| Anatomical approval / muscle staging | NOT_GRANTED / BLOCKED | NOT_GRANTED / BLOCKED | NOT_GRANTED / BLOCKED |

Quality records count nonzero metric observations across frames, not distinct anatomical defects. Counts depend on mesh density and tessellation and must not be used to rank candidates across different topology. Measurements use unchanged R57 formulas and thresholds: collapse area ratio<0.1, stretch>2, and nonadjacent intersection pairs. Standing display and benchmark neutral poses differ; these results cannot be equated to archived standing-pose intersection counts. This adapter does not certify the production bridge.

W8 archive offset-array maximum differs3.5928599834mm vs0.01mm guard, and proportion-array maximum0.8375732899mm. Array correspondence is unestablished: these are not proven anatomical point displacements. Skeleton side-fit Y shift differs0.000431996mm. Full1skeleton/12W8/10v14 JSON differences remain archived. Unordered BMesh operations and newer defaults remain possible causes, not proven explanations.

## Preserved provenance and downloadable diagnostics

| Candidate | Native .blend SHA256 |
|---|---|
| W8 | `2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c` |
| v14 | `5969aa98122e267b6bdd94fdfaf6d2877a1b27f7ea8d11c6a8e078b467b0ff91` |
| R120 | `fb3b0acfc68bc59952b0fc6c45f7d7715717207fd9ba0b7f2b124e905ce2ddcb` |

- [W8 full diagnostics](https://github.com/anyangle1409-code/animation-software/actions/runs/39923681466/artifacts/12489875422), ZIP SHA256 `6853e820ac3431cc59cd4ea90a161d52e6c1b192a5e5aaec95c313d1f257aa3b`.
- [v14 full diagnostics and logs](https://github.com/anyangle1409-code/animation-software/actions/runs/39927465329/artifacts/12490363437), ZIP SHA256 `549db71c84bc2f2de5d3004144562d4642b9c7104737265c884bb0d7c7a23365`.
- [R120 full diagnostics and logs](https://github.com/anyangle1409-code/animation-software/actions/runs/39927465329/artifacts/12490334814), ZIP SHA256 `4d684611ada252809e63b081c9c9b4280cf98d13cb964a1fd4c629b8b88e8dc3`.

V14/R120 diagnostic artifacts expire2027-01-21. Model/render artifact retention is recorded in the access manifest; these are Actions artifacts, not permanent release assets. A draft prerelease is deliberately not created because reconstruction acceptance gates failed. Full combined summary: [JSON](BODY_V2_CANDIDATE_MOVEMENT_DIAGNOSTICS_20261023.json).

Rest measurement tessellation SHA256: v14 `89b516b30ad4672e450220edc960fceb32a94cf6e343461f1f8357d4d761b2b7`; R120 `377dbcd3e269a68f14e214cd571827a82b02b735fed66dd7b61fdcf1fe930a85`.

## Remaining and required evidence

1. Exact recovery is blocked by missing original archived .blend/topology/rest arrays or an independently established vertex correspondence. Obtain Claude's original W8 and v14 files if still available, with source revision/environment and SHA256; compare against the preserved candidates. Re-running identical code cannot establish missing correspondence. If originals are unavailable, a newly repaired candidate needs explicit separate acceptance evidence and cannot be called an exact archive recovery.
2. Investigate and localize the existing grip-solver and frame-metric failures using the saved path/frame reports and unsaved pose views before modifying geometry, weights or correctives. No present evidence establishes whether each failure belongs to source deformation, candidate-adapter applicability, or a particular anatomical region. Geometry/corrective repair needs new candidate hashes, preserved originals, unchanged acceptance thresholds, and complete native revalidation. Do not infer repair locations from aggregate counts alone.
3. The unchanged production67-bone bridge remains a separate applicability blocker. These authoring-rig diagnostics do not authorize changing validated skeletal data or production assets.
4. Anatomical attachment remains gated on source/content acceptance and reviewed landmarks. PR124 stays pinned `7c820d68de69dcdef7d567e836302123df953446`; its permanent muscle IDs, shoulder/arm-first worklist and independent curl/press/squat contracts remain available. No reviewed landmark bindings were invented, no muscle staging promoted, no geometry attached. Pelvis/legs follow shoulder/arms only after those gates.
5. Historical suite failures remain separate: missing R35–R52 fixture environment variables are not model assertion failures. Previously recorded application887PASS/1skip, TypeScriptPASS, PR12438PASS and offline archive18PASS do not override failed native model gates.

No merge, deployment, source-branch edit, production replacement, original-file change or PT_MODEL_VERSION1.0 change was performed. Further polling of completed runs provides no additional evidence; follow-up stops at this recorded blocker.
