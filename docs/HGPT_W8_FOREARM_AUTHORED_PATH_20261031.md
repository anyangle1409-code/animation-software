# W8 authored forearm path — verified 31 October 2026

## Verified native evidence

The previously implemented forearm probe at `eef58e56a95f3576777e0c83d7a0e91cb20d7240` completed run [41114474836](https://github.com/anyangle1409-code/animation-software/actions/runs/41114474836), success 7/7. This continuation verified the existing result rather than reimplementing it.

Artifact `13005761946` was independently downloaded, ZIP CRC-checked and matched GitHub SHA256 `93fc680728196671473816f2a033a851a7758f20583280594881f0468b62e945`. The JSON and Markdown digests, actual cloud test counts and scope are in `recovery_20261023/cloud_verification_20261031_run41114474836.json`. The JSON passes the strict validator and regenerates the Markdown byte for byte.

## Result and interpretation

- Nine samples hold the authored elbow-flexion field at 90 degrees while the target travels from 0 to +68.8 to -82.4 degrees. Those are authored target fields, not independently measured anatomical angles.
- Independent local quaternion captures show twist helper 0 tracks the target magnitude; helper 1 tracks half the magnitude. Largest magnitude disagreement is under 0.000025 degrees across the two suffixes. This is implementation consistency, not anatomical certification.
- The hand local rotation remains zero; it still inherits parent motion.
- Rounded benchmark minimum forearm slice-radius ratios range from 0.96 to 0.91 on both suffixes. These are six-slice geometric skinning proxies. They do not measure anatomical cross-sectional area, tissue safety, muscle continuity, or acceptable deformation. A 0.91 ratio is not a verified 9% tissue loss.
- The frozen plain benchmark clears shape keys. It does not test the active corrective skin system. It ends at authored supination; return to neutral remains untested.
- The inventory provides one forearm control and two twist helpers, without independent radius/ulna control evidence. No anatomical laterality, ISB frame, human range, or movement approval follows.

## Review and report hardening

A fresh-context review found no Critical/Important native evidence error. Review noted that the pinned-source check validates Git HEAD but not working-tree cleanliness; dirty-checkout hardening remains deferred. The cloud workflow uses a fresh checkout of the pinned commit, and no dirty source affected this report.

A strict-schema gap allowed sample IDs `false`, `true`, and `2.0` to compare equal to integer IDs. A new regression failed in all three cases before a type check fixed it. The focused suite is now 14/14 and the existing native report and rendered Markdown remain unchanged. The full report-only suite passed 366/366 locally. Replacement cloud run 41151053374 is pending; do not claim the hardened implementation cloud-verified until it passes.

## Next task

The frozen benchmark has no standalone elbow-flexion path. Use its existing bent-over-row path for the next elbow-bending observation, recording authored upperarm/forearm/hand controls and evaluated elbow-region geometry; it combines shoulder and elbow motion and must not be described as an isolated elbow test. Use the existing source hashes and nine-sample discipline; keep target fields, unsigned control geometry and anatomical joint coordinates distinct. Do not add radius/ulna controls, change weights, attach muscles or approve anatomy from this evidence.

All protected model/rig/weight/shape-key/muscle/application assets and PT_MODEL_VERSION 1.0 remain unchanged. 46 landmarks remain unbound and 0/19 generic motions are approved.
