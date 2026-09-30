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

Repository tests prove, on the clean fallback, that:

- a generated bodyweight squat completes with no skipped body checks;
- a loaded hammer curl can be corrected within its certified family and passes
  equipment-clearance and arm-to-trunk checks;
- unsupported/ambiguous prompts are blocked before validation rather than
  guessed;
- generated definitions remain candidates and are not silently inserted into
  the exercise library.

Browser automation additionally exercises the live Generate panel. The
production-output smoke uses built `dist` content, generates a bodyweight squat,
requires `READY FOR REVIEW`, requires all rendered validation gates to pass,
and rejects any HTTP(S) request to a non-local origin.

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
- the certified family vocabulary is intentionally bounded;
- final production-package offline acceptance and physical-device evidence are
  still required;
- promotion of generated candidates remains an explicit human/code decision.

## Conclusion

Keep the current deterministic generation architecture.

Improve coverage by adding project-owned vocabulary, certified families and
validation evidence. Do not replace the generation system with a hosted runtime
AI service, and do not weaken validation to make new prompts pass.
