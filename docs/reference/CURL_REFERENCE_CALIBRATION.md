# Curl reference calibration notes

This is development evidence, **not** the independent reference truth.

It records what the current accepted library definitions author so future work does
not need to rediscover it. The local `ReferenceSpec` must remain broader and
independently reviewed.

## Current authored library values

| Variant | Elbow start → peak | Forearm/grip start → peak | Upper arm sagittal start → peak | Left abduction start → peak | Root pitch |
|---|---:|---:|---:|---:|---:|
| Dumbbell bicep curl | 16° → 126° | +72° → +80° | +3° → +7° | −3° → −4° | 0° |
| Hammer curl | 16° → 126° | 0° → +6° | +3° → +7° | −12° → −13° | 0° |
| Reverse curl | 23° → 126° | −66° → −60° | +3° → +7° | −3° → −4° | 0° |
| 45° incline curl | 16° → 126° | +72° → +80° | −42° → −38° | −20° → −18° | −45° |

These values come from the currently authored family/variant definitions at the
source snapshot. They must **not** be copied automatically into a reference
envelope.

## Current draft independent envelope

The first reference draft intentionally allows more variation:

- bottom elbow: 5–30°;
- peak elbow: 115–140°;
- elbow excursion: 90–130°;
- standing upper arm sagittal: −5–15°;
- incline upper arm sagittal: −50 to −30°;
- upper-arm excursion: 0–12°;
- standing left abduction: −20 to −2°;
- incline left abduction: −25 to −12°;
- supinated forearm: +55 to +90°;
- neutral forearm: −15 to +20°;
- pronated forearm: −80 to −45°;
- wrist flexion/extension: −10 to +10°;
- wrist deviation: −12 to +15°;
- local spine flexion: −8 to +8°;
- left clavicle elevation axis: 0–10°;
- standing root pitch: −5 to +5°;
- incline root pitch: −50 to −40°.

These are still marked **draft**.

## Calibration process on the laptop

Use the generic helpers in `src/reference/measure.ts` to collect the current
motion as evidence:

- `measureJointAxis`;
- `measureRootAxis`;
- `measurePhaseTiming`;
- `measureBilateralRotationError`.

Then compare that evidence with independently approved biomechanical expectations.

Do not choose a reference limit merely because it is one degree outside the
current implementation. A reference envelope should describe acceptable human
motion, not protect today's numbers.

## First independent-review questions

1. Is 5–30° a reasonable bottom-elbow envelope for the supported curl variants?
2. Is 115–140° an appropriate peak envelope?
3. Should standing hammer curls legitimately allow substantially more abduction
   than supinated/reverse curls, or should that remain an equipment-clearance
   correction rather than a reference preference?
4. Should incline-curl arm position be referenced relative to the trunk instead
   of root/world pitch in the next schema?
5. What maximum shoulder/upper-arm excursion should be considered a technique
   failure rather than natural late-rep movement?
6. Should tempo/reference timing use broad phase ratios or only sequencing until
   named tempo profiles have their own references?

Until these are reviewed, the curl reference is evidence-only and must not gate
approval.
