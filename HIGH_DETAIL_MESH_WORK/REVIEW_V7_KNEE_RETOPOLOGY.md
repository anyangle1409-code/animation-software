# V7 medial-knee review candidate

V7 is a separate candidate built from the unchanged V6 knee-seam baseline. It is a **review checkpoint**, not an accepted final knee or a production asset. Compare the matched-camera squat images in `renders_v7_knee_retopology/V7_KNEE_V6_COMPARISON.jpg`.

## Exact geometry work

- The editable Blender body joins the 30 paired medial-knee UV-seam vertices into a continuous surface. It has 33,059 body vertices and the same 62,961 triangles. UV0 remains per polygon corner; both UV layers retain their loop counts.
- A read-only audit of the saved Blender mesh counts 19/18 local boundary edges around the left/right knees, down from the V6 GLB's 74/74; the remaining edges are continuing UV-island boundaries outside the welded segment.
- The dressed and bare GLBs retain 33,089 vertices because glTF duplicates vertices at the UV0 island boundary. Paired positions and weights match exactly, with a 0 mm gap at rest and in all 28 saved candidate poses. The GLB index-based boundary count therefore remains an **advisory UV-split metric**, not proof of an open Blender mesh.
- A local, symmetric posed-space smoothing pass reshapes the medial knee and patellar edge. It changes 1,078 GLB positions, all within the two knee regions, with a maximum rest-space displacement of 25.15 mm. Local normals were recomputed. No other body region was sculpted.
- The direct GLB-index weld trial was rejected because it inverted and stretched UV0 triangles. The final GLBs preserve both V6 UV sets and indices byte-for-byte.

## Files and hashes

| File | SHA-256 |
| --- | --- |
| `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v7_knee_retopology.blend` | `eeeae666812fb61a00f98bcde308dbbdc38ffd112ead3a9294424094e30a6622` |
| `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v7_knee_retopology.glb` | `f6346ac4da1508cc15bb16d6406d7cc0cc8c97a92c173d57d2d422bcb9a59d6d` |
| `HomeGymPT_Male_HIGH_DETAIL_CANDIDATE_v7_knee_retopology_BARE.glb` | `08c6ff33a07900880773e363583b2d6a5dce638e204f4dca4623925e9ebee410` |

## Validation

- `FINISH_CANDIDATE.bat v7_knee_retopology knee` passed against runtime source `614033b256d869230ea273522620467401b0bc71` and frozen canonical hierarchy `hgpt_canonical_v3` / 63 bones.
- Five focused guards passed: sagittal shoulder, bare/dressed equivalence, grip metric, dumbbell clearance, and renderer/exporter agreement. The shoulder cap remains 31.0 mm above the fixed joint with apex z -47.4 mm.
- All seven reviewed clips (three curl variants, squat, shoulder press, push-up, pull-up) passed 26-frame comparisons. Original hand positions, bone matrices and equipment matrices differed by 0 from the frozen reference; loops closed.
- The GLB document, skin weights, UVs, indices, materials, animations, nodes and skins match V6. Zero degenerate triangles and zero edges with more than two faces. All 400 pinned source files and V6 GLB are hash-identical to their baselines. See `reports/final_integrity_v7_knee_retopology.json` and `reports/checkpoint_v7_knee_retopology.json`.

## Visual assessment and limits

In the matched squat front, side and three-quarter views, the former pointed medial flap and side leaf are substantially reduced. A small medial notch remains and the patellar volume is broad and simplified. These areas need human review before this becomes the accepted geometry baseline. V7 still carries its prior character rig; it is not a newly rebound 63-bone production asset. It does not finish skin materials, hand anatomy, axilla topology or final knee weight painting.

Stop here for review as `WORK_MASTER_HANDOFF.md` requires. Do not promote or start the hand pass until the V7 knee candidate is reviewed.
