# Standalone prompt-generation audit

## Current finding

The exercise-generation pipeline is operationally first-party and compatible
with the zero-runtime-dependency target.

Current live path:

- `src/generation/parse.ts`
- `src/generation/slots.ts`
- `src/generation/intent.ts`
- `src/generation/families.ts`
- `src/generation/generate.ts`
- `src/generation/validate.ts`
- `src/editor/generationStoreCore.ts`

The parser, family selection, validation and bounded correction loop are local,
deterministic and project-owned. They do not require a hosted AI/LLM service.

## Live validation character

Until ORIGINAL v1 is production-approved, the live Generate panel validates
body-dependent checks against the clean project-authored procedural fallback:

`Home Gym PT clean scaffold`

This is the same first-party operational fallback used elsewhere in the studio.
It is not the final production character and must not be promoted as ORIGINAL
v1, but it allows prompt generation to run equipment/body/self-clearance checks
without borrowing any legacy or imported character.

The fallback is built lazily once per app session and reused serially by the
generation store.

## Current automated evidence

Repository tests prove on the clean project-authored procedural fallback that
**every currently certified generator family** can be built and fully validated
with no skipped body checks:

- curl — including bounded correction of a loaded hammer curl;
- overhead press — standing dumbbell shoulder press;
- horizontal press — standard push-up;
- supine — flat dumbbell bench press and dumbbell fly, both passing the same
  clean-fallback equipment/body clearance gate without relaxing its limits;
- trunk flexion — bodyweight crunch and sit-up, both reproducing the accepted
  family motion and fully validating with no skipped body checks;
- carry — farmer's walk with paired dumbbells, preserving the family's fixed
  two-step gait and exported travel speed; tempo/distance variants remain blocked;
- rotation — seated bodyweight Russian twist and the accepted high-to-low cable woodchop;
- anti-rotation — standing cable Pallof press with the accepted two-hand press line and no-twist constraints;
- squat — bodyweight air squat;
- lunge — split/forward/reverse family evidence, with reverse lunge in the
  all-family clean-fallback certification loop;
- calf — bodyweight standing calf raise and the paired-dumbbell loaded variant;
- hinge — dumbbell Romanian deadlift;
- row — dumbbell bent-over row;
- raise — lateral and front raises;
- vertical pull — strict pull-up;
- extension — dumbbell overhead triceps extension and straight-bar cable triceps pushdown.

For the supine family, an initial clean-fallback run measured the bench pad
3.04 mm from the body against the existing 3.00 mm support-contact limit. The
bench placement was corrected by 0.1 mm at the family source; the threshold was
not weakened. The full clean-fallback family loop then passed.

The same suite also proves that accepted family defaults reproduce the relevant
hand-authored library motion where that comparison is defined, generated
definitions remain candidates rather than silently entering the library, and
unsupported/ambiguous requests are blocked instead of guessed.

Current structural coverage is **28 / 28 registered exercises** across all
**16 core movement families**. `src/generation/libraryCoverage.test.ts`
requires every registered exercise to appear in exactly one generator family's
proving set and requires each product-facing exercise name to parse back to its
exact library reference. This is a maintenance gate, not a claim that every
conceivable variation of those movements is certified.

Deterministic prompt-language hardening is also verified without widening the
biomechanical boundary:

- tested safe aliases include RDL/OHP, press-up, farmer's carries, heel raise and
  pressdown spellings;
- mobile smart apostrophes and Unicode dash/hyphen variants are normalised;
- common equipment spellings/spacing are recognised instead of being silently
  ignored;
- `tempo 3010` is accepted as compact 3-0-1-0 notation;
- unilateral hand/arm wording is caught and blocked when only bilateral motion
  is certified;
- written number words are parsed for supported weight/angle units instead of
  being silently ignored;
- ambiguous free-weight/plate/hand-weight wording, unsupported repetition
  styles, set/rep/timed prescriptions, total/combined dumbbell loads, written
  carry distances and explicit single-dumbbell requests are all blocked when
  the current certified/output schema cannot represent them faithfully;
- explicit support/grip/angle, stance-width, foot-orientation, movement-range
  and joint-path directives are blocked when the selected family has no
  corresponding intent field;
- no-pause/touch-and-go/continuous-repetition timing, vague pace/speed wording
  and phase-specific timing are blocked instead of being replaced by the family
  default; complete supported tempo notation remains accepted;
- qualitative workout programming (for example high/low reps, multiple sets,
  "for reps" and "as many reps as possible") is blocked because the current
  product generates one validated repetition clip;
- unsupported push-up support variants such as wall/bench/counter/table,
  assisted, handles and parallettes are blocked rather than approximated;
- the Generate panel exposes the simple `exercise: ...` workflow directly and
  reports cable equipment as cable rather than bodyweight.

The exact product-level shorthand requested for normal use is covered by the
production-output browser smoke:

`exercise: dumbbell shoulder press`

Against built `dist`, the live Generate panel must take that command to
`READY FOR REVIEW`, show the clean first-party fallback as the validation
character, emit validation gates, and have **zero non-pass gates**. The smoke
uses the same local deterministic generation path as longer natural-language
requests; there is no separate command parser or hosted service.

The same production smoke also:

- fully validates a generated bodyweight squat;
- fully validates `exercise: cable triceps pushdown` and requires the live
  Generate panel to report `Cable station`, not bodyweight;
- fully validates the mobile-keyboard spelling `exercise: farmer’s walk`
  (smart apostrophe) through the built production bundle;
- submits an unsupported goblet squat and requires `NEEDS A DECISION` with a
  local, specific explanation and no preview/approval candidate actions;
- requires the project-owned WebGL renderer to draw the production build;
- records browser HTTP(S) traffic and fails if any request leaves the local
  preview origin.

These browser checks are supplementary automated evidence. They do not close
the final ORIGINAL-v1 packaging or real desktop/iPhone offline acceptance gates.


## Standalone rule

Do **not** introduce a runtime dependency on:

- OpenAI API;
- Anthropic API;
- Gemini/Google AI;
- hosted inference APIs;
- remote embeddings/rerankers;
- cloud-only prompt interpretation;
- downloaded third-party language models.

Development assistance from GPT/Claude remains allowed because it is not part of
the finished operational product.

## How to make prompt handling smarter without third-party runtime AI

Prefer:

1. expand project-owned vocabulary/slot parsing;
2. add certified movement families;
3. add deterministic synonyms/grammar;
4. add project-owned intent disambiguation;
5. extend first-party validation/correction evidence;
6. decline unsupported biomechanics rather than guessing.

If a learned model is ever proposed for the finished product, it must separately
satisfy the project's first-party provenance rule. Until then, the deterministic
parser is the approved production architecture.

## Current dependency state

Generation no longer has a Three/runtime-framework dependency to migrate away.
The math, scene, character deformation, collision and rendering paths beneath
generation are project-owned, and guarded third-party source-import ceilings are
zero.

Do not reopen the completed dependency migration merely because this historical
audit once described Three-based validation.

## Remaining generation work

The architecture is approved, but release acceptance remains open because:

- ORIGINAL v1 is not yet the production validation/render character;
- all current library exercises have deterministic prompt routes, but the accepted
  vocabulary and biomechanical variants remain intentionally bounded; new variants
  still require their own validation evidence;
- final production-package offline acceptance and physical-device evidence are
  still required;
- promotion of generated candidates remains an explicit human/code decision.

## Conclusion

Keep the current deterministic generation architecture.

Keep improving coverage only from concrete evidence: add project-owned
vocabulary when a real prompt would otherwise be misread, add a new family or
variant only with its own validation evidence, and keep unsupported intent
blocked rather than guessed. Do not replace the generation system with a hosted
runtime AI service, and do not weaken validation to make new prompts pass.
