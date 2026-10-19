# Arm-to-body reference and back-motion diagnosis — 19 October 2026

Status: read-only diagnosis; no candidate geometry, model save, skeleton change or test change.

Owner approved the recovery plan and asked whether the skeleton needs review. Existing evidence supports investigating the mesh/corrective layer first. This is not a new whole-skeleton validation.

## Reference interpretation

The actual original IMG_1978 reference and latest IMG_1987 markup were retrieved and visually inspected. The intended arm underside continues diagonally into the torso side; the current R52 frame at t=0.800 still hooks inward at the armpit. The original reference and current press pose differ, so a side-by-side comparison is an interpretation aid, not quantitative silhouette registration. The reference's old folds and elbow detail are not a request to restore them.

The private comparison remains outside Git, as do the original reference and markup. No private photo, trace or derived outline coordinates are committed. The old R47-target1mm pass establishes only agreement with that historical marked-pose target. It does not establish agreement with the owner's original example across the press.

## Reproduced motion failure

Run the new diagnostic against the hash-verified original-v1-r52-review artifact:

```bash
python scripts/audit_original_review_r52_temporal_failure.py --response /path/to/extracted/tmp/r52-response --out /path/to/audit-output
```

Source response SHA256: 2a6c01cf7eacd3d1ceb47ae9f131f76dd0487fce5d3518d5cd1df65bc059fa8d.

The161-pose baseline equals the original41-pose source at every shared frame and every recorded back vertex: maximum difference0.0mm. The161-pose R52 geometry likewise equals the83-pose native report at every shared full-press frame/back vertex:0.0mm. This rules out inconsistent coarse/dense snapshots as the explanation for these measured failures.

Worst dense point: vertex19057, left posterior upper flank, t=0.500, press elevation118degrees. Baseline second difference is0.014902mm; actual R52 is2.555191mm. Excess2.540289mm, or40.644618mm after the existing16 normalization. The original41-pose excess reproduces0.706690mm. These are discrete second differences, not physical accelerations in mm/s².

At t=0.49375/0.50000/0.50625, R52's added world-X correction is7.719040/7.841587/10.221869mm. Its added world-Z correction is1.648188/2.413154/2.017736mm. The baseline is smooth at this point, while the added field changes slope sharply.

The source-control decoder places this sample at118.000069degrees for this vertex. Its adjacent material controls117/118/119degrees have a3.206837mm second difference; its118→119 step is2.989777mm. Thus a near3mm bound on adjacent displacement does not ensure a smooth change in slope. The fitter uses only the original41 press responses, allowing intermediate spikes to escape its coarse objective. This explains a concrete mechanism in R52's rejected movement; it does not prove every visually perceived swelling has the same cause.

The additional early outward failure is also reproduced: vertex20913, t=0.4125, approximately105.528625degrees,0.624537mm added outward displacement. The fitter's smaller0.067308mm figure is measured on the coarse grid, not the identical161-pose set. Do not cite the smaller number as a native full-motion pass.

## Skeleton versus skin

R52 changes S7 skin controls only. Existing protected-identity reports show bones, Basis, groups, weights and non-S7 keys unchanged. The same pose path is used for paired baseline and corrected measurements. The large additional mid-press change occurs after applying the skin correction; changing canonical bone positions is not supported by this evidence.

A read-only skeleton/skin overlay can still check the complete motion visually during the next native preview. No new full-bone motion audit or corrective-family ablation has been run in this diagnostic, and baseline deformation elsewhere is not certified correct. Keep the frozen skeleton intact. If an overlay later shows a separate motion defect, document it separately rather than compensating by moving the skeleton to fit this skin.

## Next steps and remaining gates

- Reference comparison is prepared; exact cross-pose quantitative target is not yet defined or approved.
- Root cause is established for the worst sampled added temporal discontinuity; full deformation-family ablation and visual skeleton overlay remain to run.
- Diagnose before modifying geometry. A temporal method must constrain intermediate motion and slope changes, not merely neighbouring control distances or coarse frames.
- Check target feasibility at protected source110/166 and anchors before changing their scope; no release is authorized by this note.
- Preserve the newer arm/elbow detail and all old tests. Keep the original0.5mm motion,2degree crease and1mm historical outline guards, zero marked reversed faces, no new contacts and all13 benchmarks visible.
- Any new geometry gets a new immutable candidate with actual before/after renders/video. No new candidate or workflow started by this audit.
