import type { CommonError, ExerciseDefinition, MuscleInvolvement } from '../exercises/types';
import { curlFamily } from '../exercises/families/curl';
import type { CurlVariant } from '../exercises/families/curl';
import { pressFamily } from '../exercises/families/press';
import type { PressVariant } from '../exercises/families/press';
import { squatFamily } from '../exercises/families/squat';
import type { SquatVariant } from '../exercises/families/squat';
import { lungeFamily } from '../exercises/families/lunge';
import type { LungeVariant } from '../exercises/families/lunge';
import { hingeFamily } from '../exercises/families/hinge';
import type { HingeVariant } from '../exercises/families/hinge';
import { rowFamily } from '../exercises/families/row';
import type { RowVariant } from '../exercises/families/row';
import { verticalPullFamily } from '../exercises/families/verticalPull';
import type { VerticalPullVariant } from '../exercises/families/verticalPull';
import { extensionFamily } from '../exercises/families/extension';
import type { ExtensionVariant } from '../exercises/families/extension';
import type { ExerciseIntent, GeneratorFamilyId, IntentGrip, IntentImplement, IntentIssue, IntentSupport } from './intent';
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
 * The slots every family reads the same way: implement, execution, load and
 * tempo. Grip and support differ by family and are left to it.
 *
 * `implement` says what the family holds. A dumbbell family reads a load and
 * refuses any other equipment; a bodyweight family holds nothing yet, so any
 * load or equipment named is refused instead of silently dropped — the family
 * cannot really carry it.
 */
function interpretCommon(
  slots: PromptSlots,
  family: string,
  implement: IntentImplement,
  defaultLoad: number,
  assumptions: string[],
  issues: IntentIssue[],
): { load: number; tempo: ExerciseIntent['tempo'] } {
  let load = defaultLoad;
  if (implement === 'dumbbell') {
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

    const loads = distinct(slots.loads);
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
  } else if (implement === 'cable') {
    const others = slots.equipment.filter((slot) => slot.value !== 'cable');
    if (others.length > 0) {
      issues.push(
        blocking(
          'equipment',
          `${quote(others.map((slot) => slot.words))}: the ${family} family is certified on the cable station only.`,
        ),
      );
    } else if (slots.equipment.length === 0) {
      assumptions.push('Cable station with the family\'s straight bar attachment.');
    }
    if (slots.loads.length > 0) {
      issues.push(
        blocking(
          'load',
          `${quote(slots.loads.map((slot) => slot.words))}: cable-stack resistance is not a family parameter yet, so a requested stack load cannot be represented.`,
        ),
      );
    }
    load = 0;
  } else {
    const others = slots.equipment.filter((slot) => slot.value !== 'bodyweight');
    if (others.length > 0) {
      issues.push(
        blocking(
          'equipment',
          `${quote(others.map((slot) => slot.words))}: the ${family} family is bodyweight only; it does not hold any load yet.`,
        ),
      );
    } else {
      assumptions.push('Bodyweight — no hand-held load, which is all this family is certified with.');
    }
    if (slots.loads.length > 0) {
      issues.push(
        blocking(
          'load',
          `${quote(slots.loads.map((slot) => slot.words))}: the ${family} family is bodyweight only; it does not hold any load yet.`,
        ),
      );
    }
    load = 0;
  }

  if (slots.execution.length > 0) {
    issues.push(
      blocking(
        'execution',
        `${quote(slots.execution.map((slot) => slot.words))}: only the plain, even-sided movement is certified. ` +
          'Alternating and single-side work change the whole repetition, so it is not substituted silently — ' +
          'ask for the plain version to proceed.',
      ),
    );
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
  const loadWords = intent.equipment === 'dumbbell' ? formatLoad(intent.load) : '';
  const name = loadWords ? `${title} (${loadWords})` : title;
  const tempo =
    'explicit' in intent.tempo
      ? `tempo_${[intent.tempo.explicit.eccentric, intent.tempo.explicit.pauseStretched, intent.tempo.explicit.concentric, intent.tempo.explicit.pauseContracted].join('_')}`
      : intent.tempo.profile === 'family'
        ? ''
        : intent.tempo.profile;
  return {
    id: slug(['generated', title, loadWords, tempo].join(' ')),
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

    const { load, tempo } = interpretCommon(slots, 'curl', 'dumbbell', 10, assumptions, issues);
    return {
      intent: { prompt, family: 'curl', equipment: 'dumbbell', execution: 'bilateral', grip, support, benchAngle, load, tempo },
      assumptions,
      issues,
    };
  },

  variant(intent) {
    const grip = intent.grip!;
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
    return { supinated: 'dumbbell_bicep_curl', neutral: 'dumbbell_hammer_curl', pronated: 'dumbbell_reverse_curl' }[intent.grip!];
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
    const { load, tempo } = interpretCommon(slots, 'overhead press', 'dumbbell', 12, assumptions, issues);
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

// ---------------------------------------------------------------------------
// Squat
// ---------------------------------------------------------------------------

/**
 * The squat family builds one certified variant: the bodyweight air squat. A
 * squat's detect excludes "split squat", which is the lunge family's
 * reference variant — without the exclusion both families would match the
 * same words and the request would be refused as ambiguous.
 */
const squat: GeneratorFamily<SquatVariant> = {
  id: 'squat',
  label: 'Squat',
  builder: 'squatFamily',
  detect: /(?<!split\s)squats?\b/,
  library: ['air_squat'],

  interpret(slots, prompt) {
    const assumptions: string[] = [];
    const issues: IntentIssue[] = [];
    unsupportedNames(
      slots,
      [
        [/\bgoblet\b/, 'a goblet squat holds a dumbbell or kettlebell at the chest; the squat family is bodyweight only, not certified for generation yet.'],
        [/\bfront\b/, 'a front squat racks a barbell across the shoulders; not certified.'],
        [/\bback\b/, 'a back squat racks a barbell across the shoulders; not certified.'],
        [/\boverhead\b/, 'an overhead squat holds a barbell locked out overhead; not certified.'],
        [/\bzercher\b/, 'a Zercher squat carries the bar in the crooks of the elbows; not certified.'],
        [/\bbox\b/, 'a box squat sits onto a box at the bottom; the family squats to depth without one, not certified.'],
        [/\bpistol\b/, 'a pistol squat is single-leg; the family is certified two-legged only.'],
        [/\bjump(?:ing)?\b/, 'a jump squat is plyometric; the family holds a controlled tempo throughout.'],
        [/\bsumo\b/, 'a sumo squat widens the stance beyond what the family is certified at.'],
        [/\bhack\b/, 'a hack squat needs a machine the equipment library does not have.'],
        [/\bbulgarian\b/, 'a Bulgarian split squat rests the back foot on a bench; that is not certified either.'],
      ],
      issues,
    );

    const { tempo } = interpretCommon(slots, 'squat', 'bodyweight', 0, assumptions, issues);
    return {
      intent: { prompt, family: 'squat', equipment: 'bodyweight', execution: 'bilateral', support: 'standing', load: 0, tempo },
      assumptions,
      issues,
    };
  },

  variant(intent) {
    const tempo = tempoOf(intent);
    return {
      ...identity('Bodyweight Squat', intent),
      description:
        `Generated from "${intent.prompt.trim()}". A bodyweight squat to depth with a shoulder-width stance, ` +
        `the feet planted and the hips and knees bending together${tempoWords(intent) ? `, ${tempoWords(intent)}` : ''}.`,
      ...(tempo ? { tempo } : {}),
    };
  },

  build: squatFamily,

  reference: () => 'air_squat',

  // No lever yet: the family's one certified variant passes without one.
  // One is added when a measured failure shows which parameter resolves it.
  levers: [],
};

// ---------------------------------------------------------------------------
// Lunge
// ---------------------------------------------------------------------------

/**
 * The lunge family builds three certified variants: the static split squat
 * (no step), the forward lunge (front foot steps) and the reverse lunge
 * (back foot steps). `detect` also matches "split squat" — the family's own
 * static reference variant — alongside "lunge".
 */
const lunge: GeneratorFamily<LungeVariant> = {
  id: 'lunge',
  label: 'Lunge',
  builder: 'lungeFamily',
  detect: /\blunges?\b|\bsplit\s+squats?\b/,
  library: ['split_squat', 'forward_lunge', 'reverse_lunge'],

  interpret(slots, prompt) {
    const assumptions: string[] = [];
    const issues: IntentIssue[] = [];
    unsupportedNames(
      slots,
      [
        [/\bwalking\b/, 'a walking lunge steps continuously without returning to standing; not certified.'],
        [/\blateral\b|\bside\b/, 'a lateral lunge steps sideways, a different plane the family does not build.'],
        [/\bcurtsy\b/, 'a curtsy lunge steps behind and across the body; not certified.'],
        [/\bjump(?:ing)?\b/, 'a jumping lunge is plyometric; the family holds a controlled tempo throughout.'],
        [/\bbulgarian\b/, 'a Bulgarian split squat rests the back foot on a bench; not certified.'],
        [/\bdiagonal\b/, 'a diagonal lunge steps off the straight line forward and back; not certified.'],
        [/\btwist(?:ing)?\b|\brotat/, 'a lunge with a twist adds trunk rotation the family does not build.'],
      ],
      issues,
    );

    const forward = /\bforward\b/.test(slots.text);
    const back = /\b(?:reverse|back(?:ward)?)\b/.test(slots.text);
    const split = /\bsplit\s+squats?\b/.test(slots.text) || /\bstatic\b|\bstationary\b/.test(slots.text);

    let step: 'forward' | 'back' | undefined;
    if (forward && back) {
      issues.push(blocking('variant', 'The lunge is asked to step both forward and back; say which.'));
    } else if (split && (forward || back)) {
      issues.push(
        blocking('variant', 'A split squat does not step; ask for the split squat, the forward lunge or the reverse lunge, not more than one.'),
      );
    } else if (split) {
      assumptions.push('The split squat: both feet stay put and the body sinks straight down between them.');
    } else if (forward) {
      step = 'forward';
    } else if (back) {
      step = 'back';
    } else {
      step = 'forward';
      assumptions.push('No step direction was named; read as the forward lunge, stepping in from standing.');
    }

    const { tempo } = interpretCommon(slots, 'lunge', 'bodyweight', 0, assumptions, issues);
    return {
      intent: { prompt, family: 'lunge', equipment: 'bodyweight', execution: 'bilateral', support: 'standing', step, load: 0, tempo },
      assumptions,
      issues,
    };
  },

  variant(intent) {
    const title = intent.step === 'forward' ? 'Forward Lunge' : intent.step === 'back' ? 'Reverse Lunge' : 'Bodyweight Split Squat';
    const shape =
      intent.step === 'forward'
        ? 'from standing, one long step forward, lowering until the back knee is just above the floor, then a push back to standing'
        : intent.step === 'back'
          ? 'from standing, one long step back, lowering until the back knee is just above the floor, then a drive back to standing'
          : 'a static split stance, sinking straight down until the back knee is just above the floor, then driving back up';
    const tempo = tempoOf(intent);
    return {
      ...identity(title, intent),
      description: `Generated from "${intent.prompt.trim()}". A lunge: ${shape}${tempoWords(intent) ? `, ${tempoWords(intent)}` : ''}.`,
      ...(intent.step ? { step: intent.step } : {}),
      ...(tempo ? { tempo } : {}),
    };
  },

  build: lungeFamily,

  reference: (intent) => (intent.step === 'forward' ? 'forward_lunge' : intent.step === 'back' ? 'reverse_lunge' : 'split_squat'),

  // No lever yet: every certified variant passes without one.
  // One is added when a measured failure shows which parameter resolves it.
  levers: [],
};

// ---------------------------------------------------------------------------
// Hinge
// ---------------------------------------------------------------------------

const hinge: GeneratorFamily<HingeVariant> = {
  id: 'hinge',
  label: 'Hinge',
  builder: 'hingeFamily',
  detect: /\b(?:romanian\s+)?deadlifts?\b|\brdls?\b|\bhip\s+hinges?\b|\bgood\s?mornings?\b/,

  library: ['dumbbell_romanian_deadlift'],

  interpret(slots, prompt) {
    const assumptions: string[] = [];
    const issues: IntentIssue[] = [];

    unsupportedNames(
      slots,
      [
        [/\bsumo\b/, 'a sumo deadlift uses a much wider stance and different hip/knee balance; the hinge family is not certified for it.'],
        [/\bconventional\b/, 'a conventional deadlift starts from the floor with substantially more knee flexion; the current hinge family certifies the Romanian deadlift only.'],
        [/\bstiff[-\s]?leg(?:ged)?\b/, 'a stiff-leg deadlift deliberately changes the knee angle from the certified Romanian deadlift.'],
        [/\bsingle[-\s]?leg\b|\bone[-\s]?leg\b/, 'a single-leg RDL is unilateral and requires balance/contact behaviour the family does not build yet.'],
        [/\bgood\s?mornings?\b/, 'a good morning carries load across the shoulders rather than in the hands; that equipment/support pattern is not certified.'],
        [/\bbarbell\b/, 'a barbell RDL uses two hands on one rigid bar; the certified hinge family currently uses paired dumbbells.'],
        [/\bkettle-?bells?\b|\bkbs?\b/, 'a kettlebell hinge is not certified; the current family uses paired dumbbells.'],
        [/\bmixed\s+grip\b/, 'a mixed grip is asymmetric; only the even two-hand dumbbell hinge is certified.'],
      ],
      issues,
    );

    const romanian = /\bromanian\b|\brdls?\b|\bhip\s+hinges?\b/.test(slots.text);
    const namedNonRomanian = /\b(?:conventional|sumo|stiff[-\s]?leg(?:ged)?|single[-\s]?leg|one[-\s]?leg)\b/.test(slots.text);
    if (/\bdeadlifts?\b/.test(slots.text) && !romanian && !namedNonRomanian) {
      issues.push(
        blocking(
          'variant',
          'A plain "deadlift" normally means the conventional floor deadlift. The certified hinge family currently builds only the dumbbell Romanian deadlift; ask for an RDL or Romanian deadlift explicitly.',
        ),
      );
    }

    const grip = interpretGrip(slots, null, 'pronated', assumptions, issues);
    if (grip !== 'pronated') {
      issues.push(
        blocking(
          'grip',
          'The certified dumbbell Romanian deadlift uses the hinge family\'s pronated hand orientation; a ' + grip + ' grip is not certified.',
        ),
      );
    }

    const support = interpretSupport(slots, ['standing'], 'hinge', assumptions, issues);
    if (slots.angles.length > 0) {
      issues.push(blocking('angle', quote(slots.angles.map((slot) => slot.words)) + ': the hinge family has no adjustable bench/body angle input.'));
    }

    const { load, tempo } = interpretCommon(slots, 'hinge', 'dumbbell', 16, assumptions, issues);
    return {
      intent: {
        prompt,
        family: 'hinge',
        equipment: 'dumbbell',
        execution: 'bilateral',
        grip,
        support,
        load,
        tempo,
      },
      assumptions,
      issues,
    };
  },

  variant(intent) {
    const tempo = tempoOf(intent);
    return {
      ...identity('Dumbbell Romanian Deadlift', intent),
      description:
        'Generated from "' + intent.prompt.trim() + '". A standing dumbbell Romanian deadlift: hips travel back, knees stay soft, ' +
        'the spine stays neutral and the dumbbells remain close to the legs, ' + formatLoad(intent.load) + ' in each hand' +
        (tempoWords(intent) ? ', ' + tempoWords(intent) : '') + '.',
      mass: intent.load,
      ...(tempo ? { tempo } : {}),
    };
  },

  build: hingeFamily,

  reference: () => 'dumbbell_romanian_deadlift',

  // The accepted reference variant already passes the current mechanical/body
  // checks. Add a correction lever only after a generated hinge produces a
  // measured failure and the family exposes a safe parameter that resolves it.
  levers: [],
};

// ---------------------------------------------------------------------------
// Horizontal pull / bent-over row
// ---------------------------------------------------------------------------

const row: GeneratorFamily<RowVariant> = {
  id: 'row',
  label: 'Bent-over row',
  builder: 'rowFamily',
  detect: /\brows?\b/,

  library: ['dumbbell_bent_over_row'],

  interpret(slots, prompt) {
    const assumptions: string[] = [];
    const issues: IntentIssue[] = [];

    unsupportedNames(
      slots,
      [
        [/\bupright\b/, 'an upright row is a shoulder-dominant vertical pull; the bent-over row family does not build it.'],
        [/\bchest[-\s]?supported\b|\bsupported\s+row\b/, 'a chest-supported row needs a bench/support relationship the current row family does not build.'],
        [/\b(?:one|single)[-\s]arm\b|\bunilateral\b/, 'a one-arm row is unilateral and usually braced; the certified row is an even two-arm movement.'],
        [/\brenegade\b/, 'a renegade row is a plank/floor-support movement; not certified by the bent-over row family.'],
        [/\bseated\b|\bcable\b/, 'a seated cable row uses a cable and seated support; the current row family uses paired dumbbells from a standing hinge.'],
        [/\bbarbell\b|\bt[-\s]?bar\b/, 'a rigid bar row uses different two-hand equipment; the certified row uses paired dumbbells.'],
      ],
      issues,
    );

    const bentOver = /\bbent[-\s]?over\b/.test(slots.text);
    if (!bentOver) {
      issues.push(
        blocking(
          'variant',
          'The current certified row is specifically the two-arm dumbbell bent-over row. Ask for a bent-over row explicitly so another row style is not guessed.',
        ),
      );
    }

    const grip = interpretGrip(slots, null, 'neutral', assumptions, issues);
    if (grip !== 'neutral') {
      issues.push(
        blocking(
          'grip',
          'The certified bent-over row uses the row family\'s neutral palms-facing grip; a ' + grip + ' grip is not certified.',
        ),
      );
    }

    const support = interpretSupport(slots, ['standing'], 'bent-over row', assumptions, issues);
    if (slots.angles.length > 0) {
      issues.push(
        blocking(
          'angle',
          quote(slots.angles.map((slot) => slot.words)) +
            ': the row family uses its certified hinge posture and does not expose an arbitrary torso angle.',
        ),
      );
    }

    const { load, tempo } = interpretCommon(slots, 'bent-over row', 'dumbbell', 14, assumptions, issues);
    return {
      intent: {
        prompt,
        family: 'row',
        equipment: 'dumbbell',
        execution: 'bilateral',
        grip,
        support,
        load,
        tempo,
      },
      assumptions,
      issues,
    };
  },

  variant(intent) {
    const tempo = tempoOf(intent);
    return {
      ...identity('Dumbbell Bent-Over Row', intent),
      description:
        'Generated from "' +
        intent.prompt.trim() +
        '". A two-arm dumbbell bent-over row from the family\'s fixed hinge posture, ' +
        'palms facing in, elbows driving back past the ribs, ' +
        formatLoad(intent.load) +
        ' in each hand' +
        (tempoWords(intent) ? ', ' + tempoWords(intent) : '') +
        '.',
      mass: intent.load,
      ...(tempo ? { tempo } : {}),
    };
  },

  build: rowFamily,

  reference: () => 'dumbbell_bent_over_row',

  // The accepted reference row passes the shared validation gates. Add a
  // correction lever only after a measured generated-row failure proves which
  // row-family parameter should safely move.
  levers: [],
};

// ---------------------------------------------------------------------------
// Vertical pull / pull-up
// ---------------------------------------------------------------------------

const verticalPull: GeneratorFamily<VerticalPullVariant> = {
  id: 'vertical_pull',
  label: 'Pull-up',
  builder: 'verticalPullFamily',
  detect: /\bpull[-\s]?ups?\b/,

  library: ['pull_up'],

  interpret(slots, prompt) {
    const assumptions: string[] = [];
    const issues: IntentIssue[] = [];

    unsupportedNames(
      slots,
      [
        [/\bkipping\b|\bkip\b/, 'the certified pull-up is strict; kipping changes the whole-body movement.'],
        [/\bassisted\b/, 'an assisted pull-up needs a band, machine or counterweight relationship that is not certified.'],
        [/\bweighted\b/, 'a weighted pull-up needs an added-load attachment model; the certified family is bodyweight only.'],
        [/\bwide[-\s]?grip\b|\bclose[-\s]?grip\b|\bnarrow[-\s]?grip\b/, 'the current family owns one fixed grip width, just wider than the shoulders.'],
        [/\bbehind[-\s](?:the[-\s])?neck\b/, 'a behind-the-neck pull-up is a different shoulder path and is not certified.'],
      ],
      issues,
    );

    const grip = interpretGrip(slots, null, 'pronated', assumptions, issues);
    if (grip !== 'pronated') {
      issues.push(
        blocking(
          'grip',
          'The certified pull-up uses a pronated overhand grip. Chin-up/underhand and neutral-grip variants are not certified yet.',
        ),
      );
    }

    const support = interpretSupport(slots, ['hanging'], 'pull-up', assumptions, issues);
    if (slots.angles.length > 0) {
      issues.push(blocking('angle', quote(slots.angles.map((slot) => slot.words)) + ': the pull-up family has no angle input.'));
    }

    const { load, tempo } = interpretCommon(slots, 'pull-up', 'bodyweight', 0, assumptions, issues);
    return {
      intent: {
        prompt,
        family: 'vertical_pull',
        equipment: 'bodyweight',
        execution: 'bilateral',
        grip,
        support,
        load,
        tempo,
      },
      assumptions,
      issues,
    };
  },

  variant(intent) {
    const tempo = tempoOf(intent);
    return {
      ...identity('Pull-Up', intent),
      description:
        'Generated from "' +
        intent.prompt.trim() +
        '". A strict bodyweight pull-up from a dead hang on the fixed rack bar, using the certified pronated grip just wider than shoulder width' +
        (tempoWords(intent) ? ', ' + tempoWords(intent) : '') +
        '.',
      ...(tempo ? { tempo } : {}),
    };
  },

  build: verticalPullFamily,

  reference: () => 'pull_up',

  // The fixed grip/support geometry is already solved by the family and the
  // accepted library pull-up passes the shared gates. Add a lever only after a
  // measured generated failure identifies a safe family parameter.
  levers: [],
};

// ---------------------------------------------------------------------------
// Elbow extension / triceps
// ---------------------------------------------------------------------------

const extension: GeneratorFamily<ExtensionVariant> = {
  id: 'extension',
  label: 'Triceps extension',
  builder: 'extensionFamily',
  detect: /\btriceps?\b|\bpush[-\s]?downs?\b|\boverhead\s+extensions?\b/,

  library: ['dumbbell_overhead_triceps_extension', 'cable_triceps_pushdown'],

  interpret(slots, prompt) {
    const assumptions: string[] = [];
    const issues: IntentIssue[] = [];

    unsupportedNames(
      slots,
      [
        [/\bskull\s?crushers?\b/, 'a skull crusher is a lying elbow extension with a different shoulder/support position.'],
        [/\bkickbacks?\b/, 'a triceps kickback uses a hinged torso and the upper arm held behind the body; not certified by this family adapter.'],
        [/\brope\b/, 'the cable pushdown family currently uses its straight bar attachment, not a rope.'],
        [/\breverse[-\s]?grip\b|\bunderhand\b/, 'the current cable pushdown is certified only with its pronated straight-bar grip.'],
        [/\b(?:single|one)[-\s]arm\b|\bunilateral\b/, 'single-arm triceps work is not certified; the family currently moves both arms together.'],
        [/\blying\b|\bsupine\b/, 'lying triceps extensions need a bench/support variant the current adapter does not expose.'],
      ],
      issues,
    );

    const asksPushdown = /\bpush[-\s]?downs?\b/.test(slots.text) || /\bcable\s+triceps?\b/.test(slots.text);
    const asksOverhead = /\boverhead\b/.test(slots.text);
    if (asksPushdown && asksOverhead) {
      issues.push(blocking('variant', 'The request asks for both an overhead extension and a cable pushdown; choose one.'));
    }
    if (!asksPushdown && !asksOverhead) {
      issues.push(
        blocking(
          'variant',
          'The extension family has two certified setups: an overhead dumbbell triceps extension or a cable triceps pushdown. Say which one.',
        ),
      );
    }

    const position = asksPushdown ? 'pushdown' : 'overhead';
    const expectedGrip: IntentGrip = position === 'pushdown' ? 'pronated' : 'neutral';
    const grip = interpretGrip(slots, null, expectedGrip, assumptions, issues);
    if (grip !== expectedGrip) {
      issues.push(
        blocking(
          'grip',
          position === 'pushdown'
            ? 'The certified cable pushdown uses a pronated palms-down straight-bar grip.'
            : 'The certified overhead dumbbell extension uses a neutral palms-facing grip.',
        ),
      );
    }

    const support = interpretSupport(slots, ['standing'], position === 'pushdown' ? 'cable pushdown' : 'overhead triceps extension', assumptions, issues);
    if (slots.angles.length > 0) {
      issues.push(blocking('angle', quote(slots.angles.map((slot) => slot.words)) + ': the extension family has no adjustable angle input.'));
    }

    const implement: IntentImplement = position === 'pushdown' ? 'cable' : 'dumbbell';
    const { load, tempo } = interpretCommon(
      slots,
      position === 'pushdown' ? 'cable pushdown' : 'overhead triceps extension',
      implement,
      position === 'pushdown' ? 0 : 8,
      assumptions,
      issues,
    );

    return {
      intent: {
        prompt,
        family: 'extension',
        equipment: implement,
        execution: 'bilateral',
        grip,
        support,
        extensionPosition: position,
        load,
        tempo,
      },
      assumptions,
      issues,
    };
  },

  variant(intent) {
    const position = intent.extensionPosition ?? 'overhead';
    const pushdown = position === 'pushdown';
    const tempo = tempoOf(intent);
    return {
      ...identity(pushdown ? 'Cable Triceps Pushdown' : 'Dumbbell Overhead Triceps Extension', intent),
      description: pushdown
        ? 'Generated from "' + intent.prompt.trim() + '". A standing two-arm cable triceps pushdown using the family\'s straight bar, elbows pinned at the sides' +
          (tempoWords(intent) ? ', ' + tempoWords(intent) : '') + '.'
        : 'Generated from "' + intent.prompt.trim() + '". A standing two-arm overhead triceps extension with neutral-grip dumbbells, ' +
          formatLoad(intent.load) + ' in each hand' + (tempoWords(intent) ? ', ' + tempoWords(intent) : '') + '.',
      position,
      ...(pushdown ? {} : { mass: intent.load }),
      ...(tempo ? { tempo } : {}),
    };
  },

  build: extensionFamily,

  reference(intent) {
    return intent.extensionPosition === 'pushdown'
      ? 'cable_triceps_pushdown'
      : 'dumbbell_overhead_triceps_extension';
  },

  levers: [],
};

/** Families certified for generation, in detection order. */
export const GENERATOR_FAMILIES: GeneratorFamily[] = [
  curl as unknown as GeneratorFamily,
  overheadPress as unknown as GeneratorFamily,
  squat as unknown as GeneratorFamily,
  lunge as unknown as GeneratorFamily,
  hinge as unknown as GeneratorFamily,
  row as unknown as GeneratorFamily,
  verticalPull as unknown as GeneratorFamily,
  extension as unknown as GeneratorFamily,
];

export const generatorFamily = (id: GeneratorFamilyId): GeneratorFamily =>
  GENERATOR_FAMILIES.find((family) => family.id === id)!;
