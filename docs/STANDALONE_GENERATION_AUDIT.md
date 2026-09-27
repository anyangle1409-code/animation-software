# Standalone prompt-generation audit

## Finding

The current exercise-generation pipeline is already architecturally compatible
with the zero-third-party operational target.

Verified source path:
- `src/generation/parse.ts`
- `src/generation/slots.ts`
- `src/generation/intent.ts`
- `src/generation/families.ts`
- `src/generation/generate.ts`
- `src/generation/validate.ts`

At source reference:
`chatgpt/absolute-retarget-imports @ 47187360b5d631d438a6b33b284ad06732e244cb`

## Current design

Prompt handling is:
- local;
- rule-based;
- deterministic;
- explainable;
- family-certified;
- bounded by project validation;
- corrected by project-owned numeric levers.

The parser explicitly says it is deterministic rather than a language model.
The generation loop does not require a hosted AI/LLM service.

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
5. use the existing validation/correction loop;
6. decline unsupported biomechanics rather than guessing.

If a learned model is ever proposed for the finished product, it must separately
satisfy the project's first-party provenance rule. Until then, the deterministic
parser is the approved production architecture.

## Remaining third-party coupling in generation

The generation **logic** is first-party, but its validation path currently uses
Three.js mathematics indirectly/directly, for example `Vector3` in
`src/generation/validate.ts` and the Three-based canonical
`PoseEvaluation`.

That dependency disappears through the prepared first-party math migration. It
does not require redesigning the prompt/generation architecture.

## Conclusion

Keep the generation architecture.

Replace its underlying third-party math/runtime implementation as part of the
normal Three.js migration; do not replace the generation system itself.
