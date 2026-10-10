# Claude laptop handoff — physical pelvis landmark review (9 Oct 2026)

**Read this before Blender work. This file is a coordination handoff, not permission to change the accepted skeleton.**

## Latest independently verified GPT/Work source evidence

- Working development: draft PR **#15**, branch `codex/independent-pelvis-stl-intake-20261009`. Parent PR #14 contains external anatomy source/APP math. Parent PR #13 contains P004–P007 mechanical trunk diagnostics.
- Latest Claude independent anatomical branch when checked: `claude/skeleton-anatomical-development-20261009` at `f3f725f4`. Preserve newer commits; always fetch live heads.
- CT scout machine-readable pinned inputs: `ORIGINAL_V1_WORK/anatomy/audit/nlm_pelvis_scout_pinned_source_positions_20261009.json`. Original pixel and header SHAs each independently matched on GitHub.
- Source report: `docs/NLM_ORIGINAL_CT_PELVIC_REGION_SCOUT_20261009.md`.
- NLM original source images index: https://data.lhncbc.nlm.nih.gov/public/Visible-Human/Male-Images/PNG_format/radiological/normalCT/index.html
- Original scanner headers index: https://data.lhncbc.nlm.nih.gov/public/Visible-Human/Male-Images/PNG_format/radiological/normalCTHeaders/index.html

**Source is one cadaver, NOT a canonical 182cm male population. No CT image has yet been approved as a particular osseous anatomical landmark. The HU conversion and pixel-centre convention remain unverified.**

## High-value original source slices to inspect visually in full resolution

| Filename | Original GE scanner RAS superior S (mm) | Scan group | Reason for first-pass review |
|---|---:|---|---|
| `cvm1451f.png` | −54 | 0.898438 mm XY / 3 mm thick | Source high-intensity structure baseline |
| `cvm1602f.png` | −210 | 0.898438 mm XY / 3 mm thick | Lower torso/pelvis search reference |
| `cvm1752f.png` | −360 | 0.898438 mm XY / 3 mm thick | Distinct changing bilateral dense structures |
| `cvm1800f.png` | −408 | 0.898438 mm XY / 3 mm thick | Distinct bilateral/central dense structures |
| `cvm1906f.png` | −514 | 0.898438 mm XY / 3 mm thick | More caudal reference; physical anatomy unreviewed |
| `cvm1948f.png` | −556 | 0.898438 mm XY / 3 mm thick | NLM gallery describes upper thigh below femoral heads; cross-check image ID |

Other pinned source locations: `cvm1300f` +102; `cvm1399f` +3; `cvm1500f` −108; `cvm1551f` −159; `cvm1650f` −258; `cvm1701f` −309.

**Do not infer anatomy from the coarse ASCII intensity grids alone.** The four reviewed 32x32 tiles were derived at provisional stored-value thresholds of 1200/1600; these are **not verified Hounsfield units or bony segmentation thresholds**. Review actual full-resolution source images, label the structures anatomically only when confidence is sufficient, and provide side-by-side annotated images from clinical/academic reference materials.

## Two physically contiguous CT source windows — use these first

A verified live NLM/GitHub Actions source run (https://github.com/anyangle1409-code/animation-software/actions/runs/37940126718) retrieved six **original** CT PNGs and their original GE scanner headers, decoded 16-bit grayscale source pixels, and verified true **3 mm contiguous adjacent scan-centre steps** on the original scanner. No original CT pixels or personal identifying fields were committed.

| Three consecutive original frames | Actual GE scanner RAS superior Z | Physical covered slab |
|---|---|---|
| `cvm1749f`, `cvm1752f`, `cvm1755f` | −357, −360, −363 mm | −364.5 to −355.5 mm |
| `cvm1797f`, `cvm1800f`, `cvm1803f` | −405, −408, −411 mm | −412.5 to −403.5 mm |

Each frame is 512×512, 0.898438 mm/pixel in-plane, **3 mm thick**, in the same scan group. The full set of six individual image/header SHA-256 source fingerprints is recorded in `ORIGINAL_V1_WORK/anatomy/audit/nlm_contiguous_ct_windows_pinned_20261009.json`.

**The bones depicted at those levels are not yet identified!** Claude must inspect the full original images and establish actual region/anatomical identity from trustworthy CT anatomy atlases. The 3-slice span is only 9 mm; don't invent 3D femoral head or S1 surfaces from it.

Useful command to validate the pinned source again (only official NLM HTTP, original image bytes retained in memory temporarily):

```bash
python3 scripts/anatomy_fit/nlm_contiguous_pelvis_ct_windows.py --live \
  --pinned-manifest ORIGINAL_V1_WORK/anatomy/audit/nlm_contiguous_ct_windows_pinned_20261009.json
```

**Blender assignment:** Review both three-slice sequences as orthogonal images in correct original scanner RAS orientation and make annotated **candidate** names (iliac blade, acetabulum, sacrum, proximal femoral head or other) only where clear. Identify what additional adjacent ranges must be downloaded for complete bony surfaces. Cross-check with independent CT anatomical teaching figures; never claim that existing source pixels have validated landmarks automatically.

## Laptop isolation: Claude and GPT can work concurrently

1. On laptop, `git fetch --all --prune`, inspect uncommitted local Blender/solver work, then use a **separate clean worktree** for read-only PR #15 source code, e.g. `git worktree add --detach ../hgpt-ct-source-review origin/codex/independent-pelvis-stl-intake-20261009`.
2. Keep Claude's current anatomical development on `claude/skeleton-anatomical-development-20261009` or create a separate **Claude-owned** branch for CT/Blender evidence. Do not merge PRs #13–#15 merely to access their read-only tools, and do not modify the GPT PR #15 branch.
3. Inspect actual PNGs and NLM scanner headers locally in a private untracked folder; avoid committing or redistributing raw original CT images or historical original metadata. Use only source geometry, hashed provenance and right-cleared annotated review images.
4. Validate the file's SHA against `nlm_pelvis_scout_pinned_source_positions_20261009.json`; reject a changed source unless independently reviewed. Use scanner **RAS millimetres**, not file-number arithmetic or guessed Home Gym PT world origins.
5. Start with visually identifying: osseous left/right ASIS, bilateral pubic tubercles, sacral superior endplate/S1 promontory, left/right acetabula and femoral articular heads. Determine 3D Z bands *from multiple consecutive original slices* before assigning a 3D landmark.
6. Record for each landmark: source filename+SHA, actual scanner RAS coordinate, original row/column, scanner field of view, slice thickness, confidence and relevant source citations. Do not confuse the 3mm slab/0.898438mm pixel step with submillimetre clinical localisation.
7. Review anatomy source compatibility independently; in particular one individual's bony landmarks should not overwrite population-validated skeletal proportions. Publish findings to a separate Claude-owned branch and report evidence and blockers.
8. Run visual real-pose Blender checks (pelvis and trunk, ribs/manubrium/scapular movement) without modifying the old skin to force a fit.

### Available first-party tools (read-only, no new runtime dependencies)

```bash
# Run synthetic integrity tests first.
python3 -m unittest discover -s scripts -p 'test_nlm_pelvis_region_scout.py' -v
python3 -m unittest discover -s scripts -p 'test_nlm_ct_pixel_ras_envelope.py' -v
python3 -m unittest discover -s scripts -p 'test_pelvic_app_bone_frame.py' -v

# Optional bounded original-source scanner scout:
python3 scripts/anatomy_fit/nlm_pelvis_region_scout.py --live-scout \
  --slice-ids 1602 1752 1800 \
  --pinned-manifest ORIGINAL_V1_WORK/anatomy/audit/nlm_pelvis_scout_pinned_source_positions_20261009.json

# Conditional pixel scanner-RAS coordinate envelope after a human verified an original image point:
python3 scripts/anatomy_fit/nlm_ct_pixel_ras_envelope.py \
  --scanner-geometry-report <PRIVATE-SAFE-SCANNER-GEOMETRY-JSON> \
  --row <ZERO_BASED_ROW> --col <ZERO_BASED_COLUMN>
```

The pixel mapper's candidate coordinate explicitly assumes the NLM GE corner values refer to outer pixel-edge boundaries; the exact convention must still be independently checked. It retains a ±1.5 mm axial-slab bound rather than treating a single image position as a bone surface.

## Output required from Claude

- A **physical slice-to-bone anatomical region index** with original scanner RAS ranges.
- Visually annotated pelvis/sacrum/hip **bone** images with source and angle orientation, not unlabeled control sticks.
- Candidate actual bony APP landmarks, with uncertainty and provenance, or explicit `UNVERIFIED` for each.
- A Blender skeleton-versus-source inspection of pelvis/S1, L4/L5 and hip joint surface centres.
- Independent review of whether source evidence supports any change to c004 (do **not** change it yet).
- Exact local and GitHub test results, new Claude branch/commit and remaining blockers.

**Canon readiness unchanged: 0 READY / 9 PARTIAL / 3 BLOCKED. No c005, no mesh-forces-skeleton correction.**
