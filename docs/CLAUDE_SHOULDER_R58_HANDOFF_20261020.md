# Shoulder work: Claude's R53–R57 review and R58 localisation (20 Oct 2026)

**Status:**
- No model was changed, saved or approved.
- Work's branches (R53–R57, PRs #119–#122) were read but not edited.
- The R58 diagnostic is read-only. Its files are added as new files on `claude/home-gym-pt-animation-txux66`:
  - `scripts/shoulder_r58/`;
  - `.github/workflows/shoulder-r58-temporal-localisation.yml`.

  Its workflow checks out the R57 sources at their pinned commit; it does not merge them.

## R53–R57 in one paragraph each

**R53 (root cause).**
- With S7 muted, R52 equals R41 exactly. The R52 moving defect is in the S7 increments.
- A sharp skin-weight gradient (edge 18081–21057, lat-helper share 0.32 → 0.40 across ~1 mm) is a real local mechanism.
- S5 and S7 push in opposing directions over ~5,000 vertices.
- Rejected:
  - moving the lat-helper origin: outline error 0.95 → 25.7 mm;
  - the 26-vertex weight averaging: seed edge 14.57 → 15.22 mm at lockout.

**R54.** All 25 global S5/S7 amplitude pairs (0.90–1.10 each) fail. The best pair is the unchanged 1.0/1.0, which keeps the outline (0.95 mm) but still has 40.64 mm motion excess. Global scaling is ruled out.

**R55.**
- 1,711 of 1,796 posterior vertices individually exceed 0.5 mm; 1,685 of them lie outside the 26-vertex patch.
- Worst vertex 19057 (40.64 mm) is 35.5 mm along the mesh from that patch.
- The early-outward vertex is 20913 (10.36 mm).
- The weight patch cannot be the fix.

**R56.** Per-control permissions:
- Source 110° and 166°, and dense controls 95, 110 and 166, are zero and protected.
- Source 120–156°: 1,776 editable posterior vertices.
- All 40 worst hotspots are editable at dense 118°/119°.
- An S7-only local study inside the existing permissions is allowed.

**R57 (cloud run 39411211783; rejected, all failures kept).**
- Change: temporal smoothing of the dense S7 increments over 114–122° (5-tap [1,4,6,4,1], strength ≤ 0.65), within a 55 mm mesh-distance taper around 19057/20913 and their mirrors.
- Results:

  | Check | R57 | Limit |
  |---|---|---|
  | R47 marked outline | 0.95 mm (passes) | 1 mm |
  | Dense 161 motion | 39.38 mm (R52 40.64) | 0.5 mm |
  | Early outward | 0.62 mm, unchanged | 0.05 mm |
  | Reversed normals in the marked pose | 6 | 0 |
  | New contacts in the 83 safety checks | 7 (vertex 10855 vs 22184–22187, samples 25/26/65/66) | 0 |
  | Original 41-pose motion | 1.09 mm | 0.5 mm |
  | Posterior crease | 142° | 2° |
  | Benchmarks regressed | 6 | 0 |
  | Adjacent step | fails | 3 mm |

## What R57 tells us

Smoothing at 114–122° removed only 1.3 of 40.6 mm, so **the dominant extra acceleration is not at 118°**. Two facts from the code (`original_review_r52_native.install`, `original_review_r43_sampling`) point to where it more likely is:

1. **The S7 increment is pinned to zero at the 110° control and the 166° control.** The free controls 111° and 165° next to them can hold up to the 45 mm cap. A large increment that starts or stops within 1° of a pinned zero is a kink in the increment profile. When the press sweeps through that degree it becomes a frame-level acceleration spike.
   - Near lockout the press moves slowly (smoothstep ease-out), so a kink there spans more frames.
   - Mid-press the press moves fastest, so a kink there gives the sharpest per-frame jump.
2. **Early outward (0.62 mm before 110°)** can come only from the free controls 96–109° (95 and 110 are zero). Smoothing at 114–122° cannot touch it.

**R58 measures this directly instead of guessing.** It reports:
- per frame and arm angle, the worst excess;
- for each worst vertex, its peak frame and angle, and its increment profile over the 72 controls with the top three kinks;
- the early-outward vertex and its angle, and the largest increment at 96–109°.

## Exact next steps (resume here)

1. **Read the R58 artifact** `original-v1-r58-temporal-localisation`, file `r58_report.json`, from the workflow run on this branch. Check `excess_by_elevation_band_mm_x16`, `timeline_top_frames` and `worst_vertices[].top3_kinks`.
2. **If the peak sits next to a protected zero (110/111° or 165/166°):** the next S7-only study (R59) should ramp the increment in over several controls *inside the existing permission*.
   - Ease the free controls 111–11x toward the pinned zero so the profile has no kink. Do the same into 166°.
   - Do not touch the protected controls, the 45 mm cap, weights, the skeleton or non-S7 data.
   - **The ramp must not move the R47 marked pose** (t = 0.625, 135.6°), so keep the 123–145° controls unchanged.
   - Run the unchanged R57 gates: the R57 workflow with the generator swapped.
3. **If the peak is mid-press (123–156°):** that band supports the approved R47 marked outline. Any change there risks the outline (1 mm guard). Report this to the owner as a scope decision; do not change it silently.
4. **If early outward comes from 96–109°:** clamp the outward component of the increments at those controls (it must be ≤ 0.05 mm before 110°). That is inside the S7 permission.
5. **Separately, the 7 contacts** (vertex 10855 against 22184–22187 at samples 25/26/65/66) and the **6 reversed normals in the marked pose** exist in both R52 and R57. They need their own localisation before R59 can pass.

**Rules unchanged:**
- Skeleton, canonical bones, Basis, weights and topology stay frozen.
- HGPT_SHOULDER_* stays with Work.
- No merge or deploy, and no claim of approval.
- The R47 marked silhouette is the owner-approved reference; keep it within 1 mm.
- The newer arm and elbow detail is kept.
- Reference photos stay out of Git.
