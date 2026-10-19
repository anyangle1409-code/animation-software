# R53 root-cause evidence and rejected helper-origin probe

Status: INVESTIGATION_FINDINGS_VERIFIED; SHOULDER_REPAIR_UNRESOLVED. No correction candidate or Blender model saved. No visual approval, promotion, merge or production change.

Work is isolated on `codex/r53-shoulder-root-cause-20261019`, starting from `cb4a7ac361c6a8acbe2ca2b9b976e3241352e2a5`. A fresh final check found consolidated HEAD still unchanged and isolated HEAD at `90bd6586f99a68c8fffb4c55b670d4768f1f2ab4`; no newer shoulder PR displaced this work. Original handoff, R47 approval scope, R52 build/results, historical R4 root cause and R11 remesh evidence were reconciled. The skeleton remains the foundation. Height remains 1.82000017 m in the original rest data.

## What was demonstrated

1. **The R52-specific moving defect is in S7.** Across 161 actual Blender poses, R41/R52 bone matrices are identical. With S7 muted, their evaluated shoulder points agree to 0.00000373 mm; muting all shoulder families gives the same agreement. Bone equality across versions does not mean stationary bones: within-clip clavicle/scapula/upperarm relative rotations were measured separately. Removing keys is not a fix: native images show inherited folds and bulging.
2. **A local weight-gradient mechanism exists below those keys.** At lockout, original edge 18081–21057 is 0.986359 mm at rest, 7.001459 mm with all shoulder families disabled, and 14.568945 mm with the active R41 stack. The lat-helper share changes from 0.321240 to 0.404388 across that short edge, with cap/arm changes. An independently computed full-body linear-skinning replay matches the native no-shoulder-key mesh to at most 0.006198 mm. Its edge decomposition matches the actual edge vector within 0.0000731 mm. The fixed-weight edge term has length approximately 0.925 mm; the spatial weight-gradient term approximately 7.15 mm. These are vectors, whose scalar lengths must not be added. Correctives add further differential displacement. This confirms one local mechanism; it does not prove every remaining arch has the same cause.
3. **The inherited corrective stack compensates in opposing directions.** At t=0.5, S5/S7 both move 5271 shoulder-region vertices by over 1 mm, with opposing displacement dot products at 2750. S1/S3/S5/S7 are present; S2/S4/S6 are absent. Disabling S5 or S7 creates visible crumpling. Another unconstrained fit or removal of a whole family is unsupported.
4. **The muscle-line representation is a dependency, not a simple replacement fix.** The existing `muscle_lat` helper carries an AI-to-humerus line with the scapula. Its origin moves about 119.3 mm laterally between t=0 and t=0.8 while the thorax stays fixed. UAMS describes broad lat origins and occasional AI attachment, while teres major originates at the inferior scapula. Therefore an AI-connected proxy is not categorically wrong; its name alone is not a diagnosis. Influence allocation and the distinction between a posterior-fold proxy and broad lat anatomy matter.

## Actual controlled probe: rejected

The probe temporarily carried the existing AI rest point with spine_03 instead of scapula, leaving the insertion, weights, key geometry and all key activations unchanged. Only muscle_lat_l/r pose transforms changed; all other pose matrices matched exactly. It is an origin-transport experiment, not an authored broad lat or a proposed runtime correction.

| Actual measurement | Original R52 | Origin-motion probe | Requirement |
|---|---:|---:|---:|
| R47 outline error at 135.625 degrees | 0.949948 mm | 25.747078 mm | <=1 mm |
| 161-pose motion excess, original-grid equivalent | 40.644618 mm | 39.026514 mm | <=0.5 mm |

The same probe on R41 changed marked-outline error from 41.105288 to 34.215394 mm and introduced 3.017229 mm motion excess against R41. Both remain unacceptable. New side/flank creases are visible in the native R52 probe. Five snapshot checks against the union of original per-source frozen_arm masks show differences up to 13.238258 mm; that union diagnostic is not a substitute for the actual any-angle scope test. The probe cannot be described as preserving the desired arm shape merely because weights and rest geometry were unchanged. No part of it is adopted.

Full original 83 safety checks, 13 movement benchmarks and historical contour/front tests were **not rerun on this diagnostic pose experiment**. No claim about its complete fold/contact counts is made. R52's previously recorded failed motion, marked reversed faces, contacts, crease and benchmark regressions remain unresolved baseline evidence. No test or threshold was changed, weakened or deleted.

## Native verification and preservation

* Capture: https://github.com/anyangle1409-code/animation-software/actions/runs/39264438580 ; source `f9f9bcb241ea16a3b460f30babdf4245616c0163`.
* Origin probe: https://github.com/anyangle1409-code/animation-software/actions/runs/39267601720 ; source `90bd6586f99a68c8fffb4c55b670d4768f1f2ab4`.
* Both completed successfully as evidence workflows. Each native mode evaluated 161 poses. Input/model hashes, five diagnostic tests and protected identities passed. Probe baseline replay error was exactly zero. Canonical/rest skeleton, anatomy, topology, weights, groups and all key coordinates remained unchanged. No saved file changed.
* Capture artifact SHA256: `562f90894196d357079d1ca14c5f253c386684553b44a7a122b6929a29ef6f4d`.
* Probe artifact SHA256: `cb00d5f1ff04d42743c25eed788beda2dedb7ef344655545466035a4319c8eb7`.
* Both archives were downloaded and independently hash-verified. Actual front/rear/side/three-quarter images and press videos are retained. The probe video uses forward/reverse playback of captured poses; lowering was not separately simulated. Example t=0.8 images show approximately 156.016-degree elevation, distinct from the marked-pose outline measurement at t=0.625.
* Actual evidence and media were also saved for owner review. No reference photos or third-party assets entered Git or the model. Anatomy and real-exercise references, limitations and photographed clothing/occlusion are in the companion anatomy note.

## Smallest next correction and current blocker

Do not adopt the origin-motion change. The next evidence-supported experiment is **local skin-weight redistribution** around the verified short-edge transition, preserving the original helper motion and skeletal foundation. A proposed 12 mm mirrored neighbourhood contains 30 vertices in the original R47 material union; excluding the four vertices flagged by any original source frozen_arm mask leaves 26 eligible vertices. Seed edges are 18081–21057 and 18057–21044. The explicit proposed mask is recorded separately; no weights have been changed.

Start from the actual R52 study so the R47 marked outline remains the reference. Change only that bounded weight patch in a separately named review candidate, then run the unchanged native safety, motion/crease, historical contour/front, scope and 13 benchmark checks across the complete press. Preserve all other weights, rest positions, topology, canonical bones, HGPT_SHOULDER and newer distal arm/elbow detail. Keep the unchanged 1 mm actual-outline guard. Expand neither the patch nor the runtime contract automatically. Retain failures and reject the change if it worsens the surface or loses the outline.

**This is outside the existing S7-only authoring scope.** R47's explicit contract freezes weights and non-S7 data. The owner's new brief allows only corrections within existing authorization and says not to expand approved modification scope. A localized weight-correction experiment therefore needs a scope decision before implementation. Existing identity tests must not be weakened to conceal that deliberate change; their status and any explicitly approved policy exception must be documented. No skeleton change is proposed or required by the demonstrated local mechanism.

The investigation has narrowed and verified causes, but the whole arm-to-body transition and full-motion surface are not repaired. No R53 model is accepted or ready for production.
