# Phase 1 — close-until-contact cylindrical grip: implemented, not locked

Executing `docs/REFERENCE_BODY_PHASE1_GRIP_SOLVER.md` from `416ca2d`. Stage 1
frozen, **Stage 2 not started**, nothing promoted or merged.

Measured on `HomeGymPT_Male_STAGE1_CANDIDATE.glb`
(`c0d4b6905fc7ff5e3341e84843bdcf02f6086814bdb2f93e0e04454a69f1eefb`) with the
repaired harness as the source of truth.

## What the solver does

Each joint advances along the authored profile's pattern, proximal and distal
together, and locks where that digit's own skinned surface first reaches the
real finite cylinder. The authored profile is the upper bound and the
anatomical starting shape, so the result is the least deviation from the
accepted pose that stops penetrating.

Solving the joints one at a time from the base instead leaves the distal joints
straight while the base rotates, so an extended finger sweeps the handle and
locks the base far too early. That produced a pinky with a straight middle joint
and a bent tip — not a shape a hand makes. Advancing them together fixed it.

## Result, at the frozen grip centre, closure 0.85

| digit | MCP / PIP / DIP | nearest | inside |
|---|---|---|---|
| index | 30.4 / 80.8 / 51.0 | −0.46 mm | 0 |
| middle | 49.7 / 70.7 / 51.0 | −0.29 mm | 0 |
| ring | 49.7 / 57.2 / 51.0 | +0.18 mm | 0 |
| pinky | 19.3 / 33.6 / 51.0 | −0.22 mm | 0 |
| thumb | oppX +14, flex −18.7 / 51.0 / 51.0 | +3.80 mm | 0 |
| palm | — | −1.14 mm | 1 |

**Wrap 240°**, against ~160° for the only clean static profiles and a meaningless
339° for the static fist that closed through the bar. Authored static: −11.48 mm
over 53 vertices.

The thumb needed no change to its flexion. Its whole problem was the sign of
`thumbOppositionX`, which takes no per-side flip and so drove the thumb into the
handle on both hands.

## Where it lives, and why not in the grip profile

First attempt put the solved angles in `GRIP_PROFILES.dumbbell`. That broke four
canonical tests: `index_02_l` ended 42.7 mm from the canonical handle against a
32 mm bound. The canonical rig has its own finger lengths and its own handle
offset, so the pose that lands this character's fingers on the bar is not the
pose that lands the canonical rig's fingers on the canonical bar. One angle
table cannot serve both.

So the canonical rig keeps the authored profile and the solved grip is
character-scoped, in `src/character/solvedGrip.ts`, keyed by character and grip
family with the solved radius recorded alongside. `applyCharacterPose`
substitutes the solved rows when the frame says what is being held; the incoming
pose is shared, so it is never written to.

- `CharacterPoseContext.grip` carries `{ kind, closure }`.
- `StudioClip.hands` carries the clip's grip so both call sites can supply it.
- `CharacterBuild.gripSolutionId` marks which character may use which solution;
  it is only defaulted for a character that also carries its own
  `handleGripOffsets`, since those were measured on the same hand.
- `bar`, `handle` and `rope` keep the shared `thumbOppositionX: -14` until each
  is solved and validated in its own right, as the decision requires.

## Verification

- The production path is what was measured: `applyCharacterPose` with the grip
  context gives **4 vertices inside against 75 without it**, and the render
  through the shipped path reproduces the solved figures exactly.
- One table, re-used unchanged across curl Bottom / Mid / Peak, both hands, and
  shoulder press (also a dumbbell): every figure identical, which is what
  pose-invariance predicts for a rigidly held handle measured in its own frame.
- That identity was checked for deadness rather than assumed: perturbing the
  table by +12° at the index MCP moves the result to −4.30 mm with 2 inside.
- Renders share the metric's vertex set exactly.
- `src/character/solvedGrip.test.ts` guards the data: per-digit rows differ,
  opposition is positive where the profile's is negative, and every solved angle
  is inside the rig's joint limits at the curl's closure — the substitution does
  not re-run `clampPose`, so the angles have to be reachable unaided.
- Full suite: 297 passed, 1 skipped, 1 failed — the pre-existing `strainReview`
  5 s timeout, environmental and unrelated. Typecheck clean.

A harness note worth keeping: Vite reserves `PROD` as `import.meta.env.PROD` and
statically substitutes `process.env.PROD`, so an env flag by that name silently
reads empty inside a test. One run was measuring the wrong path before this
surfaced. The flag is now `SHIPPED`.

## Acceptance criteria

| # | criterion | status |
|---|---|---|
| 2 | palm naturally loaded | met — −1.14 mm, one vertex |
| 4 | thumb opposes and locks | met — +3.80 mm, none inside |
| 5 | no meaningful penetration | met — zero digits inside, worst −0.46 mm of skin press |
| 6 | palm not unloaded to clear digits | met — palm contact unchanged |
| 7 | no implausible joint angle | met — monotonic curl per digit, all inside rig limits |
| 8 | both hands symmetric | met — identical to the digit |
| 9 | handle centred, renderer/exporter agreement | met — grip centre untouched |
| 10 | curl Bottom/Mid/Peak stable | met — identical at all three |
| 11 | second cylindrical handle, no per-exercise numbers | met for shoulder press, same 15 mm family; untested at another diameter |
| 12 | hand/wrist and equipment lock no regression | met — full suite baseline unchanged |
| 1, 3 | reads as a convincing full fist; all four fingers substantially wrap | **not certified** — see below |

## Why I am not locking Phase 1

Criteria 1 and 3 are visual, and I will not sign them off on my own flat-shaded
diagnostic render.

What that render does show is a genuine wrap, not a fingertip hook and not the
~160° cupped hand the decision rules out: all four digits contact, the palm is
loaded, the thumb opposes. It also shows roughly 120° of the circumference open
at the lower right — the fingertips come around the handle but do not close
under it.

The reason is visible in the solved angles: every MCP locks early (index 30.4°
against an authored 66.3°, pinky 19.3°) because the proximal phalanx reaches the
handle almost immediately. The handle centre sits close enough to the MCP row
that the knuckles cannot roll over it, which caps the wrap near 240°.

That points at MCP placement relative to the frozen `handleGripOffsets`, and
"finger lengths or MCP joint placement must be changed" is a listed stop
condition. So this is the report rather than the lock, and **Stage 2 has not
been started**. The work above is retained and safe either way: it is a large,
validated improvement over a hand that closed 11.48 mm through the bar.

What would settle it: a high-zoom Studio render of the solved grip for the
visual call, and, if that call is "not yet a full fist", a decision on whether
the handle centre may move proximally within the palm — which is Stage 1 data
and therefore yours, not mine.
