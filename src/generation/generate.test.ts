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
import { raiseFamily } from '../exercises/families/raise';
import type { RaiseVariant } from '../exercises/families/raise';
import { extensionFamily } from '../exercises/families/extension';
import type { ExtensionVariant } from '../exercises/families/extension';
import { horizontalPressFamily } from '../exercises/families/horizontalPress';
import type { HorizontalPressVariant } from '../exercises/families/horizontalPress';
import { calfFamily } from '../exercises/families/calf';
import type { CalfVariant } from '../exercises/families/calf';
import { trunkFlexionFamily } from '../exercises/families/trunkFlexion';
import type { TrunkFlexionVariant } from '../exercises/families/trunkFlexion';
import { supineFamily } from '../exercises/families/supine';
import type { SupineVariant } from '../exercises/families/supine';
import { carryFamily } from '../exercises/families/carry';
import type { CarryVariant } from '../exercises/families/carry';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { airSquat } from '../exercises/definitions/airSquat';
import { splitSquat } from '../exercises/definitions/splitSquat';
import { forwardLunge } from '../exercises/definitions/forwardLunge';
import { reverseLunge } from '../exercises/definitions/reverseLunge';
import { romanianDeadlift } from '../exercises/definitions/romanianDeadlift';
import { bentOverRow } from '../exercises/definitions/bentOverRow';
import { pullUp } from '../exercises/definitions/pullUp';
import { lateralRaise } from '../exercises/definitions/lateralRaise';
import { frontRaise } from '../exercises/definitions/frontRaise';
import { overheadExtension } from '../exercises/definitions/overheadExtension';
import { pushUp } from '../exercises/definitions/pushUp';
import { calfRaise } from '../exercises/definitions/calfRaise';
import { dumbbellCalfRaise } from '../exercises/definitions/dumbbellCalfRaise';
import { crunch } from '../exercises/definitions/crunch';
import { sitUp } from '../exercises/definitions/sitUp';
import { dumbbellBenchPress } from '../exercises/definitions/dumbbellBenchPress';
import { dumbbellFly } from '../exercises/definitions/dumbbellFly';
import { farmersWalk } from '../exercises/definitions/farmersWalk';
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
const PULL_UP = 'Create a strict pull-up with controlled tempo.';
const LATERAL_RAISE = 'Create a lateral raise with 6 kg dumbbells.';
const FRONT_RAISE = 'Create a front raise with 7 kg dumbbells and slow tempo.';
const OVERHEAD_EXTENSION = 'Create a standing dumbbell triceps extension with 8 kg dumbbells.';
const PUSH_UP = 'Create a standard push-up with controlled tempo.';
const CALF = 'Create a calf raise with 18 kg dumbbells and slow tempo.';
const CRUNCH = 'Create a crunch.';
const SIT_UP = 'Create a sit-up with controlled tempo.';
const BENCH_PRESS = 'Create a dumbbell bench press with 20 kg dumbbells and controlled tempo.';
const FLY = 'Create a dumbbell fly with 10 kg dumbbells.';
const FARMERS_WALK = "Create a farmer's walk with 26 kg dumbbells.";

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

  it('builds the strict pull-up from verticalPullFamily', () => {
    const result = generateExercise(PULL_UP, options);
    expect(result.family?.id).toBe('vertical_pull');
    expect(result.exercise).toEqual(verticalPullFamily(result.variant as VerticalPullVariant));
    expect(result.reference).toBe('pull_up');
    expect(result.exercise?.tempo).toEqual(TEMPO_PROFILES.controlled);
    expect(motionOf(generateExercise('a pull-up', options).exercise!)).toEqual(motionOf(pullUp));
  });

  it('builds both dumbbell raises from raiseFamily', () => {
    const lateral = generateExercise(LATERAL_RAISE, options);
    expect(lateral.family?.id).toBe('raise');
    expect(lateral.exercise).toEqual(raiseFamily(lateral.variant as RaiseVariant));
    expect(lateral.reference).toBe('dumbbell_lateral_raise');
    expect(lateral.exercise?.equipment.instances.filter((item) => item.kind === 'dumbbell').map((item) => item.mass)).toEqual([6, 6]);
    expect(motionOf(generateExercise('a lateral raise', options).exercise!)).toEqual(motionOf(lateralRaise));

    const front = generateExercise(FRONT_RAISE, options);
    expect(front.family?.id).toBe('raise');
    expect(front.exercise).toEqual(raiseFamily(front.variant as RaiseVariant));
    expect(front.reference).toBe('dumbbell_front_raise');
    expect(front.exercise?.tempo).toEqual(TEMPO_PROFILES.slow);
    expect(motionOf(generateExercise('a front raise', options).exercise!)).toEqual(motionOf(frontRaise));
  });

  it('builds the standing overhead triceps extension from extensionFamily', () => {
    const result = generateExercise(OVERHEAD_EXTENSION, options);
    expect(result.family?.id).toBe('extension');
    expect(result.exercise).toEqual(extensionFamily(result.variant as ExtensionVariant));
    expect(result.reference).toBe('dumbbell_overhead_triceps_extension');
    expect(result.exercise?.equipment.instances.filter((item) => item.kind === 'dumbbell').map((item) => item.mass)).toEqual([8, 8]);
    expect(motionOf(generateExercise('a dumbbell triceps extension', options).exercise!)).toEqual(motionOf(overheadExtension));
  });

  it('builds the standard push-up from horizontalPressFamily', () => {
    const result = generateExercise(PUSH_UP, options);
    expect(result.family?.id).toBe('horizontal_press');
    expect(result.exercise).toEqual(horizontalPressFamily(result.variant as HorizontalPressVariant));
    expect(result.reference).toBe('push_up');
    expect(result.exercise?.tempo).toEqual(TEMPO_PROFILES.controlled);
    expect(motionOf(generateExercise('a push-up', options).exercise!)).toEqual(motionOf(pushUp));
  });

  it('builds bodyweight and loaded calf raises from calfFamily', () => {
    const bodyweight = generateExercise('a standing calf raise', options);
    expect(bodyweight.family?.id).toBe('calf');
    expect(bodyweight.exercise).toEqual(calfFamily(bodyweight.variant as CalfVariant));
    expect(bodyweight.reference).toBe('standing_calf_raise');
    expect(motionOf(bodyweight.exercise!)).toEqual(motionOf(calfRaise));

    const loaded = generateExercise(CALF, options);
    expect(loaded.family?.id).toBe('calf');
    expect(loaded.exercise).toEqual(calfFamily(loaded.variant as CalfVariant));
    expect(loaded.reference).toBe('dumbbell_calf_raise');
    expect(loaded.exercise?.equipment.instances.filter((item) => item.kind === 'dumbbell').map((item) => item.mass)).toEqual([18, 18]);
    expect(loaded.exercise?.tempo).toEqual(TEMPO_PROFILES.slow);
    expect(motionOf(generateExercise('a calf raise with 14 kg dumbbells', options).exercise!)).toEqual(motionOf(dumbbellCalfRaise));
  });

  it('builds crunch and sit-up from trunkFlexionFamily', () => {
    const crunchResult = generateExercise(CRUNCH, options);
    expect(crunchResult.family?.id).toBe('trunk_flexion');
    expect(crunchResult.exercise).toEqual(trunkFlexionFamily(crunchResult.variant as TrunkFlexionVariant));
    expect(crunchResult.reference).toBe('crunch');
    expect(motionOf(crunchResult.exercise!)).toEqual(motionOf(crunch));

    const situpResult = generateExercise(SIT_UP, options);
    expect(situpResult.family?.id).toBe('trunk_flexion');
    expect(situpResult.exercise).toEqual(trunkFlexionFamily(situpResult.variant as TrunkFlexionVariant));
    expect(situpResult.reference).toBe('sit_up');
    expect(situpResult.exercise?.tempo).toEqual(TEMPO_PROFILES.controlled);
    expect(motionOf(generateExercise('a sit-up', options).exercise!)).toEqual(motionOf(sitUp));
  });

  it('builds dumbbell bench press and fly from supineFamily', () => {
    const press = generateExercise(BENCH_PRESS, options);
    expect(press.family?.id).toBe('supine');
    expect(press.exercise).toEqual(supineFamily(press.variant as SupineVariant));
    expect(press.reference).toBe('dumbbell_bench_press');
    expect(press.exercise?.equipment.instances.filter((item) => item.kind === 'dumbbell').map((item) => item.mass)).toEqual([20, 20]);
    expect(press.exercise?.tempo).toEqual(TEMPO_PROFILES.controlled);
    expect(motionOf(generateExercise('a dumbbell bench press', options).exercise!)).toEqual(motionOf(dumbbellBenchPress));

    const fly = generateExercise(FLY, options);
    expect(fly.family?.id).toBe('supine');
    expect(fly.exercise).toEqual(supineFamily(fly.variant as SupineVariant));
    expect(fly.reference).toBe('dumbbell_fly');
    expect(motionOf(fly.exercise!)).toEqual(motionOf(dumbbellFly));
  });

  it("builds the farmer's walk from carryFamily", () => {
    const result = generateExercise(FARMERS_WALK, options);
    expect(result.family?.id).toBe('carry');
    expect(result.exercise).toEqual(carryFamily(result.variant as CarryVariant));
    expect(result.reference).toBe('farmers_walk');
    expect(result.exercise?.equipment.instances.filter((item) => item.kind === 'dumbbell').map((item) => item.mass)).toEqual([26, 26]);
    expect(motionOf(generateExercise("a farmer's walk", options).exercise!)).toEqual(motionOf(farmersWalk));
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
    'builds a strict pull-up through the same production-character pipeline',
    async () => {
      const result = await generateExerciseAsync(PULL_UP, { rig, library, character });
      expect(result.family?.id).toBe('vertical_pull');
      expect(result.status).toBe('passed');
      expect(result.initial?.failed).toEqual([]);
      expect(result.corrections).toEqual([]);
      expect(result.validations).toBe(1);
      expect(result.reference).toBe('pull_up');
      expect(result.report?.checks.every((check) => check.status === 'pass')).toBe(true);
    },
    900_000,
  );

  it(
    'builds lateral and front raises through the same production-character pipeline',
    async () => {
      for (const prompt of [LATERAL_RAISE, FRONT_RAISE]) {
        const result = await generateExerciseAsync(prompt, { rig, library, character });
        expect(result.family?.id, prompt).toBe('raise');
        expect(result.status, prompt).toBe('passed');
        expect(result.initial?.failed, prompt).toEqual([]);
        expect(result.corrections, prompt).toEqual([]);
        expect(result.validations, prompt).toBe(1);
        expect(result.report?.checks.every((check) => check.status === 'pass'), prompt).toBe(true);
      }
    },
    900_000,
  );

  it(
    'builds the overhead triceps extension through the same production-character pipeline',
    async () => {
      const result = await generateExerciseAsync(OVERHEAD_EXTENSION, { rig, library, character });
      expect(result.family?.id).toBe('extension');
      expect(result.status).toBe('passed');
      expect(result.initial?.failed).toEqual([]);
      expect(result.corrections).toEqual([]);
      expect(result.validations).toBe(1);
      expect(result.reference).toBe('dumbbell_overhead_triceps_extension');
      expect(result.report?.checks.every((check) => check.status === 'pass')).toBe(true);
    },
    900_000,
  );

  it(
    'builds the standard push-up through the same production-character pipeline',
    async () => {
      const result = await generateExerciseAsync(PUSH_UP, { rig, library, character });
      expect(result.family?.id).toBe('horizontal_press');
      expect(result.status).toBe('passed');
      expect(result.initial?.failed).toEqual([]);
      expect(result.corrections).toEqual([]);
      expect(result.validations).toBe(1);
      expect(result.reference).toBe('push_up');
      expect(result.report?.checks.every((check) => check.status === 'pass')).toBe(true);
    },
    900_000,
  );

  it(
    'builds bodyweight and loaded calf raises through the same production-character pipeline',
    async () => {
      for (const prompt of ['Create a standing calf raise.', CALF]) {
        const result = await generateExerciseAsync(prompt, { rig, library, character });
        expect(result.family?.id, prompt).toBe('calf');
        expect(result.status, prompt).toBe('passed');
        expect(result.initial?.failed, prompt).toEqual([]);
        expect(result.corrections, prompt).toEqual([]);
        expect(result.validations, prompt).toBe(1);
        expect(result.report?.checks.every((check) => check.status === 'pass'), prompt).toBe(true);
      }
    },
    900_000,
  );

  it(
    'builds crunch and sit-up through the same production-character pipeline',
    async () => {
      for (const prompt of [CRUNCH, SIT_UP]) {
        const result = await generateExerciseAsync(prompt, { rig, library, character });
        expect(result.family?.id, prompt).toBe('trunk_flexion');
        expect(result.status, prompt).toBe('passed');
        expect(result.initial?.failed, prompt).toEqual([]);
        expect(result.corrections, prompt).toEqual([]);
        expect(result.validations, prompt).toBe(1);
        expect(result.report?.checks.every((check) => check.status === 'pass'), prompt).toBe(true);
      }
    },
    900_000,
  );

  it(
    'builds flat dumbbell bench press and fly through the same production-character pipeline',
    async () => {
      for (const prompt of [BENCH_PRESS, FLY]) {
        const result = await generateExerciseAsync(prompt, { rig, library, character });
        expect(result.family?.id, prompt).toBe('supine');
        expect(result.status, prompt).toBe('passed');
        expect(result.initial?.failed, prompt).toEqual([]);
        expect(result.corrections, prompt).toEqual([]);
        expect(result.validations, prompt).toBe(1);
        expect(result.report?.checks.every((check) => check.status === 'pass'), prompt).toBe(true);
      }
    },
    900_000,
  );

  it(
    "builds the farmer's walk through the same production-character pipeline",
    async () => {
      const result = await generateExerciseAsync(FARMERS_WALK, { rig, library, character });
      expect(result.family?.id).toBe('carry');
      expect(result.status).toBe('passed');
      expect(result.initial?.failed).toEqual([]);
      expect(result.corrections).toEqual([]);
      expect(result.validations).toBe(1);
      expect(result.reference).toBe('farmers_walk');
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
