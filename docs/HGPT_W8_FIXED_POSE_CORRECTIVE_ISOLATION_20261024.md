# W8 fixed-pose corrective isolation — 24 October 2026

Status: software tests PASS; new native cloud execution PENDING. No model repair or anatomical acceptance.

## Purpose and decision

The verified W8 native archive shows abnormal local edge ratios, stored S7/K1 key geometry and actual S7 activity. The earlier probe omitted K1 channels. Association between an active key and an edge change cannot isolate its contribution. Next dependency: observe actual K1 values and compare the same endpoints at the same skeletal pose with controlled key muting.

Chosen approach: extend the existing pinned r57/W8 probe in memory, retaining its source SHA256, frozen native tessellation and nine press samples. This reuses the native pose exactly. Static key-ratio multiplication would misrepresent key combinations and the modifier stack; an edited .blend candidate is unnecessary for a diagnostic.

## Measurement contract

- Source W8 `2434afd0daa231ab3a03c873cad4187ffcbc1bab78132375221160b0b0f09e4c`, frozen driver/benchmark source `025d5f28fa7eba2064fba565b1c9b60119cdd2cb`.
- Four previously ranked W8 edges only: [15645,53019], [17185,44317], [29237,71026], [32352,71428]. These IDs and suffixes are not reviewed anatomical landmarks or sides; no equivalent V14/R120 correspondence is inferred.
- At each existing press sample, record observed coordinates and actual key values including K1 elbow channels. Temporarily mute S7 alone, K1 alone, and all non-Basis keys, in separate conditions reset from original mute flags.
- Evaluate all conditions with the unchanged pose. Compare edge lengths against benchmark rest V0 in the benchmark's common coordinate space. Report native geometric length ratios, never tissue strain or safe limits.
- Preserve pre-existing muted keys; do not change key values, rig transforms, mesh coordinates, weights or source files. Restore mute flags in `finally`, refresh dependency graph, require identical full skeletal pose signature and key values, unchanged topology and restored endpoint coordinates within 1e-8 m. That tolerance is a numerical reproducibility check, not a biological threshold.
- All-keys-muted retains authored helper motion, constraints, weights and modifiers. It is NOT independently certified skeletal skinning or physiological truth. Conditional changes are not additive causal percentages; unchanged sampled edges do not prove keys have no effect elsewhere.
- No corrected candidate is saved. Failure prevents a successful native report. Source hash and rest signature remain guarded by the existing probe. Publish enriched pose JSON and a phone-readable Markdown table in the existing pose artifact.

## Tests and evidence

K1 omission regression observed FAIL (empty extracted list), then PASS after adding the existing named prefix. Eleven new isolation tests cover fixed-pose measurements, restoration on exceptions, preserved values/pre-existing mutes, changed topology, nonfinite coordinates, missing endpoints, degenerate rest edges, altered skeletal pose, failed coordinate restoration, operator/save guard and phone report status. Missing-module and missing-renderer failures observed before implementation. Full Python diagnostic suite: **226/226 PASS** in isolated cloud workspace; actual Blender execution pending the new workflow. Native results must be downloaded, hashed and read before any claim they passed.

## Anatomical dependencies remain blocked

ISB Part II (Wu et al. 2005, DOI 10.1016/j.jbiomech.2004.05.042; https://pubmed.ncbi.nlm.nih.gov/15844264/) concerns standardized motion coordinates, not automatic rig-axis identity. Seth et al. 2019 (https://pmc.ncbi.nlm.nih.gov/articles/PMC6856649/) models independent scapular movement and validates muscle path behavior; neither justifies treating arbitrary Blender helpers as anatomical joints. Existing foundation-first roadmap and permanent muscle IDs remain authoritative. No new attachments, clinical ROM clamps or highlighting.

The 46 landmarks remain unbound; 0/19 native generic human movement scenarios approved. Shoulder/squat/grip, archive identity and real contact/skin acceptance remain open.

## Native result verified, with separate downstream reporting failure

Run40076138093 at `39d65c0bc766fa81d71fd64e5eea33ce69f852e8` succeeded in 6/7 jobs, including the native W8 pose probe. Overall workflow FAILED: timeline reporting rejected newly observed K1 names. That parser is fixed in `75affbdddc6922c6570fc39bcb098164b844aded`; real JSON replay and 228 tests pass; cloud confirmation is separate.

All eight ZIPs freshly downloaded and SHA256-matched to GitHub. Every ZIP/member hash is in `recovery_20261023/cloud_verification_20261024_run40076138093.json`. Native pose artifact12553561589 ZIP `fe888f196f3fab7548b52b22262025815f9f50e9d1eabfc7cadbb7de8f1ae516`; JSON `19ec870df061f22be1f466e72b55a124b3a06ff13fdc422a515052a9d7ba883d`. Restoration endpoint error 0 m for all nine native samples. All nine previously measured elevations and baseline deformation metric dictionaries remain exactly equal to run40072736803.

| Native sample / edge | Observed / rest | S7 muted / rest | K1 muted / rest | All keys muted / rest |
|---|---:|---:|---:|---:|
| 0 / [15645,53019] | 0.1676121 | 0.1676121 | 0.0773237 | 0.7065723 |
| 0 / [17185,44317] | 0.1631255 | 0.1631255 | 0.0667802 | 0.7057421 |
| 6 / [29237,71026] | 2.6733724 | 1.2014833 | 2.6733724 | 1.4132507 |
| 6 / [32352,71428] | 2.6485931 | 1.2034341 | 2.6485931 | 1.4227250 |

K1_90 actual values for both suffixes: samples0–3 = 1.0, 0.871094, 0.53125, 0.050781; recorded K1 values are all zero at samples4–8. Thus K1 omission is resolved for this native probe. Local sampled distortion decreases when S7 is muted at sample6; muting K1 worsens the distal sampled compression at sample0. This does not authorize disabling either family: no matched visual assessment, adjacent controls or whole-body revalidation exists.

## Next isolated controls staged

At sample0, observed S3_75/S3_100 and S5_85/S5_110 are active alongside K1_90. The next probe adds separate S1, S3 and S5 mute conditions at all nine existing poses, preserving the same state/coordinate checks. Synthetic combined-family regression observed FAIL before implementation and PASS after; complete suite now **229/229 PASS locally**. Additional family native results are pending. S2/S4/S6 are nominally absent in the verified W8 configuration; no invented activation is added. These controls still sample only four edges and cannot establish whole-body improvement or joint physiology.
