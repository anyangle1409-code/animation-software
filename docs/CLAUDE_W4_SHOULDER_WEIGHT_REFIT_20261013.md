# W4: weights-only shoulder-top/axilla refit for LBS conditioning — measured negative result (Claude, 13 Oct 2026)

- **Script:** `scripts/build_original_shoulder_weight_refit_blender.py`, run in memory. The source blend, rig and every other weight are unchanged.
- **Report:** `ORIGINAL_V1_WORK/anatomy/audit/claude_w4/shoulder_weight_refit_report.json` (KAPPA 0.15, spine_03 allowed).

**Idea.**
- The W2 diagnosis (#112) found that shoulder-top skin becomes nearly singular under linear-blend skinning at 145–160°.
- For each of the 1,312 zone vertices, the refit searches the weight simplex (0.1 grid, at most 4 influences) over its own bones plus the same side's clavicle, scapula and upper arm (and optionally spine_03).
- It maximizes the worst smallest singular value of the blended matrix at 90/120/145/160°, minus a penalty for changing weights.
- The weight change is then smoothed over the zone.

**Results.** Coupled shoulder sweep; each cell gives collapse faces / self-intersecting pairs / volume %.

| Elevation | Original weights | Refit κ 0.15 + spine | κ 0.4 + spine | κ 0.15, no spine | κ 0.4, no spine |
|---|---|---|---|---|---|
| 90 | 0 / 0 / +1.8 | 8 / 4 / +2.9 | 2 / 2 / +2.2 | 6 / 2 / +3.0 | 2 / 0 / +2.3 |
| 120 | 2 / 0 / −1.4 | 10 / **216** / +0.4 | 6 / 112 / −0.3 | 6 / 226 / +0.5 | 6 / 122 / −0.2 |
| 140 | 40 / 132 / −3.6 | 4 / **404** / −1.4 | 4 / 372 / −2.0 | 6 / 336 / −1.3 | 6 / 352 / −1.9 |
| 160 | 42 / 444 / −5.0 | 6 / 400 / −2.8 | 10 / 492 / −3.2 | 4 / 406 / −2.7 | 10 / 452 / −3.1 |

Conditioning improves: vertices with a smallest singular value below 0.1 fall from 102 to 14–18. **But self-intersection rises sharply from 110° to 145° in every variant.** Moving skin off the arm makes the arm skin pass through it. Conditioning is necessary but not sufficient.

**Rejected:** weights-only conditioning refits. The record is kept so the experiment is not repeated.

**Combined evidence across W2 (#112), weight diffusion and W4:**
- With the existing 67 controls and linear-blend skinning, pose-space correctives, weight diffusion and conditioning refits all trade one defect for another at 120–160°.
- The remaining routes are a shoulder-top helper deformer (for example a deltoid/acromion bone driven at a fraction of humeral elevation), or a different skinning scheme.
- **Both change the 67-joint runtime contract.** Lane G (GPU palette/GLB) and PR68's six-control map consume it, so this needs **owner and Lane G agreement**. That is ledger W3, now the controlling blocker for the shoulder press.
