# First-party IK orientation migration

Prepared:
- `src/ik/firstPartyOrient.ts`
- `src/ik/firstPartyOrient.parity.test.ts`

Production `src/ik/orient.ts` now delegates orientation calculations to these project-owned functions via `Skeleton.firstParty` and `PoseEvaluation.firstPartyEvaluation`. Its Three input/output types are temporary compatibility boundaries. `twoBone.ts` and `solve.ts` retain Three-dependent calculations and caller boundaries. The hinge-twist / mid-flexion internal quaternion calculation of `twoBone.ts` is first-party at `fa06d26da9e0a99a2aa9d1b2ca9528075b4b5025`, with frozen solved rotations; its triangle and pole vector arithmetic remain Three-dependent. Both exact-SHA Actions workflows passed on `fa06d26`.

The parallel implementation covers:
- joint-limit clamping;
- rest-world orientation;
- analytic XZY swing;
- one-axis elbow/knee hinge solve.

The parity tests compare it to the current Three-based implementation using
representative exercise poses and arm/leg directions.

## Completed orientation integration

Checkpoint `dd4a7abd5129b387612265df2b609b9cb7c13899`: focused parity, full exercise/contact suite, build, software gates and local Chromium smoke pass. Both exact-SHA GitHub Actions workflows (`Standalone prep verification` and `Browser viewport smoke`) passed.

## Next integration rule

Only integrate after:
1. first-party math parity passes;
2. first-party skeleton parity passes;
3. this orientation parity passes;
4. full current suite remains green.

Next migrate one IK chain at a time in `twoBone.ts` and `solve.ts`, comparing:
- solved joint rotations;
- target residual;
- pole direction;
- contact locks;
- joint-limit status.

Do not change IK thresholds or anatomical limits to make the first-party math
implementation pass.
