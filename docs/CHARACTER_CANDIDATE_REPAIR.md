# Imported character repair validation

The candidate uses the preserved source skeleton and absolute retarget production path. Contact correction, hand/wrist fitting, localized hip smoothing, and the curl elbow/relaxed-arm follow-up are included. The original upload remains unchanged.

Input SHA-256: `854cc1193498b49722ea7ccce92d47d8ba6166b3fc0055cb4666675b710e5a49`  
Current candidate SHA-256: `2d974bfd2b0be85cbfb309ad7649a6ca1d8aa45536c2f1f74c75e27939aa8eb2`

## Production changes

- Final canonical contact targets are passed into preserved imported characters.
- Source-skeleton IK resolves floor and equipment contact for the imported proportions.
- The fitted GLB has isolated bilateral fingers, a blended wrist cuff, a localized hip transition, and a wider upper/forearm blend at each elbow.
- The curl bottom now uses 3° upper-arm clearance and no forward shoulder flexion, rather than 6° clearance and 2° flexion. The contracted pose uses 4° clearance and 4° forward drift rather than 7° of each.
- The curl still reaches 126° elbow flexion; its range was not shortened to hide the deformation.

No mesh topology, model proportions, skeleton, exercise timing, repetitions, equipment, muscle data, or contact rules were changed in the elbow follow-up.

## Verification

- **190 regular automated tests passed; 1 optional asset test skipped in that run.**
- The optional production diagnostic was run explicitly with the candidate GLB: **passed**.
- TypeScript and production build passed. The existing bundle-size warning remains.
- At the fully contracted curl, arm-region edges above 2× rest length fell from 44 to 12; all-mesh edges above 2× fell from 60 to 30.
- At pull-up top, arm-region edges above 2× fell from 57 to 29; all-mesh edges above 2× fell from 124 to 96.
- Curl bottom remains at 4 arm-region edges above 2×. Curl midpoint changed from 20 to 22 whole-mesh edges above 2×, while its maximum and 99th-percentile strain remained effectively unchanged.
- Push-up and shoulder-press peak metrics remained unchanged.
- Every finger and thumb passed the independent isolation probe with zero opposite-side or central/forearm leakage.
- Absolute anatomical transfer replaces the source A-pose and open-hand rest.

## Current visual verdicts

| Movement | Verdict | Exact result |
|---|---|---|
| Dumbbell bicep curl | **NEEDS MINOR FIX** | Bottom shoulders read more relaxed and contracted elbow stretching is substantially reduced. The elbow remains angular because the source topology has limited loops around the joint; minor handle/skin intersections and knuckle faceting remain. |
| Bodyweight squat | **NEEDS MINOR FIX** | Feet maintain contact, but flattened groin/inner-thigh shaping and angular knee folds remain at depth. |
| Dumbbell shoulder press | **NEEDS MINOR FIX** | Grips remain locked; overhead shoulder/armpit creasing and wrist/knuckle faceting remain. |
| Push-up | **NEEDS MINOR FIX** | Palms and feet stay on the floor; low-poly wrist and knuckle folds remain. |
| Pull-up | **NEEDS MINOR FIX** | Grip frames remain locked and elbow strain is reduced; bar/skin intersections and loaded wrist folds remain. |

The screenshots are offline renders of the actual production-posed triangles rather than captures of the Studio interface. Edge ratios and visual inspection do not constitute a complete collision or all-frame self-intersection proof.
