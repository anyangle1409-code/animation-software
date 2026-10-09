# P001: metacarpals 2–4 at the male radiographic means (diagnostic proposal; NOT a candidate, NOT canonical)

**The defect it addresses is proven:** c004 (and a003) CMC-to-MCP spans for M2/M3/M4 are 58.4 / 54.0 / 51.6 mm.

| | M2 | M3 | M4 |
|---|---|---|---|
| Aydinlioglu 1998 (50 men, AP radiographs, head/base midpoints) | 68 ± 4 mm | 64 ± 4 mm | 58 ± 4 mm |
| 2025 CT series | 67.7 mm | 66.1 mm | 58.0 mm |
| c004 z-score | −2.4 | −2.5 | −1.6 |

The two independent sources agree within 2.1 mm. M1 and M5 are within 1 SD and unchanged.

**The change (isolated):**
- Each metacarpal keeps its CMC end and its own axis; only its MCP end moves out to the target length.
- The digit 2–4 phalanges and the MCP/PIP/DIP markers translate rigidly with it, by 6.4–9.9 mm (table in `proposal_record.json` → `candidate.changes`).
- Nothing else changes: carpus, CMC/intermetacarpal markers, thumb, little finger and every other bone are byte-identical to c004 (test-enforced).

**Why it is not a candidate:** exact canonical CMC positions depend on carpal geometry, which is BLOCKED in the readiness report. The target values are population means, not a frozen 1.82 m-specific target. This shows the direction and its consequences only.

**Results (all computed; files in `checks/` and the run directory):**
- **CP2:** same verdict as c004; only the inherited zero-disc FAIL.
- **CP3 round trip** (fresh empty-scene Blender build): PASS.
- **Isolated sweeps** (`../../runs/isolated_bone_only_p001_metacarpals_001`): 135/135 integrity, 41/43 mirror. 109 tests are byte-identical to c004; 26 hand/thumb/wrist tests change because they read the metacarpal tips.
- **Solver ↔ Blender:** AGREE.
- **Other checks:** mirror 0 FAIL; frame continuity 0 issues; joint-frame audit 0 issues and 0 sign flips; attachment v2 identical to c004; amplitude provenance TRACED.
- **Crossing:** no new axis crossings. One new info-only near approach: during *hip abduction* the hanging middle fingertip comes within 2.0 mm of the femoral axis. This is the same whole-body interaction as H6 (isolated sweeps from the hanging posture), not a hand defect.
- **Hand length:** bony wrist-centre-to-middle-fingertip length 186.5 → 196.4 mm. The stature-conditioned ANSUR surface hand length (wrist crease to fingertip skin) is 199.5 mm. This is descriptive only, since the endpoints differ.
