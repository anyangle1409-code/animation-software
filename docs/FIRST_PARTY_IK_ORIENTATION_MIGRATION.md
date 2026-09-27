# First-party IK orientation migration

Prepared:
- `src/ik/firstPartyOrient.ts`
- `src/ik/firstPartyOrient.parity.test.ts`

No production IK caller has been switched.

The parallel implementation covers:
- joint-limit clamping;
- rest-world orientation;
- analytic XZY swing;
- one-axis elbow/knee hinge solve.

The parity tests compare it to the current Three-based implementation using
representative exercise poses and arm/leg directions.

## Integration rule

Only integrate after:
1. first-party math parity passes;
2. first-party skeleton parity passes;
3. this orientation parity passes;
4. full current suite remains green.

Then migrate one IK chain at a time, comparing:
- solved joint rotations;
- target residual;
- pole direction;
- contact locks;
- joint-limit status.

Do not change IK thresholds or anatomical limits to make the first-party math
implementation pass.
