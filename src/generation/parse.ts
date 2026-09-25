import type { ParsedPrompt } from './intent';
import { GENERATOR_FAMILIES } from './families';
import type { GeneratorFamily } from './families';
import { readSlots } from './slots';

/**
 * Natural-language request → `ExerciseIntent`.
 *
 * Rule-based and deterministic rather than a language model: the vocabulary a
 * certified family can act on is small and exact, the same sentence must always
 * produce the same exercise, and every decision has to be explainable in the
 * review. A model can be put in front of this later to rephrase a request into
 * these terms; it should not replace the part that decides.
 *
 * The parser recognises every movement in the library, and declines the ones
 * not yet certified for generation with the reason, so a request is never
 * quietly answered with the nearest thing that is certified.
 */

/**
 * Movements the library has but the generator is not certified to build, and
 * movements that share a word with a certified family ("leg curl", "bench
 * press"). Checked first, so neither is mistaken for a certified family.
 */
const NOT_CERTIFIED: [RegExp, string][] = [
  [/\b(?:leg|hamstring|nordic|lying leg)\s+curls?\b/, 'a leg curl works the hamstrings on a machine; the curl family is the elbow-flexion curl.'],
  [/\bwrist\s+curls?\b/, 'a wrist curl moves only the wrist; not certified.'],
  [/\b(?:bench|chest|floor|incline bench|incline chest|incline dumbbell)\s+press(?:es)?\b|\bfl(?:y|ies|yes)\b/, 'lying presses and flyes belong to the supine family (dumbbell bench press, dumbbell fly), which is not certified for generation yet.'],
  [/\bleg\s+press\b/, 'a leg press needs a machine the equipment library does not have.'],
  [/\bpush[-\s]?ups?\b|\bpress[-\s]?ups?\b/, 'the push-up family (push-up) is not certified for generation yet.'],
  [/\brows?\b/, 'the row family (bent-over row) is not certified for generation yet.'],
  [/\b(?:pull|chin)[-\s]?ups?\b|\blat\s+pull/, 'the vertical-pull family (pull-up) is not certified for generation yet.'],
  [/\b(?:lateral|side|front)\s+raises?\b/, 'the raise family (lateral and front raise) is not certified for generation yet.'],
  [/\btriceps?\b|\bskull\s?crushers?\b|\bpush[-\s]?downs?\b|\bextensions?\b/, 'the extension family (overhead extension, cable pushdown) is not certified for generation yet.'],
  [/\bcalf\s+raises?\b|\bcalves\b/, 'the calf family (calf raises) is not certified for generation yet.'],
  [/\bfarmers?'?s?\s+(?:walk|carry)\b|\bcarry\b|\bcarries\b/, "the carry family (farmer's walk) is not certified for generation yet."],
  [/\bcrunch(?:es)?\b|\bsit[-\s]?ups?\b/, 'the trunk-flexion family (crunch, sit-up) is not certified for generation yet.'],
  [/\brussian\s+twists?\b|\bwood\s?chops?\b|\bpallof\b/, 'the rotation and anti-rotation families are not certified for generation yet.'],
];

export function parsePrompt(prompt: string): ParsedPrompt {
  const slots = readSlots(prompt);

  for (const [pattern, reason] of NOT_CERTIFIED) {
    const match = slots.text.match(pattern);
    // A certified family named alongside is still that family: "a curl, not a
    // leg curl" is not what this guards, but "incline dumbbell press" is.
    if (match) {
      const certified = GENERATOR_FAMILIES.find((family) => family.detect.test(slots.text.replace(match[0], ' ')));
      if (!certified) {
        return {
          prompt,
          intent: null,
          assumptions: [],
          issues: [{ code: 'family', message: `"${match[0]}": ${reason}`, blocking: true }],
        };
      }
    }
  }

  const matches: GeneratorFamily[] = GENERATOR_FAMILIES.filter((family) => family.detect.test(slots.text));
  if (matches.length === 0) {
    return {
      prompt,
      intent: null,
      assumptions: [],
      issues: [
        {
          code: 'family',
          message:
            'No certified movement was named. The generator can build ' +
            GENERATOR_FAMILIES.map((family) => family.label.toLowerCase()).join(' and ') +
            ' variants, e.g. "a standing hammer curl with 12 kg dumbbells".',
          blocking: true,
        },
      ],
    };
  }
  if (matches.length > 1) {
    return {
      prompt,
      intent: null,
      assumptions: [],
      issues: [
        {
          code: 'family',
          message: `The request names more than one movement (${matches.map((family) => family.label.toLowerCase()).join(', ')}). Ask for one exercise at a time.`,
          blocking: true,
        },
      ],
    };
  }

  const interpretation = matches[0].interpret(slots, prompt);
  return { prompt, ...interpretation };
}
