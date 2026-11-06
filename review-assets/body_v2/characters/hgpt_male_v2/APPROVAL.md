# Approval record: hgpt_male_v2 (Home Gym PT male, Body v2)

**Status:** `approved_appearance` (standing appearance only), Meshy Pro male checkpoint **07c**, locked. Movement and production are **not approved**.

- **Appearance:** standing appearance approved by the owner on 6 Nov for checkpoint 07c (`HGPT_Male_Rig_07c_StandingCleanup_WIP_PROXY.blend`, SHA-256 `e9448c688d2ae83bc35c18678a353449e226c638298feef1482f123ac74b55a0`). The file is read-only and is never overwritten. (The earlier Body v2 sculpt defects in `docs/ANATOMICAL_DEFECT_LIST_20261103.md` §1 belong to the superseded W12c candidate.)
- **Movement:** not approved. Movement work stays paused until the female standing model is also approved.
- **Production:** unchanged. PT_MODEL_VERSION 1.0 and the production model are untouched.

Only the owner adds entries below. Claude records the evidence that was reviewed; tests or workflows passing are not approval.

| Date | Approved by | What (appearance / movement / production) | Candidate | Evidence | Notes |
|---|---|---|---|---|---|
| 2026-11-03 | owner | Proportions TARGET only (not appearance, not production): the MPFB benchmark M13/M14 legs, waist, width and arms; chest excluded (to be sculpted in the first-party model). The owner chose option 1: "use MPFB for overall proportions only" | MPFB benchmark M13/M14 (experimental, not production geometry) | review-assets/body_v2/mpfb_benchmark_20261103/ | The independent first-party mesh still needs its own visual approval |
| 2026-11-06 | owner | Appearance (standing) | Meshy male 07c, `e9448c68…` (locked) | review-assets/meshy_retopo_20261105/README.md (SC1), standing_07c/ | "Male standing model 07c is approved as the base male standing character for Home Gym PT. Lock 07c as the approved male standing checkpoint. Do not overwrite it. Do not resume movement development yet." |

## Future polish for 07c (non-blocking, recorded at the owner's request)

None of these blocks the approval. They are picked up only after both standing models are approved.

- Hands: detail and a presentation pose.
- Small marks at the nostrils, the hairline and the right shoulder.
- Optional fitted shorts or another presentation clothing layer.
- Any later visual refinements after both standing models are approved.
