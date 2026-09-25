import { existsSync, readFileSync } from 'node:fs';
import { beforeAll, describe, expect, it } from 'vitest';
import { canonicalSkeleton } from '../rig/skeleton';
import { generateClip } from '../animation/generate';
import { retargetedCharacterSource } from '../character/retargetSource';
import type { CharacterBuild } from '../character';
import { EXERCISES, EXERCISE_BY_ID } from '../exercises/library';
import { curlFamily } from '../exercises/families/curl';
import type { CurlVariant } from '../exercises/families/curl';
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
import { horizontalPressFamily } from '../exercises/families/horizontalPress';
import type { HorizontalPressVariant } from '../exercises/families/horizontalPress';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { airSquat } from '../exercises/definitions/airSquat';
import { splitSquat } from '../exercises/definitions/splitSquat';
import { forwardLunge } from '../exercises/definitions/forwardLunge';
import { reverseLunge } from '../exercises/definitions/reverseLunge';
import { romanianDeadlift } from '../exercises/definitions/romanianDeadlift';
import { bentOverRow } from '../exercises/definitions/bentOverRow';
import { pullUp } from '../exercises/definitions/pullUp';
import { pushUp } from '../exercises/definitions/pushUp';
import type { ExerciseDefinition } from '../exercises/types';
import { generateExercise, generateExerciseAsync } from './generate';
import type { GenerationOptions } from './generate';
import { TEMPO_PROFILES } from './intent';
import { validateCandidate } from './validate';

/**
 * Prompt → intent → family → definition → clip → validation → bounded
 * correction → candidate, end to end.
 */
const rig = canonicalSkeleton;
const library = (id: string) => EXERCISE_BY_ID.get(id);
const HAMMER = 'Create a standing hammer curl with 12 kg dumbbells and controlled tempo.';
const INCLINE = 'Create an incline dumbbell curl at 45 degrees with 8 kg dumbbells.';
const PRESS = 'Create a seated dumbbell shoulder press with 10 kg dumbbells and controlled tempo.';
const SQUAT = 'Create a bodyweight squat with a slow tempo.';
const REVERSE_LUNGE = 'Create a reverse lunge with controlled tempo.';
const RDL = 'Create a dumbbell Romanian deadlift with 18 kg dumbbells and slow tempo.';
const ROW = 'Create a dumbbell bent-over row with 16 kg dumbbells and controlled tempo.';
const PULLUP = 'Create a strict pull-up with controlled tempo.';
const PUSHUP = 'Create a standard push-up with controlled tempo.';

/** Everything but what names and describes an exercise. */
const motionOf = ({ id: _id, name: _name, clipName: _clip, description: _description, ...rest }: ExerciseDefinition) => rest;

describe('generating without a character', () => {
  const options: GenerationOptions = { rig, library };

  it('builds the exercise from the family, not from a library file', () => {
    const result = generateExercise(HAMMER, options);
    expect(result.family?.id).toBe('curl');
    // The definition is exactly what the family builder makes of the variant.
    expect(result.exercise).toEqual(curlFamily(result.variant as CurlVariant));
    expect(result.exercise?.hands.orientation).toBe('neutral');
    expect(result.exercise?.equipment.instances.filter((item) => item.kind === 'dumbbell').map((item) => item.mass)).toEqual([12, 12]);
    expect(result.exercise?.tempo).toEqual(TEMPO_PROFILES.controlled);
    // A candidate, never a library exercise.
    expect(result.exercise?.id).toMatch(/^generated_/);
    expect(EXERCISES.some((exercise) => exercise.id === result.exercise?.id)).toBe(false);
  });

  it('reproduces a library exercise from the same intent, which is what makes the family the source', () => {
    const result = generateExercise('a standing dumbbell curl with 10 kg dumbbells', options);
    expect(motionOf(result.exercise!)).toEqual(motionOf(bicepCurl));
  });

  it(
    'builds the squat and lunge variants from their families, not from per-exercise code',
    () => {
      const squat = generateExercise(SQUAT, options);
      expect(squat.family?.id).toBe('squat');
      expect(squat.exercise).toEqual(squatFamily(squat.variant as SquatVariant));
      expect(squat.exercise?.equipment.instances).toEqual([]);
      expect(squat.exercise?.tempo).toEqual(TEMPO_PROFILES.slow);

      const lunge = generateExercise(REVERSE_LUNGE, options);
      expect(lunge.family?.id).toBe('lunge');
      expect(lunge.exercise).toEqual(lungeFamily(lunge.variant as LungeVariant));
      expect(lunge.reference).toBe('reverse_lunge');
      expect(lunge.exercise?.tempo).toEqual(TEMPO_PROFILES.controlled);
    },
    20_000,
  );

  it(
    'reproduces the library air squat, split squat and lunge variants from the same intent',
    () => {
      expect(motionOf(generateExercise('a bodyweight squat', options).exercise!)).toEqual(motionOf(airSquat));
      expect(motionOf(generateExercise('a split squat', options).exercise!)).toEqual(motionOf(splitSquat));
      expect(motionOf(generateExercise('a forward lunge', options).exercise!)).toEqual(motionOf(forwardLunge));
      expect(motionOf(generateExercise('a reverse lunge', options).exercise!)).toEqual(motionOf(reverseLunge));
    },
    20_000,
  );

  it('builds the Romanian deadlift from hingeFamily rather than a standalone definition', () => {
    const result = generateExercise(RDL, options);
    expect(result.family?.id).toBe('hinge');
    expect(result.exercise).toEqual(hingeFamily(result.variant as HingeVariant));
    expect(result.reference).toBe('dumbbell_romanian_deadlift');
    expect(result.exercise?.equipment.instances.filter((item) => item.kind === 'dumbbell').map((item) => item.mass)).toEqual([18, 18]);
    expect(result.exercise?.tempo).toEqual(TEMPO_PROFILES.slow);
  });

  it('reproduces the library Romanian deadlift motion from a plain certified intent', () => {
    const result = generateExercise('a dumbbell Romanian deadlift', options);
    expect(motionOf(result.exercise!)).toEqual(motionOf(romanianDeadlift));
  });

  it('builds the bent-over row from rowFamily rather than a standalone definition', () => {
    const result = generateExercise(ROW, options);
    expect(result.family?.id).toBe('row');
    expect(result.exercise).toEqual(rowFamily(result.variant as RowVariant));
    expect(result.reference).toBe('dumbbell_bent_over_row');
    expect(result.exercise?.equipment.instances.filter((item) => item.kind === 'dumbbell').map((item) => item.mass)).toEqual([16, 16]);
    expect(result.exercise?.tempo).toEqual(TEMPO_PROFILES.controlled);
  });

  it('reproduces the library bent-over row motion from the plain certified intent', () => {
    const result = generateExercise('a dumbbell bent-over row', options);
    expect(motionOf(result.exercise!)).toEqual(motionOf(bentOverRow));
  });

  it('builds the strict pull-up from verticalPullFamily rather than a standalone definition', () => {
    const result = generateExercise(PULLUP, options);
    expect(result.family?.id).toBe('vertical_pull');
    expect(result.exercise).toEqual(verticalPullFamily(result.variant as VerticalPullVariant));
    expect(result.reference).toBe('pull_up');
    expect(result.exercise?.equipment.instances.map((item) => item.kind)).toEqual(['squat_rack']);
    expect(result.exercise?.tempo).toEqual(TEMPO_PROFILES.controlled);
  });

  it('reproduces the accepted pull-up motion from a plain certified intent', () => {
    const result = generateExercise('a pull-up', options);
    expect(motionOf(result.exercise!)).toEqual(motionOf(pullUp));
  });

  it('builds the standard push-up from horizontalPressFamily rather than a standalone definition', () => {
    const result = generateExercise(PUSHUP, options);
    expect(result.family?.id).toBe('horizontal_press');
    expect(result.exercise).toEqual(horizontalPressFamily(result.variant as HorizontalPressVariant));
    expect(result.reference).toBe('push_up');
    expect(result.exercise?.equipment.instances).toEqual([]);
    expect(result.exercise?.tempo).toEqual(TEMPO_PROFILES.controlled);
  });

  it('reproduces the accepted push-up motion from a plain certified intent', () => {
    const result = generateExercise('a push-up', options);
    expect(motionOf(result.exercise!)).toEqual(motionOf(pushUp));
  });

  it('will not certify what it could not measure', () => {
    const result = generateExercise(HAMMER, options);
    // Every character-free check passes — and the hammer curl's dumbbells are
    // 17 mm inside the thighs, which only the body checks can see.
    expect(result.report?.failed).toEqual([]);
    expect(result.report?.skipped).toEqual(['equipmentClearance', 'armTrunk']);
    expect(result.status).toBe('unverified');
  });

  it('builds nothing from a request it has to ask about', () => {
    for (const prompt of [
      'alternating hammer curl',
      'incline curl at 30 degrees',
      'neutral grip shoulder press',
      'goblet squat',
      'walking lunge',
      'a squat with 20 kg dumbbells',
    ]) {
      const result = generateExercise(prompt, options);
      expect(result.status, prompt).toBe('blocked');
      expect(result.exercise, prompt).toBeUndefined();
      expect(result.validations, prompt).toBe(0);
    }
  });
});

const ASSET =
  process.env.REAL_CHARACTER_GLB ?? 'review-assets/characters/HomeGymPT_Male_CORNER_FINAL_SHORTS.glb';

describe.skipIf(!existsSync(ASSET))('generating on the production character', () => {
  let character: { build: CharacterBuild; label: string };
  // The async pipeline yields between steps, so a long generation does not
  // starve the test worker's reporting.
  beforeAll(async () => {
    const bytes = readFileSync(ASSET);
    const data = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    character = { build: await retargetedCharacterSource({ id: ASSET, label: ASSET, data }).build(rig), label: ASSET };
  }, 120_000);

  it(
    'corrects the standing hammer curl out of the thighs, within the family, and certifies it',
    async () => {
      const result = await generateExerciseAsync(HAMMER, { rig, library, character });
      // From the family's defaults the neutral-grip dumbbells hang in the
      // thighs, and the arms sit closer to the chest than the library's hammer
      // curl does.
      expect(result.initial?.failed).toEqual(['equipmentClearance', 'armTrunk']);
      // One lever answers both, so it is the only change made: the arms held
      // 12° out, which is what the library's hand-tuned hammer curl arrived at.
      expect(result.corrections).toHaveLength(1);
      expect((result.variant as CurlVariant).abduction).toEqual({ start: 12, peak: 13 });
      expect((result.variant as CurlVariant).elbow).toBeUndefined();
      expect(result.attempts.at(-1)?.outcome).toBe('accepted');
      expect(result.status).toBe('passed');
      expect(result.report?.checks.every((check) => check.status === 'pass')).toBe(true);

      // The loop's verdict stands on its own: validated afresh, outside the loop.
      const again = validateCandidate(
        { rig, character, reference: library(result.reference!) },
        result.exercise!,
        generateClip(rig, result.exercise!),
        (exercise) => generateClip(rig, exercise),
      );
      expect(again.passed).toBe(true);
    },
    900_000,
  );

  it(
    'builds the incline curl on the 45° bench, passing first time',
    async () => {
      const result = await generateExerciseAsync(INCLINE, { rig, library, character });
      expect(result.status).toBe('passed');
      expect(result.initial?.failed).toEqual([]);
      expect(result.corrections).toEqual([]);
      expect(result.validations).toBe(1);
      expect(result.exercise?.equipment.instances.map((item) => item.kind).sort()).toEqual(['dumbbell', 'dumbbell', 'incline_bench']);
      expect(result.exercise?.equipment.instances.find((item) => item.kind === 'dumbbell')?.mass).toBe(8);
      expect(result.reference).toBe('incline_dumbbell_curl');
      // 45° is the bench's implicit default, so the bench instance carries no
      // `backAngle` at all — the same shape the library's own incline curl has.
      expect(result.exercise?.equipment.instances.find((item) => item.kind === 'incline_bench')?.backAngle).toBeUndefined();
    },
    900_000,
  );

  it(
    'refuses an incline angle the bench adjusts to but no candidate there is certified, without spending the character',
    async () => {
      // 30° and 60° were both tried against this same character and refused
      // (see `families.ts`'s `CERTIFIED_INCLINE_ANGLES`): the back does not
      // reach the pad at 30°, and presses too far into it at 60°. The request
      // is blocked before any validation runs, character or not.
      for (const angle of [30, 60]) {
        const result = await generateExerciseAsync(
          `Create an incline dumbbell curl at ${angle} degrees with 8 kg dumbbells.`,
          { rig, library, character },
        );
        expect(result.status, `${angle}°`).toBe('blocked');
        expect(result.validations, `${angle}°`).toBe(0);
        expect(result.parsed.issues.find((issue) => issue.code === 'angle')?.message, `${angle}°`).toMatch(/45°/);
      }
    },
    30_000,
  );

  it(
    'builds a seated shoulder press through the same pipeline, with no press-specific generator code',
    async () => {
      const result = await generateExerciseAsync(PRESS, { rig, library, character });
      expect(result.family?.id).toBe('overhead_press');
      expect(result.status).toBe('passed');
      expect(result.exercise?.equipment.instances.some((item) => item.kind === 'flat_bench' && item.supportsBody)).toBe(true);
      expect(result.exercise?.tempo).toEqual(TEMPO_PROFILES.controlled);
    },
    900_000,
  );

  it(
    'stops at its budget and reports the failure rather than passing it',
    async () => {
      const result = await generateExerciseAsync(HAMMER, { rig, library, character, budget: 3 });
      expect(result.validations).toBeLessThanOrEqual(3);
      expect(result.status).toBe('failed');
      expect(result.report?.failed).toContain('equipmentClearance');
    },
    900_000,
  );

  it(
    'builds a dumbbell Romanian deadlift through the same pipeline',
    async () => {
      const result = await generateExerciseAsync(RDL, { rig, library, character });
      expect(result.family?.id).toBe('hinge');
      expect(result.status).toBe('passed');
      expect(result.initial?.failed).toEqual([]);
      expect(result.corrections).toEqual([]);
      expect(result.validations).toBe(1);
      expect(result.reference).toBe('dumbbell_romanian_deadlift');
      expect(result.exercise?.tempo).toEqual(TEMPO_PROFILES.slow);
      expect(result.report?.checks.every((check) => check.status === 'pass')).toBe(true);
    },
    900_000,
  );

  it(
    'builds a dumbbell bent-over row through the same pipeline',
    async () => {
      const result = await generateExerciseAsync(ROW, { rig, library, character });
      expect(result.family?.id).toBe('row');
      expect(result.status).toBe('passed');
      expect(result.initial?.failed).toEqual([]);
      expect(result.corrections).toEqual([]);
      expect(result.validations).toBe(1);
      expect(result.reference).toBe('dumbbell_bent_over_row');
      expect(result.exercise?.tempo).toEqual(TEMPO_PROFILES.controlled);
      expect(result.report?.checks.every((check) => check.status === 'pass')).toBe(true);
    },
    900_000,
  );

  it(
    'builds a strict pull-up through the same pipeline',
    async () => {
      const result = await generateExerciseAsync(PULLUP, { rig, library, character });
      expect(result.family?.id).toBe('vertical_pull');
      expect(result.status).toBe('passed');
      expect(result.initial?.failed).toEqual([]);
      expect(result.corrections).toEqual([]);
      expect(result.validations).toBe(1);
      expect(result.reference).toBe('pull_up');
      expect(result.exercise?.tempo).toEqual(TEMPO_PROFILES.controlled);
      expect(result.report?.checks.every((check) => check.status === 'pass')).toBe(true);
    },
    900_000,
  );

  it(
    'builds a standard push-up through the same pipeline',
    async () => {
      const result = await generateExerciseAsync(PUSHUP, { rig, library, character });
      expect(result.family?.id).toBe('horizontal_press');
      expect(result.status).toBe('passed');
      expect(result.initial?.failed).toEqual([]);
      expect(result.corrections).toEqual([]);
      expect(result.validations).toBe(1);
      expect(result.reference).toBe('push_up');
      expect(result.exercise?.tempo).toEqual(TEMPO_PROFILES.controlled);
      expect(result.report?.checks.every((check) => check.status === 'pass')).toBe(true);
    },
    900_000,
  );

  it(
    'builds a bodyweight squat through the same pipeline, with no squat-specific generator code',
    async () => {
      const result = await generateExerciseAsync(SQUAT, { rig, library, character });
      expect(result.family?.id).toBe('squat');
      expect(result.status).toBe('passed');
      expect(result.initial?.failed).toEqual([]);
      expect(result.corrections).toEqual([]);
      expect(result.validations).toBe(1);
      expect(result.exercise?.equipment.instances).toEqual([]);
      expect(result.exercise?.tempo).toEqual(TEMPO_PROFILES.slow);
      expect(result.report?.checks.every((check) => check.status === 'pass')).toBe(true);
    },
    900_000,
  );

  it(
    'builds a reverse lunge through the same pipeline, with no lunge-specific generator code',
    async () => {
      const result = await generateExerciseAsync(REVERSE_LUNGE, { rig, library, character });
      expect(result.family?.id).toBe('lunge');
      expect(result.status).toBe('passed');
      expect(result.initial?.failed).toEqual([]);
      expect(result.corrections).toEqual([]);
      expect(result.validations).toBe(1);
      expect(result.reference).toBe('reverse_lunge');
      expect(result.exercise?.tempo).toEqual(TEMPO_PROFILES.controlled);
      expect(result.report?.checks.every((check) => check.status === 'pass')).toBe(true);
    },
    900_000,
  );

  it(
    'builds the split squat and forward lunge too, passing first time',
    async () => {
      for (const [prompt, family, reference] of [
        ['Create a split squat.', 'lunge', 'split_squat'],
        ['Create a forward lunge.', 'lunge', 'forward_lunge'],
      ] as const) {
        const result = await generateExerciseAsync(prompt, { rig, library, character });
        expect(result.family?.id, prompt).toBe(family);
        expect(result.status, prompt).toBe('passed');
        expect(result.validations, prompt).toBe(1);
        expect(result.reference, prompt).toBe(reference);
      }
    },
    900_000,
  );
});
