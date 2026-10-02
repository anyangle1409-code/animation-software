import type { ParsedPrompt } from './intent';
import { GENERATOR_FAMILIES } from './families';
import type { GeneratorFamily } from './families';
import { readSlots } from './slots';

const escapeRegExp = (text: string) =>
  text.replace(/[.*+?^$\{\}()|[\]\\]/g, (character) => `\\${character}`);

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
 * movements that share a word with a certified family ("leg curl", "chest
 * press"). Checked first, so neither is mistaken for a certified family.
 */
const NOT_CERTIFIED: [RegExp, string][] = [
  [/\b(?:leg|hamstring|nordic|lying leg)\s+curls?\b/, 'a leg curl works the hamstrings on a machine; the curl family is the elbow-flexion curl.'],
  [/\bwrist\s+curls?\b/, 'a wrist curl moves only the wrist; not certified.'],
  [/\b(?:chest|floor)\s+press(?:es)?\b/, 'only the flat dumbbell bench press is certified in the supine family; generic chest presses and floor presses are not.'],
  [/\bleg\s+press\b/, 'a leg press needs a machine the equipment library does not have.'],
  [/(?<!romanian\s)\bdeadlifts?\b|\bhip\s+hinges?\b|\bgood\s?mornings?\b/, 'only the bilateral dumbbell Romanian deadlift is certified in the hinge family; conventional deadlifts, generic hinges and good mornings are not.'],
  [/\b(?:barbell|cable|machine|upright|pendlay|renegade|seated|chest[-\s]?supported|seal)\s+rows?\b/, 'only the bilateral dumbbell bent-over row is certified in the row family.'],
  [/\bchin[-\s]?ups?\b|\blat\s+pull/, 'only the strict pronated bodyweight pull-up is certified in the vertical-pull family.'],
  [/\b(?:rear(?:[-\s]?delt)?|bent[-\s]?over|incline|plate)\s+raises?\b/, 'only the bilateral standing dumbbell lateral and front raises are certified in the raise family.'],
  [/\bskull\s?crushers?\b|\b(?:lying|cable)\s+(?:triceps?\s+)?extensions?\b/, 'only the standing bilateral dumbbell overhead extension and straight-bar cable pushdown are certified in the extension family.'],
  [/\b(?:suitcase|waiter|overhead|front[-\s]?rack|rack|trap[-\s]?bar|hex[-\s]?bar)\s+(?:walk|carry)\b/, "only the bilateral dumbbell farmer's walk is certified in the carry family."],
];

const UNSUPPORTED_REP_STYLE = [
  /\bpartial\b/,
  /\b(?:half|quarter)[-\s]?(?:reps?|repetitions?)\b/,
  /\b(?:top|bottom)[-\s]+half\b/,
  /\b(?:1\.5|one[-\s]+and[-\s]+a[-\s]+half)[-\s]?(?:reps?|repetitions?)\b/,
  /\beccentric[-\s]?only\b|\bnegative[-\s]?(?:reps?|repetitions?)\b/,
  /\b(?:isometric(?:s)?|iso[-\s]?holds?|static[-\s]+holds?)\b/,
  /\b(?:paused?|pausing)\b/,
  /\b(?:hold|holding)\s+(?:at|in|for)\b/,
  /\beccentrics?\b|\bnegatives?\b/,
];

const UNSUPPORTED_PAUSE_STYLE =
  /\b(?:no[-\s]+pauses?|without[-\s]+pauses?|touch[-\s]+and[-\s]+go|continuous(?:ly)?[-\s]+reps?|continuous[-\s]+repetitions?)\b/;

const COUNT_WORD =
  '(?:\\d+(?:\\.\\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred)';
const RANGE_NUMBER =
  `(?:\\d+(?:\\.\\d+)?|${COUNT_WORD}(?:[-\\s]+(?:and[-\\s]+)?${COUNT_WORD})*)`;
const DIGIT_RANGE_NUMBER = '\\d+(?:\\.\\d+)?';
const WEIGHT_UNIT = '(?:kgs?|kilo(?:gram)?s?|lbs?|pounds?)';
const ANGLE_UNIT = '(?:(?:degrees?|deg)\\b|[°º])';
const UNSUPPORTED_LOAD_RANGE = [
  // A hyphen inside a valid written number ("twenty-five") is not a range.
  // Hyphenated ranges therefore require numeric endpoints; written ranges use
  // "to", "through", or "between ... and ...".
  new RegExp(`\\b${DIGIT_RANGE_NUMBER}\\s*-\\s*${DIGIT_RANGE_NUMBER}\\s*${WEIGHT_UNIT}\\b`),
  new RegExp(`\\b${RANGE_NUMBER}\\s*(?:to|through)\\s*${RANGE_NUMBER}\\s*${WEIGHT_UNIT}\\b`),
  new RegExp(`\\bbetween\\s+${RANGE_NUMBER}\\s+and\\s+${RANGE_NUMBER}\\s*${WEIGHT_UNIT}\\b`),
];
const UNSUPPORTED_ANGLE_RANGE = [
  new RegExp(`\\b${DIGIT_RANGE_NUMBER}\\s*-\\s*${DIGIT_RANGE_NUMBER}\\s*${ANGLE_UNIT}`),
  new RegExp(`\\b${RANGE_NUMBER}\\s*(?:to|through)\\s*${RANGE_NUMBER}\\s*${ANGLE_UNIT}`),
  new RegExp(`\\bbetween\\s+${RANGE_NUMBER}\\s+and\\s+${RANGE_NUMBER}\\s*${ANGLE_UNIT}`),
];

const PHASE_WORD = '(?:eccentric|concentric|lower(?:ing)?|lift(?:ing)?|descent|ascent|down|up)';
const QUALITATIVE_TEMPO_WORD = '(?:slow(?:ly)?|fast|quick(?:ly)?|explosive(?:ly)?|controll?ed)';
const UNSUPPORTED_PHASE_TIMING = [
  new RegExp(`\\b${COUNT_WORD}[-\\s]*(?:s|secs?|seconds?)\\s+${PHASE_WORD}\\b`),
  new RegExp(`\\b${PHASE_WORD}\\s+(?:for\\s+)?${COUNT_WORD}\\s*(?:s|secs?|seconds?)\\b`),
  new RegExp(`\\b${QUALITATIVE_TEMPO_WORD}[-\\s]+${PHASE_WORD}\\b`),
  new RegExp(`\\b${PHASE_WORD}[-\\s]+${QUALITATIVE_TEMPO_WORD}\\b`),
];
const UNSUPPORTED_PROGRAMMING = [
  new RegExp(`\\b${COUNT_WORD}\\s*(?:sets?|reps?|repetitions?)\\b`),
  new RegExp(`\\bsets?\\s+of\\s+${COUNT_WORD}\\b`),
  new RegExp(`\\b${COUNT_WORD}\\s*(?:rounds?|circuits?)\\b`),
  new RegExp(`\\bfor\\s+${COUNT_WORD}\\s*(?:seconds?|secs?|minutes?|mins?)\\b`),
  /\b\d+\s*[x×]\s*\d+\b/,
  /\b(?:drop[-\s]?sets?|super[-\s]?sets?|giant[-\s]?sets?|cluster[-\s]?sets?|rest[-\s]?pause)\b/,
  /\b(?:amrap|emom)\b/,
  /\b(?:to|until)\s+failure\b/,
  /\brpe\s*\d+(?:\.\d+)?\b|\brir\s*\d+\b|\breps?\s+in\s+reserve\b/,
  /\brest(?:ing)?\s+(?:for\s+)?\d+(?:\.\d+)?\s*(?:s|secs?|seconds?|m|mins?|minutes?)\b/,
];

const NEGATED_GRIP =
  /\b(?:not|no|without)\s+(?:a\s+)?(?:neutral(?:[-\s]grip)?|hammer[-\s]grip|underhand|overhand|supinat(?:ed|ion)|pronat(?:ed|ion)|palms?\s+(?:facing\s+)?(?:up|down|forwards?|each\s+other|inwards?))\b/;
const NEGATED_SUPPORT =
  /\b(?:not|no|without)\s+(?:being\s+)?(?:standing|seated|sitting|sat|inclined?|lying|supine|hanging|floor[-\s]?supported)\b/;
const NEGATED_TEMPO =
  /\b(?:not|no|without)\s+(?:a\s+)?(?:slow(?:ly)?|fast|quick(?:ly)?|controll?ed|explosive(?:ly)?)(?:\s+tempo)?\b/;
const UNSUPPORTED_SUPPORT_POSITION =
  /\b(?:half[-\s]?)?kneeling\b|\bquadruped\b|\ball[-\s]+fours\b/;
const UNSUPPORTED_STANCE_WIDTH =
  /\b(?:wide|narrow|close|staggered|shoulder[-\s]?width|hip[-\s]?width)[-\s]+stance\b|\b(?:feet|foot)\s+(?:(?:shoulder|hip)[-\s]?width(?:\s+apart)?|wide|wider|close|closer|together)\b/;
const UNSUPPORTED_FOOT_ORIENTATION =
  /\b(?:(?:front|back|rear)\s+)?(?:toes?|feet|foot)\s+(?:(?:turn(?:ed)?|point(?:ed)?)\s+)?(?:out(?:wards?)?|in(?:wards?)?|forwards?)\b|\b(?:turn|point)\s+(?:the\s+)?(?:(?:front|back|rear)\s+)?(?:toes?|feet|foot)\s+(?:out(?:wards?)?|in(?:wards?)?|forwards?)\b/;
const UNSUPPORTED_GRIP_WIDTH =
  /\b(?:wide|narrow|close)[-\s]+grip\b|\bhands?\s+(?:wide|wider|close|closer|together)\b/;
const UNSUPPORTED_RANGE_OR_PATH = [
  /\b(?:atg|ass[-\s]+to[-\s]+grass|to[-\s]+parallel|below[-\s]+parallel|above[-\s]+parallel|parallel[-\s]+squats?)\b/,
  /\b(?:elbows?|arms?)\s+(?:tucked|flared|out|in)\b|\b(?:tuck|flare)\s+(?:the\s+)?elbows?\b/,
  /\b(?:no|without)\s+(?:full[-\s]+)?lock[-\s]?out\b|\bstop(?:ping)?\s+short\s+of\s+(?:full[-\s]+)?lock[-\s]?out\b/,
];
const UNSUPPORTED_LOWER_SIDE =
  /\b(?:left|right)[-\s]?(?:leg|foot)(?:ed)?\b|\b(?:on|with|using)\s+(?:the\s+)?(?:left|right)\s+(?:leg|foot)\b/;

export function parsePrompt(prompt: string): ParsedPrompt {
  const slots = readSlots(prompt);

  for (const pattern of UNSUPPORTED_LOAD_RANGE) {
    const match = slots.text.match(pattern);
    if (match) {
      return {
        prompt,
        intent: null,
        assumptions: [],
        issues: [{
          code: 'load',
          message:
            `"${match[0]}": the current exercise intent stores one exact load, not a load range. ` +
            'Give one exact load per hand, or omit it to use the documented family default.',
          blocking: true,
        }],
      };
    }
  }

  for (const pattern of UNSUPPORTED_ANGLE_RANGE) {
    const match = slots.text.match(pattern);
    if (match) {
      return {
        prompt,
        intent: null,
        assumptions: [],
        issues: [{
          code: 'angle',
          message:
            `"${match[0]}": the current exercise intent stores one exact support angle, not an angle range. ` +
            'Give one certified angle or omit the angle.',
          blocking: true,
        }],
      };
    }
  }

  const unsupportedPauseStyle = slots.text.match(UNSUPPORTED_PAUSE_STYLE);
  if (unsupportedPauseStyle) {
    return {
      prompt,
      intent: null,
      assumptions: [],
      issues: [{
        code: 'tempo',
        message:
          `"${unsupportedPauseStyle[0]}": pause/continuous-repetition style changes are not independently represented by the current family clip. ` +
          'Use a complete four-phase tempo if exact phase timing matters, or omit the directive to use the certified family timing.',
        blocking: true,
      }],
    };
  }

  for (const pattern of UNSUPPORTED_REP_STYLE) {
    const match = slots.text.match(pattern);
    if (match) {
      return {
        prompt,
        intent: null,
        assumptions: [],
        issues: [{
          code: 'variant',
          message: `"${match[0]}": partial/eccentric-only repetition styles change the certified range or repetition structure and are not substituted with a normal full repetition.`,
          blocking: true,
        }],
      };
    }
  }

  // A phrase introduced by "tempo" or "cadence" is a timing constraint first.
  // Classify malformed/invalid timing before the generic NxN workout-programming
  // guard so "tempo 30x0" cannot be mistaken for a "30x0" set/rep prescription.
  const timingDirective = slots.text.match(/\b(?:tempo|cadence|pace|speed)\b/);
  if (timingDirective && slots.tempo.length === 0) {
    return {
      prompt,
      intent: null,
      assumptions: [],
      issues: [{
        code: 'tempo',
        message:
          `"${timingDirective[0]}": a timing instruction was given but no supported tempo could be read. ` +
          'Use a named profile such as slow/controlled/fast or four-phase seconds such as "tempo 3-1-2-0" / "tempo 3010".',
        blocking: true,
      }],
    };
  }

  const invalidExplicitTempo = slots.tempo.find((slot) =>
    'explicit' in slot.value &&
    (slot.value.explicit.eccentric <= 0 || slot.value.explicit.concentric <= 0)
  );
  if (invalidExplicitTempo) {
    return {
      prompt,
      intent: null,
      assumptions: [],
      issues: [{
        code: 'tempo',
        message:
          `"${invalidExplicitTempo.words}": lowering and lifting phases must both have positive duration; zero is only valid for pause phases.`,
        blocking: true,
      }],
    };
  }

  for (const pattern of UNSUPPORTED_PHASE_TIMING) {
    const match = slots.text.match(pattern);
    if (match) {
      return {
        prompt,
        intent: null,
        assumptions: [],
        issues: [{
          code: 'tempo',
          message:
            `"${match[0]}": phase-specific timing is not represented independently by the current family clips. ` +
            'Use a complete four-phase tempo such as "tempo 3-1-2-0" / "tempo 3010", or omit the phase timing.',
          blocking: true,
        }],
      };
    }
  }

  for (const pattern of UNSUPPORTED_PROGRAMMING) {
    const match = slots.text.match(pattern);
    if (match) {
      return {
        prompt,
        intent: null,
        assumptions: [],
        issues: [{
          code: 'programming',
          message: `"${match[0]}": the generator currently produces one validated repetition clip; set/rep counts and timed-set duration are not encoded yet.`,
          blocking: true,
        }],
      };
    }
  }

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

  const unsupportedSupport = slots.text.match(UNSUPPORTED_SUPPORT_POSITION);
  if (unsupportedSupport) {
    return {
      prompt,
      intent: null,
      assumptions: [],
      issues: [{
        code: 'support',
        message: `"${unsupportedSupport[0]}": that body-support position is not certified by the current generator families and cannot be replaced with the family default.`,
        blocking: true,
      }],
    };
  }

  const unsupportedStance = slots.text.match(UNSUPPORTED_STANCE_WIDTH);
  if (unsupportedStance) {
    return {
      prompt,
      intent: null,
      assumptions: [],
      issues: [{
        code: 'variant',
        message: `"${unsupportedStance[0]}": stance-width/offset changes are not prompt-parameterised by the certified families and cannot be replaced with the family default stance.`,
        blocking: true,
      }],
    };
  }

  const unsupportedFootOrientation = slots.text.match(UNSUPPORTED_FOOT_ORIENTATION);
  if (unsupportedFootOrientation) {
    return {
      prompt,
      intent: null,
      assumptions: [],
      issues: [{
        code: 'variant',
        message:
          `"${unsupportedFootOrientation[0]}": foot/toe orientation is not prompt-parameterised by the certified families and cannot be substituted with the family default foot angle.`,
        blocking: true,
      }],
    };
  }

  const unsupportedLowerSide = slots.text.match(UNSUPPORTED_LOWER_SIDE);
  if (unsupportedLowerSide) {
    return {
      prompt,
      intent: null,
      assumptions: [],
      issues: [{
        code: 'execution',
        message:
          `"${unsupportedLowerSide[0]}": explicit left/right leg or foot execution is not encoded by the current certified repetition and cannot be replaced with the even/default side pattern.`,
        blocking: true,
      }],
    };
  }

  const unsupportedGripWidth = slots.text.match(UNSUPPORTED_GRIP_WIDTH);
  if (unsupportedGripWidth) {
    return {
      prompt,
      intent: null,
      assumptions: [],
      issues: [{
        code: 'grip',
        message: `"${unsupportedGripWidth[0]}": grip/hand spacing is not prompt-parameterised by the certified families and cannot be replaced with the family default spacing.`,
        blocking: true,
      }],
    };
  }

  for (const pattern of UNSUPPORTED_RANGE_OR_PATH) {
    const match = slots.text.match(pattern);
    if (match) {
      return {
        prompt,
        intent: null,
        assumptions: [],
        issues: [{
          code: 'variant',
          message:
            `"${match[0]}": requested range-of-motion or joint-path changes are not prompt-parameterised by the certified families. ` +
            'Use the family-certified full movement, or add a separately validated variant before requesting that path.',
          blocking: true,
        }],
      };
    }
  }

  const movementWords = slots.text.match(matches[0].detect)?.[0];
  if (movementWords) {
    const negatedMovement = slots.text.match(
      new RegExp(`\\b(?:not|no|without)\\s+(?:an?\\s+)?${escapeRegExp(movementWords)}\\b`),
    );
    if (negatedMovement) {
      return {
        prompt,
        intent: null,
        assumptions: [],
        issues: [{
          code: 'family',
          message: `"${negatedMovement[0]}": the only detected exercise is explicitly negated. Name the exercise you do want instead.`,
          blocking: true,
        }],
      };
    }
  }

  const negatedGrip = slots.text.match(NEGATED_GRIP);
  if (negatedGrip) {
    return {
      prompt,
      intent: null,
      assumptions: [],
      issues: [{
        code: 'grip',
        message: `"${negatedGrip[0]}": a negated grip cannot be treated as the positive grip token or silently replaced with the family default. State the grip you do want.`,
        blocking: true,
      }],
    };
  }

  const negatedSupport = slots.text.match(NEGATED_SUPPORT);
  if (negatedSupport) {
    return {
      prompt,
      intent: null,
      assumptions: [],
      issues: [{
        code: 'support',
        message: `"${negatedSupport[0]}": a negated body/support position cannot be treated as a positive position or silently replaced with the family default. State the support you do want.`,
        blocking: true,
      }],
    };
  }

  const negatedTempo = slots.text.match(NEGATED_TEMPO);
  if (negatedTempo) {
    return {
      prompt,
      intent: null,
      assumptions: [],
      issues: [{
        code: 'tempo',
        message: `"${negatedTempo[0]}": a negated tempo cannot be treated as the positive tempo token or silently replaced with the family default. State the tempo you do want.`,
        blocking: true,
      }],
    };
  }

  const interpretation = matches[0].interpret(slots, prompt);
  return { prompt, ...interpretation };
}
