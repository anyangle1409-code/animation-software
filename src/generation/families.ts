import type { CommonError, ExerciseDefinition, MuscleInvolvement } from '../exercises/types';
import { curlFamily } from '../exercises/families/curl';
import type { CurlVariant } from '../exercises/families/curl';
import { pressFamily } from '../exercises/families/press';
import type { PressVariant } from '../exercises/families/press';
import type { ExerciseIntent, GeneratorFamilyId, IntentGrip, IntentIssue, IntentSupport } from './intent';
import { tempoOf } from './intent';
import type { PromptSlots } from './slots';
import { distinct } from './slots';

/**
 * The movement families the generator may build from, and what each needs to
 * turn an intent into a finished variant.
 *
 * An adapter here is not an exercise. It holds no angles, poses or rules — those
 * stay in the family builder, where the library's own exercises get them — only
 * the translation from the intent's vocabulary into the builder's typed variant,
 * the library exercise a candidate is measured against, and the parameters the
 * correction loop may move. Adding a variant the family already supports needs
 * no code here; adding a family means writing one adapter, not one per exercise.
 *
 * Only families listed here are certified for generation. Everything else in
 * the library is recognised by the parser and declined with the reason, rather
 * than approximated by the nearest thing that is certified.
 */

/** The checks a lever can be asked to resolve; see `validate.ts`. */
export type LeverCheck = 'equipmentClearance' | 'armTrunk';

/**
 * One family parameter the correction loop may move, and how far.
 *
 * Levers are the only thing the loop can change, and they change the variant —
 * the same fields a hand-written definition would set — never a validation
 * limit, which the loop has no access to. Each is bounded by what its family
 * already documents as sound, and says why it is the right lever.
 */
export interface Lever<V> {
  id: string;
  label: string;
  resolves: LeverCheck[];
  read(variant: V): number;
  write(variant: V, value: number): V;
  /** Degrees per attempt; the sign is the direction. */
  step: number;
  /** The furthest value it may reach. */
  limit: number;
  why: string;
}

export interface Interpretation {
  intent: ExerciseIntent | null;
  assumptions: string[];
  issues: IntentIssue[];
}

export interface GeneratorFamily<V extends { id: string; name: string } = { id: string; name: string }> {
  id: GeneratorFamilyId;
  label: string;
  /** The family builder's exported name, for showing the generated source. */
  builder: string;
  /** Matches a request for this family. */
  detect: RegExp;
  /** The library exercises built from this family: the proving set. */
  library: string[];
  interpret(slots: PromptSlots, prompt: string): Interpretation;
  variant(intent: ExerciseIntent): V;
  build(variant: V): ExerciseDefinition;
  /** The library exercise a candidate is compared with. Never a template. */
  reference(intent: ExerciseIntent): string;
  levers: Lever<V>[];
}

const blocking = (code: string, message: string): IntentIssue => ({ code, message, blocking: true });

const quote = (words: string[]) => words.map((word) => `"${word}"`).join(' and ');

/**
 * The slots every dumbbell family reads the same way: implement, execution,
 * load and tempo. Grip and support differ by family and are left to it.
 */
function interpretCommon(
  slots: PromptSlots,
  family: string,
  defaultLoad: number,
  assumptions: string[],
  issues: IntentIssue[],
): { load: number; tempo: ExerciseIntent['tempo'] } {
  const others = slots.equipment.filter((slot) => slot.value !== 'dumbbell');
  if (others.length > 0) {
    issues.push(
      blocking(
        'equipment',
        `${quote(others.map((slot) => slot.words))}: the ${family} family is certified with dumbbells only.`,
      ),
    );
  } else if (slots.equipment.length === 0) {
    assumptions.push('Dumbbells, one in each hand — the implement this family is certified with.');
  }

  if (slots.execution.length > 0) {
    issues.push(
      blocking(
        'execution',
        `${quote(slots.execution.map((slot) => slot.words))}: only both arms together is certified. ` +
          'Alternating and single-arm work change the whole repetition, so it is not substituted silently — ' +
          'ask for the two-arm version to proceed.',
      ),
    );
  }

  const loads = distinct(slots.loads);
  let load = defaultLoad;
  if (loads.length > 1) {
    issues.push(blocking('load', `Several loads were given (${quote(slots.loads.map((slot) => slot.words))}); say which one per hand.`));
  } else if (loads.length === 1) {
    load = loads[0];
    if (!(load >= 1 && load <= 60)) {
      issues.push(blocking('load', `${slots.loads[0].words} per hand is outside the 1–60 kg a dumbbell rack holds; check the number.`));
    }
    if (/lb|pound/.test(slots.loads[0].words)) assumptions.push(`${slots.loads[0].words} read as ${load} kg per hand.`);
    else assumptions.push(`${load} kg read as the load in each hand.`);
  } else {
    assumptions.push(`${defaultLoad} kg per hand, the family's default load. The load is recorded for export; it does not change the motion.`);
  }

  const tempos = slots.tempo;
  let tempo: ExerciseIntent['tempo'] = { profile: 'family' };
  const kinds = new Set(tempos.map((slot) => JSON.stringify(slot.value)));
  if (kinds.size > 1) {
    issues.push(blocking('tempo', `The tempo is asked for more than one way (${quote(tempos.map((slot) => slot.words))}); pick one.`));
  } else if (tempos.length > 0) {
    tempo = tempos[0].value;
    if ('explicit' in tempo) {
      const t = tempo.explicit;
      assumptions.push(
        `Tempo "${tempos[0].words}" read as ${t.eccentric} s lowering, ${t.pauseStretched} s at the bottom, ` +
          `${t.concentric} s lifting, ${t.pauseContracted} s at the top.`,
      );
    } else {
      assumptions.push(`"${tempos[0].words}" read as the ${tempo.profile} tempo profile.`);
    }
  } else {
    assumptions.push("The family's own tempo.");
  }
  return { load, tempo };
}

/** The one grip the words ask for, or an issue. */
function interpretGrip(
  slots: PromptSlots,
  implied: { grip: IntentGrip; words: string } | null,
  fallback: IntentGrip,
  assumptions: string[],
  issues: IntentIssue[],
): IntentGrip {
  const asked = [...slots.grips, ...(implied ? [{ value: implied.grip, words: implied.words }] : [])];
  const grips = distinct(asked);
  if (grips.length > 1) {
    issues.push(
      blocking(
        'grip',
        `The grip is contradictory: ${asked.map((slot) => `"${slot.words}" means ${slot.value}`).join(', ')}. Say which grip.`,
      ),
    );
    return fallback;
  }
  if (grips.length === 1) return grips[0];
  assumptions.push(`A ${fallback} grip, the family's default.`);
  return fallback;
}

/** The one support the words ask for, or an issue. */
function interpretSupport(
  slots: PromptSlots,
  allowed: IntentSupport[],
  family: string,
  assumptions: string[],
  issues: IntentIssue[],
): IntentSupport {
  let supports = distinct(slots.supports);
  // "A seated incline curl" is an incline curl: the body sits on the incline
  // bench's seat either way.
  if (supports.includes('incline')) supports = ['incline'];
  if (supports.length > 1) {
    issues.push(blocking('support', `The body is asked to be ${supports.join(' and ')} at once; say which.`));
    return allowed[0];
  }
  if (supports.length === 0) {
    assumptions.push(`${allowed[0][0].toUpperCase()}${allowed[0].slice(1)}, the family's default support.`);
    return allowed[0];
  }
  if (!allowed.includes(supports[0])) {
    issues.push(
      blocking(
        'support',
        `A ${supports[0]} ${family} is not certified; the family supports ${allowed.join(' and ')}.`,
      ),
    );
  }
  return supports[0];
}

/** Named sub-variants a family does not build, with the reason. */
function unsupportedNames(slots: PromptSlots, table: [RegExp, string][], issues: IntentIssue[]) {
  for (const [pattern, reason] of table) {
    const match = slots.text.match(pattern);
    if (match) issues.push(blocking('variant', `"${match[0]}": ${reason}`));
  }
}

const slug = (text: string) =>
  text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_|_$/g, '');

const formatLoad = (kg: number) => `${Number.isInteger(kg) ? kg : kg.toFixed(1)} kg`;

const tempoWords = (intent: ExerciseIntent) =>
  'explicit' in intent.tempo
    ? 'at the requested tempo'
    : intent.tempo.profile === 'family'
      ? ''
      : `at a ${intent.tempo.profile} tempo`;

/** Identity for a generated candidate: prefixed so it can never collide with the library. */
function identity(title: string, intent: ExerciseIntent) {
  const name = `${title} (${formatLoad(intent.load)})`;
  const tempo =
    'explicit' in intent.tempo
      ? `tempo_${[intent.tempo.explicit.eccentric, intent.tempo.explicit.pauseStretched, intent.tempo.explicit.concentric, intent.tempo.explicit.pauseContracted].join('_')}`
      : intent.tempo.profile === 'family'
        ? ''
        : intent.tempo.profile;
  return {
    id: slug(['generated', title, formatLoad(intent.load), tempo].join(' ')),
    name,
    clipName: `generated_${slug(title)}`,
  };
}

// ---------------------------------------------------------------------------
// Curl
// ---------------------------------------------------------------------------

/**
 * What the grip changes beyond the forearm's rotation, which the family already
 * derives. The library's hammer and reverse curls say the same in their own
 * definitions; here it is keyed by grip so any curl with that grip gets it.
 */
const CURL_GRIP: Record<IntentGrip, { title: string; muscles?: Partial<MuscleInvolvement>; errors: CommonError[]; palms: string }> = {
  supinated: { title: 'Dumbbell Curl', errors: [], palms: 'palms up' },
  neutral: {
    title: 'Dumbbell Hammer Curl',
    palms: 'palms facing each other',
    muscles: { primary: ['biceps', 'forearm_flexors'], secondary: ['deltoid_anterior'] },
    errors: [
      {
        id: 'rolling_to_supination',
        label: 'Rolling the palms up',
        description: 'The forearms turn towards a normal curl as the weight rises, which hands the work back to the biceps.',
        ruleId: 'grip_held_l',
        correction: 'Keep the thumbs up and the knuckles outward for the whole repetition.',
      },
    ],
  },
  pronated: {
    title: 'Dumbbell Reverse Curl',
    palms: 'palms down',
    muscles: { primary: ['biceps', 'forearm_extensors'], secondary: ['forearm_flexors', 'deltoid_anterior'] },
    errors: [
      {
        id: 'rolling_to_supination',
        label: 'Letting the palms turn up',
        description: 'The forearms rotate back towards a normal curl as the weight rises, handing the work back to the biceps.',
        ruleId: 'grip_held_l',
        correction: 'Keep the knuckles up and the palms facing the floor for the whole repetition.',
      },
    ],
  },
};

/** The incline bench's default back angle, degrees from horizontal. */
const INCLINE_BENCH_ANGLE = 45;

/**
 * Angles certified for the incline curl: each has generated a candidate that
 * passed all 13 checks on the production character
 * (`HomeGymPT_Male_CORNER_FINAL_SHORTS.glb`), pad contact included — reached
 * within 3 mm, pressed no more than 15 mm. See `generate.test.ts` for the
 * measurements behind each. The bench and the curl family derive any angle
 * geometrically (`equipment/geometry.ts`'s `inclineBackPad`,
 * `exercises/families/curl.ts`'s `inclineGeometry`), so nothing here is
 * hand-tuned per angle — but the bench's fixed frame (the posts that hold the
 * pad up, which do not move with the angle) was only ever built to clear a
 * body reclined to 45°, so not every angle the geometry can describe is one
 * the physical bench can actually hold:
 *
 * - **30°** (a shallower pad, so a more reclined body, pitch -60°): the back
 *   sits 13.17 mm short of the pad and the trunk passes 36.31 mm through the
 *   bench's rear support post. Refused.
 * - **60°** (a steeper pad, so a more upright body, pitch -30°): the back
 *   presses 29.64 mm into the pad, twice the 15 mm a pad may compress.
 *   Refused.
 *
 * Neither failure has a lever: both levers this family has are for the
 * dumbbell's clearance from the thighs, not the trunk's from the bench frame
 * or the pad's own compression, and no limit was loosened to try to pass them
 * anyway. Widening this set means moving the frame posts so they clear a
 * wider range of recline, which is a bench-geometry change, not a curl one.
 */
const CERTIFIED_INCLINE_ANGLES: readonly number[] = [45];

/** The curl family's own defaults, for the levers' starting points. */
const CURL_DEFAULTS = { elbow: { start: 16, peak: 126 }, abduction: { standing: { start: 3, peak: 4 }, incline: { start: 20, peak: 18 } } };

const curl: GeneratorFamily<CurlVariant> = {
  id: 'curl',
  label: 'Curl',
  builder: 'curlFamily',
  detect: /\bcurls?\b/,
  library: ['dumbbell_bicep_curl', 'dumbbell_hammer_curl', 'dumbbell_reverse_curl', 'incline_dumbbell_curl'],

  interpret(slots, prompt) {
    const assumptions: string[] = [];
    const issues: IntentIssue[] = [];
    unsupportedNames(
      slots,
      [
        [/\bpreacher\b/, 'a preacher curl needs a preacher pad, which the equipment library does not have yet.'],
        [/\bconcentration\b/, 'a concentration curl is single-arm and braced on the thigh; not certified.'],
        [/\bspider\b/, 'a spider curl lies chest-down on the incline; not certified.'],
        [/\bzottman\b/, 'a Zottman curl turns the grip mid-repetition; the family holds one grip throughout.'],
        [/\bdrag\b/, 'a drag curl moves the elbows back; the family keeps them under the shoulders.'],
        [/\bcross[-\s]body\b/, 'a cross-body curl is single-arm and diagonal; not certified.'],
      ],
      issues,
    );
    const implied = /\bhammer\b/.test(slots.text) && !/\bhammer[-\s]grip\b/.test(slots.text)
      ? { grip: 'neutral' as const, words: 'hammer' }
      : /\breverse\b/.test(slots.text)
        ? { grip: 'pronated' as const, words: 'reverse' }
        : null;
    const grip = interpretGrip(slots, implied, 'supinated', assumptions, issues);
    const support = interpretSupport(slots, ['standing', 'incline'], 'curl', assumptions, issues);

    let benchAngle: number | undefined;
    const angles = distinct(slots.angles);
    if (support === 'incline') {
      benchAngle = angles[0] ?? INCLINE_BENCH_ANGLE;
      if (angles.length > 1) {
        issues.push(blocking('angle', `Several bench angles were given (${quote(slots.angles.map((slot) => slot.words))}).`));
      } else if (angles.length === 0) {
        assumptions.push(`The incline bench at ${INCLINE_BENCH_ANGLE}°, the family's default angle.`);
      } else if (!CERTIFIED_INCLINE_ANGLES.includes(benchAngle)) {
        const certified = CERTIFIED_INCLINE_ANGLES.map((value) => `${value}°`);
        const list = `${certified.slice(0, -1).join(', ')}${certified.length > 1 ? ' and ' : ''}${certified.at(-1)}`;
        const has = certified.length > 1 ? 'have' : 'has';
        issues.push(
          blocking(
            'angle',
            `A ${benchAngle}° incline is not certified: the bench adjusts, but only ${list} ${has} passed every check ` +
              'on the production character (30° and 60° were tried and refused: the back does not reach the pad at ' +
              "30°, and presses too far into it at 60° — the bench's fixed frame was only ever built to clear a body " +
              'reclined to 45°). An angle is certified only once a generated candidate there passes all 13 checks, ' +
              'pad contact included, without loosening any limit.',
          ),
        );
      }
    } else if (angles.length > 0) {
      issues.push(blocking('angle', `${quote(slots.angles.map((slot) => slot.words))} has nothing to apply to in a standing curl.`));
    }

    const { load, tempo } = interpretCommon(slots, 'curl', 10, assumptions, issues);
    return {
      intent: { prompt, family: 'curl', equipment: 'dumbbell', execution: 'bilateral', grip, support, benchAngle, load, tempo },
      assumptions,
      issues,
    };
  },

  variant(intent) {
    const grip = intent.grip;
    const known = CURL_GRIP[grip];
    const incline = intent.support === 'incline';
    const benchAngle = intent.benchAngle ?? INCLINE_BENCH_ANGLE;
    // The angle is part of the title, not just the description: two incline
    // curls at different angles are different candidates and must not share
    // an id, a name or a clip name.
    const title = `${incline ? `Incline (${benchAngle}°)` : 'Standing'} ${known.title}`;
    const tempo = tempoOf(intent);
    return {
      ...identity(title, intent),
      description:
        `Generated from "${intent.prompt.trim()}". ${incline ? `A curl lying back on a ${benchAngle}° incline bench, the arms hanging behind the body` : 'A standing two-arm curl'} ` +
        `with a ${grip} grip (${known.palms}), ${formatLoad(intent.load)} in each hand${tempoWords(intent) ? `, ${tempoWords(intent)}` : ''}.`,
      grip,
      support: incline ? 'incline' : 'standing',
      mass: intent.load,
      ...(incline ? { benchAngle } : {}),
      ...(tempo ? { tempo } : {}),
      ...(known.muscles ? { muscles: known.muscles } : {}),
      ...(known.errors.length ? { commonErrors: known.errors } : {}),
    };
  },

  build: curlFamily,

  reference(intent) {
    if (intent.support === 'incline') return 'incline_dumbbell_curl';
    return { supinated: 'dumbbell_bicep_curl', neutral: 'dumbbell_hammer_curl', pronated: 'dumbbell_reverse_curl' }[intent.grip];
  },

  levers: [
    {
      id: 'curl.elbow_bottom',
      label: 'Elbow bend at the bottom',
      resolves: ['equipmentClearance'],
      read: (variant) => (variant.elbow ?? CURL_DEFAULTS.elbow).start,
      write: (variant, value) => ({ ...variant, elbow: { ...(variant.elbow ?? CURL_DEFAULTS.elbow), start: value } }),
      step: 1,
      limit: 30,
      why:
        "The curl family's own lever for a hanging dumbbell's thigh clearance: bending the elbow at the bottom carries the " +
        'dumbbell forward of the thigh without tilting the upper arm. Bounded at 30°, short of cutting the range.',
    },
    {
      id: 'curl.abduction',
      label: 'Upper arms out from the sides',
      resolves: ['equipmentClearance', 'armTrunk'],
      read: (variant) => (variant.abduction ?? CURL_DEFAULTS.abduction[variant.support === 'incline' ? 'incline' : 'standing']).start,
      write: (variant, value) => {
        const base = variant.abduction ?? CURL_DEFAULTS.abduction[variant.support === 'incline' ? 'incline' : 'standing'];
        return { ...variant, abduction: { start: value, peak: base.peak + (value - base.start) } };
      },
      step: 1,
      limit: 15,
      why:
        'Holding the arms a little wider moves the dumbbells and the upper arms away from the thighs and the chest. ' +
        "The family's upper_arm_clear and hands_shoulder_width rules still apply, so it cannot widen into a shrug.",
    },
  ],
};

// ---------------------------------------------------------------------------
// Overhead press
// ---------------------------------------------------------------------------

const overheadPress: GeneratorFamily<PressVariant> = {
  id: 'overhead_press',
  label: 'Overhead press',
  builder: 'pressFamily',
  detect: /\b(?:shoulder|overhead|military)\s+press(?:es)?\b|\bohp\b/,
  library: ['dumbbell_shoulder_press', 'seated_dumbbell_shoulder_press'],

  interpret(slots, prompt) {
    const assumptions: string[] = [];
    const issues: IntentIssue[] = [];
    unsupportedNames(
      slots,
      [
        [/\barnold\b/, 'an Arnold press rotates the grip through the press; the family holds one grip.'],
        [/\bpush[-\s]press\b/, 'a push press drives with the legs; the press family keeps the lower body still.'],
        [/\bz[-\s]press\b/, 'a Z press sits on the floor with the legs out; not certified.'],
      ],
      issues,
    );
    const grip = interpretGrip(slots, null, 'pronated', assumptions, issues);
    if (grip === 'neutral') {
      issues.push(
        blocking(
          'grip',
          'A neutral-grip overhead press is not certified. It was built and withdrawn: reaching a true palms-facing ' +
            'position overhead needs 80–85° of forearm supination, the joint limit itself — a modelling gap, not a tuning ' +
            'problem (see families/press.test.ts). Ask for the pronated press, or wait for the forearm model to change.',
        ),
      );
    } else if (grip === 'supinated') {
      issues.push(blocking('grip', 'A palms-up overhead press is not certified; the family presses pronated.'));
    }
    const support = interpretSupport(slots, ['standing', 'seated'], 'overhead press', assumptions, issues);
    if (slots.angles.length > 0) {
      issues.push(blocking('angle', `${quote(slots.angles.map((slot) => slot.words))}: the press family has no adjustable angle.`));
    }
    const { load, tempo } = interpretCommon(slots, 'overhead press', 12, assumptions, issues);
    return {
      intent: { prompt, family: 'overhead_press', equipment: 'dumbbell', execution: 'bilateral', grip, support, load, tempo },
      assumptions,
      issues,
    };
  },

  variant(intent) {
    const seated = intent.support === 'seated';
    const title = `${seated ? 'Seated' : 'Standing'} Dumbbell Shoulder Press`;
    const tempo = tempoOf(intent);
    return {
      ...identity(title, intent),
      description:
        `Generated from "${intent.prompt.trim()}". An overhead press ${seated ? 'sitting on the end of a flat bench' : 'standing'}, ` +
        `palms forward, ${formatLoad(intent.load)} in each hand${tempoWords(intent) ? `, ${tempoWords(intent)}` : ''}.`,
      grip: 'pronated',
      support: seated ? 'seated' : 'standing',
      mass: intent.load,
      ...(tempo ? { tempo } : {}),
    };
  },

  build: pressFamily,

  reference: (intent) => (intent.support === 'seated' ? 'seated_dumbbell_shoulder_press' : 'dumbbell_shoulder_press'),

  // No lever yet: nothing a certified press intent can ask for has needed one.
  // One is added when a measured failure shows which parameter resolves it.
  levers: [],
};

/** Families certified for generation, in detection order. */
export const GENERATOR_FAMILIES: GeneratorFamily[] = [
  curl as unknown as GeneratorFamily,
  overheadPress as unknown as GeneratorFamily,
];

export const generatorFamily = (id: GeneratorFamilyId): GeneratorFamily =>
  GENERATOR_FAMILIES.find((family) => family.id === id)!;
