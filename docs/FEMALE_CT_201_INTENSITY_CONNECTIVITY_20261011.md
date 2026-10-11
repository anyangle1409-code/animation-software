# Finite201-source intensity connectivity — no anatomical acceptance

Courtesy of the U.S. National Library of Medicine.

New private intensity-only mask on existing201original arrays1700..1900; no
new downloads, canonical geometry changes or production algorithm modifications.
Fixed illustrative HU>=500 (stored>=1524), no fitted threshold, anatomical seed,
largest-component selection, named bones or smoothing. All components retained.

## Verified results

- All201original raw/PNG/header pins rechecked for this new mask operation.
  Original signed raw-1024 masks independently compare against PIL PNG>=1524:
  52690944samples,0mask differences. This is new mask verification, not a claim
  that thresholded tissue is bone. Existing raw calibration was not repeated.
- Same512x512XYcorners/0.9375mm pixels, normal+1,201consecutive1mm descending
  source centres S=-737..-937, header HUaddend verified before output.
- 320936selected voxels,4271six-neighbour intensity components, all retained.
  Largest intensity-only counts92232,84525,40319,22744,22073,3640,2906,2802,2774,2639.
  Connectivity is SciPy labelling, not bone identity or expert anatomical review.
- Independent unchanged set-based algorithm agrees exactly on sources1817..1826:
  18410voxels/100components. This second algorithm check covers the bounded slab,
  not an independently re-labelled full201volume.
- 34numeric intensity labels contact superior source cut,24inferior source cut.
  None contact outerXYimage edges. Cut contact confirms truncation risk, not
  complete pelvic/bone endpoints. Lack of XYcontact does not establish anatomy.
- Persisted mask reopened:shape201x512x512,boolean,count320936; all201sourceIDs,
  component sizes/sum4271/320936, unchanged prior10-slice mask identity and closed
  registration/pixel-centre/coverage/anatomical/canonical gates checked PASS.
- New diagnostic9.172s; boolean working array52690944bytes, label array210763776
  bytes. NumPy2.5.4; existing private dependency environment reused, no install.
  No full-volume mesh produced; generic surface budget150000occupied voxels is
  unchanged. All201firstviews/raw comparisons were already complete, not repeated.

Readiness stays0READY/9PARTIAL/3BLOCKED; pelvic landmarks0/7. No anatomically
labelled segmentation or source-to-HGPT transform accepted. Full regression
remains non-green; targeted CI is not anatomical/full-regression acceptance.

## Private evidence

Directory outsideGit:
`C:/Users/Mark/Documents/Codex/hgpt-private-female-ct-candidate-1700-1900-20261011/full-intensity-201/`

`safe_full_intensity_report.json` SHA256:
`69433fd5eb86db20141434546969ed3cd9d3ad73931a1ed4ceefb9c73a9194dd`.

`private_intensity_mask_201.npz` SHA256:
`c088a4f379352c4b4b82a5a039a8317b14a02c5bc550475ced4be66fb8aa53f1`.

Full201original pins/per-source counts, unfiltered numeric connectivity labels
and exact cut-contact labels stay in private report. No medical bytes inGit.
Private orchestration: `C:/Users/Mark/Documents/Codex/hgpt-private-hip-plate-678c8c03/female_full_intensity_diagnostic.py`.
Refuses preexisting output directory; reuse verified masks rather than rerun.

## Next executable work

Source-preserving candidate3Ddiagnostics may reuse this persisted mask in bounded
per-slab meshes under unchanged helper caps, with artificial slab cuts explicitly
recorded; never call a tile's closed voxel shell a complete bone. Compare saved
native mesh coordinates/topology against source-derived outputs. Alternatively
independent full-resolution landmark review; approval still requires evidence.
Do not select named-bone seeds from component rank or promote a female candidate
as the HGPT canonical skeleton. Existing native10-slice scene remains the verified
Claude laptop starting point. Battery21% last observed; no power settings changed.

PR26checkpoint50df985c:Windows provenance and amplitude safety CI PASS;
nativeBlender CI still running at last observation, run38100645569.
