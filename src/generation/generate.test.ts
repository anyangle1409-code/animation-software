import { existsSync, readFileSync } from 'node:fs';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { canonicalSkeleton } from '../rig/skeleton';
import { generateClip } from '../animation/generate';
import { retargetedCharacterSource } from '../character/retargetSource';
import type { CharacterBuild } from '../character';
import { proceduralCharacter } from '../character/procedural';
import { EXERCISES, EXERCISE_BY_ID } from '../exercises/library';
import { curlFamily } from '../exercises/families/curl';
import type { CurlVariant } from '../exercises/families/curl';
import { squatFamily } from '../exercises/families/squat';
import type { SquatVariant } from '../exercises/families/squat';
import { lungeFamily } from '../exercises/families/lunge';
import type { LungeVariant } from '../exercises/families/lunge';
import { horizontalPressFamily } from '../exercises/families/horizontalPress';
import type { HorizontalPressVariant } from '../exercises/families/horizontalPress';
import { calfFamily } from '../exercises/families/calf';
import type { CalfVariant } from '../exercises/families/calf';
import { hingeFamily } from '../exercises/families/hinge';
import type { HingeVariant } from '../exercises/families/hinge';
import { rowFamily } from '../exercises/families/row';
import type { RowVariant } from '../exercises/families/row';
import { raiseFamily } from '../exercises/families/raise';
import type { RaiseVariant } from '../exercises/families/raise';
import { verticalPullFamily } from '../exercises/families/verticalPull';
import type { VerticalPullVariant } from '../exercises/families/verticalPull';
import { extensionFamily } from '../exercises/families/extension';
import type { ExtensionVariant } from '../exercises/families/extension';
import { supineFamily } from '../exercises/families/supine';
import type { SupineVariant } from '../exercises/families/supine';
import { trunkFlexionFamily } from '../exercises/families/trunkFlexion';
import type { TrunkFlexionVariant } from '../exercises/families/trunkFlexion';
import { carryFamily } from '../exercises/families/carry';
import type { CarryVariant } from '../exercises/families/carry';
import { rotationFamily } from '../exercises/families/rotation';
import type { RotationVariant } from '../exercises/families/rotation';
import { antiRotationFamily } from '../exercises/families/antiRotation';
import type { AntiRotationVariant } from '../exercises/families/antiRotation';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { airSquat } from '../exercises/definitions/airSquat';
import { splitSquat } from '../exercises/definitions/splitSquat';
import { forwardLunge } from '../exercises/definitions/forwardLunge';
import { reverseLunge } from '../exercises/definitions/reverseLunge';
import { pushUp } from '../exercises/definitions/pushUp';
import { romanianDeadlift } from '../exercises/definitions/romanianDeadlift';
import { bentOverRow } from '../exercises/definitions/bentOverRow';
import { lateralRaise } from '../exercises/definitions/lateralRaise';
import { frontRaise } from '../exercises/definitions/frontRaise';
import { pullUp } from '../exercises/definitions/pullUp';
import { overheadExtension } from '../exercises/definitions/overheadExtension';
import { dumbbellBenchPress } from '../exercises/definitions/dumbbellBenchPress';
import { dumbbellFly } from '../exercises/definitions/dumbbellFly';
import { crunch } from '../exercises/definitions/crunch';
import { sitUp } from '../exercises/definitions/sitUp';
import { farmersWalk } from '../exercises/definitions/farmersWalk';
import { russianTwist } from '../exercises/definitions/russianTwist';
import { cableWoodchop } from '../exercises/definitions/cableWoodchop';
import { pallofPress } from '../exercises/definitions/pallofPress';
import { calfRaise } from '../exercises/definitions/calfRaise';
import type { ExerciseDefinition } from '../exercises/types';
import { generateExercise, generateExerciseAsync } from './generate';
import { generatorFamily } from './families';
import { parsePrompt } from './parse';
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
const STANDING_PRESS = 'Create a standing dumbbell shoulder press with 10 kg dumbbells and controlled tempo.';
const SQUAT = 'Create a bodyweight squat with a slow tempo.';
const REVERSE_LUNGE = 'Create a reverse lunge with controlled tempo.';
const PUSH_UP = 'Create a standard push-up with controlled tempo.';
const CALF_RAISE = 'Create a standing calf raise with a slow tempo.';
const RDL = 'Create a dumbbell Romanian deadlift with 16 kg dumbbells and controlled tempo.';
const ROW = 'exercise: dumbbell bent-over row with 16 kg dumbbells and controlled tempo';
const LATERAL_RAISE = 'exercise: dumbbell lateral raise with 6 kg dumbbells and controlled tempo';
const FRONT_RAISE = 'exercise: dumbbell front raise with 6 kg dumbbells and controlled tempo';
const PULL_UP = 'exercise: strict pull-up with controlled tempo';
const OVERHEAD_EXTENSION = 'exercise: dumbbell overhead triceps extension with 8 kg dumbbells and controlled tempo';
const BENCH_PRESS = 'exercise: dumbbell bench press with 16 kg dumbbells and controlled tempo';
const FLY = 'exercise: dumbbell fly with 10 kg dumbbells and controlled tempo';
const CRUNCH = 'exercise: bodyweight crunch with controlled tempo';
const SIT_UP = 'exercise: bodyweight sit-up with controlled tempo';
const FARMERS_WALK = "exercise: farmer's walk with 24 kg dumbbells";
const RUSSIAN_TWIST = 'exercise: Russian twist with controlled tempo';
const CABLE_WOODCHOP = 'exercise: cable woodchop with controlled tempo';
const PALLOF_PRESS = 'exercise: Pallof press with controlled tempo';

const CLEAN_FALLBACK_CASES = [
  [STANDING_PRESS, 'overhead_press', 'dumbbell_shoulder_press'],
  [PUSH_UP, 'horizontal_press', 'push_up'],
  [BENCH_PRESS, 'supine', 'dumbbell_bench_press'],
  [FLY, 'supine', 'dumbbell_fly'],
  [CRUNCH, 'trunk_flexion', 'crunch'],
  [SIT_UP, 'trunk_flexion', 'sit_up'],
  [FARMERS_WALK, 'carry', 'farmers_walk'],
  [RUSSIAN_TWIST, 'rotation', 'russian_twist'],
  [CABLE_WOODCHOP, 'rotation', 'cable_woodchop'],
  [PALLOF_PRESS, 'anti_rotation', 'cable_pallof_press'],
  [REVERSE_LUNGE, 'lunge', 'reverse_lunge'],
  [CALF_RAISE, 'calf', 'standing_calf_raise'],
  [RDL, 'hinge', 'dumbbell_romanian_deadlift'],
  [ROW, 'row', 'dumbbell_bent_over_row'],
  [LATERAL_RAISE, 'raise', 'dumbbell_lateral_raise'],
  [FRONT_RAISE, 'raise', 'dumbbell_front_raise'],
  [PULL_UP, 'vertical_pull', 'pull_up'],
  [OVERHEAD_EXTENSION, 'extension', 'dumbbell_overhead_triceps_extension'],
] as const;

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

  it('builds the flat bench press and fly from the supine family', () => {
    const press = generateExercise(BENCH_PRESS, options);
    expect(press.family?.id).toBe('supine');
    expect(press.exercise).toEqual(supineFamily(press.variant as SupineVariant));
    expect(press.reference).toBe('dumbbell_bench_press');
    expect(press.exercise?.equipment.instances.filter((item) => item.kind === 'dumbbell').map((item) => item.mass)).toEqual([16, 16]);
    expect(press.exercise?.tempo).toEqual(TEMPO_PROFILES.controlled);

    const fly = generateExercise(FLY, options);
    expect(fly.family?.id).toBe('supine');
    expect(fly.exercise).toEqual(supineFamily(fly.variant as SupineVariant));
    expect(fly.reference).toBe('dumbbell_fly');
    expect(fly.exercise?.equipment.instances.filter((item) => item.kind === 'dumbbell').map((item) => item.mass)).toEqual([10, 10]);
    expect(fly.exercise?.tempo).toEqual(TEMPO_PROFILES.controlled);
  });

  it('reproduces the accepted flat bench press and fly motion from family defaults', () => {
    expect(motionOf(generateExercise('a dumbbell bench press', options).exercise!)).toEqual(motionOf(dumbbellBenchPress));
    expect(motionOf(generateExercise('a dumbbell fly', options).exercise!)).toEqual(motionOf(dumbbellFly));
  });

  it('builds the crunch and sit-up from the trunk-flexion family', () => {
    const crunchResult = generateExercise(CRUNCH, options);
    expect(crunchResult.family?.id).toBe('trunk_flexion');
    expect(crunchResult.exercise).toEqual(
      trunkFlexionFamily(crunchResult.variant as TrunkFlexionVariant),
    );
    expect(crunchResult.reference).toBe('crunch');
    expect(crunchResult.exercise?.equipment.instances).toEqual([]);
    expect(crunchResult.exercise?.tempo).toEqual(TEMPO_PROFILES.controlled);

    const situpResult = generateExercise(SIT_UP, options);
    expect(situpResult.family?.id).toBe('trunk_flexion');
    expect(situpResult.exercise).toEqual(
      trunkFlexionFamily(situpResult.variant as TrunkFlexionVariant),
    );
    expect(situpResult.reference).toBe('sit_up');
    expect(situpResult.exercise?.equipment.instances).toEqual([]);
  });

  it('reproduces the accepted crunch and sit-up motion from family defaults', () => {
    expect(motionOf(generateExercise('a crunch', options).exercise!)).toEqual(motionOf(crunch));
    expect(motionOf(generateExercise('a sit-up', options).exercise!)).toEqual(motionOf(sitUp));
  });

  it('builds cable woodchop and Pallof press from their existing families', () => {
    const woodchop = generateExercise(CABLE_WOODCHOP, options);
    expect(woodchop.family?.id).toBe('rotation');
    expect(woodchop.exercise).toEqual(rotationFamily(woodchop.variant as RotationVariant));
    expect(woodchop.reference).toBe('cable_woodchop');
    expect(woodchop.exercise?.equipment.instances.map((item) => item.kind).sort()).toEqual([
      'cable',
      'cable_handle',
      'cable_tower',
    ]);
    expect(woodchop.exercise?.tempo).toEqual(TEMPO_PROFILES.controlled);

    const pallof = generateExercise(PALLOF_PRESS, options);
    expect(pallof.family?.id).toBe('anti_rotation');
    expect(pallof.exercise).toEqual(antiRotationFamily(pallof.variant as AntiRotationVariant));
    expect(pallof.reference).toBe('cable_pallof_press');
    expect(pallof.exercise?.equipment.instances.map((item) => item.kind).sort()).toEqual([
      'cable',
      'cable_handle',
      'cable_tower',
    ]);
    expect(pallof.exercise?.tempo).toEqual(TEMPO_PROFILES.controlled);
  });

  it('reproduces accepted cable woodchop and Pallof motion from family defaults', () => {
    expect(motionOf(generateExercise('a cable woodchop', options).exercise!)).toEqual(
      motionOf(cableWoodchop),
    );
    expect(motionOf(generateExercise('a Pallof press', options).exercise!)).toEqual(
      motionOf(pallofPress),
    );
  });

  it('builds the Russian twist from the rotation family without rewriting its trunk motion', () => {
    const result = generateExercise(RUSSIAN_TWIST, options);
    expect(result.family?.id).toBe('rotation');
    expect(result.exercise).toEqual(rotationFamily(result.variant as RotationVariant));
    expect(result.reference).toBe('russian_twist');
    expect(result.exercise?.equipment.instances).toEqual([]);
    expect(result.exercise?.tempo).toEqual(TEMPO_PROFILES.controlled);
  });

  it('reproduces the accepted Russian-twist motion from family defaults', () => {
    expect(motionOf(generateExercise('a Russian twist', options).exercise!)).toEqual(
      motionOf(russianTwist),
    );
  });

  it("builds the farmer's walk from the carry family without rewriting the gait", () => {
    const result = generateExercise(FARMERS_WALK, options);
    expect(result.family?.id).toBe('carry');
    expect(result.exercise).toEqual(carryFamily(result.variant as CarryVariant));
    expect(result.reference).toBe('farmers_walk');
    expect(result.exercise?.equipment.instances.filter((item) => item.kind === 'dumbbell').map((item) => item.mass)).toEqual([24, 24]);
    expect(result.exercise?.travel).toEqual(farmersWalk.travel);
    expect(result.exercise?.phases.map((phase) => phase.duration)).toEqual(
      farmersWalk.phases.map((phase) => phase.duration),
    );
  });

  it("reproduces the accepted farmer's-walk motion from family defaults", () => {
    expect(motionOf(generateExercise("a farmer's walk", options).exercise!)).toEqual(
      motionOf(farmersWalk),
    );
  });

  it('builds the standard push-up from the horizontal-press family', () => {
    const result = generateExercise(PUSH_UP, options);
    expect(result.family?.id).toBe('horizontal_press');
    expect(result.exercise).toEqual(
      horizontalPressFamily(result.variant as HorizontalPressVariant),
    );
    expect(result.reference).toBe('push_up');
    expect(result.exercise?.equipment.instances).toEqual([]);
    expect(result.exercise?.tempo).toEqual(TEMPO_PROFILES.controlled);
    expect(EXERCISES.some((exercise) => exercise.id === result.exercise?.id)).toBe(false);
  });

  it('reproduces the accepted push-up motion from the same family defaults', () => {
    const result = generateExercise('a push-up', options);
    expect(motionOf(result.exercise!)).toEqual(motionOf(pushUp));
  });

  it('builds the standing calf raise from the calf family', () => {
    const parsed = parsePrompt(CALF_RAISE);
    expect(parsed.issues.filter((issue) => issue.blocking)).toEqual([]);
    const family = generatorFamily(parsed.intent!.family);
    const variant = family.variant(parsed.intent!) as CalfVariant;
    const exercise = family.build(variant);
    expect(family.id).toBe('calf');
    expect(exercise).toEqual(calfFamily(variant));
    expect(family.reference(parsed.intent!)).toBe('standing_calf_raise');
    expect(exercise.equipment.instances).toEqual([]);
    expect(exercise.tempo).toEqual(TEMPO_PROFILES.slow);
    expect(EXERCISES.some((entry) => entry.id === exercise.id)).toBe(false);
  });

  it('reproduces the accepted standing calf raise from the family defaults', () => {
    const parsed = parsePrompt('a calf raise');
    expect(parsed.issues.filter((issue) => issue.blocking)).toEqual([]);
    const family = generatorFamily(parsed.intent!.family);
    const exercise = family.build(family.variant(parsed.intent!) as CalfVariant);
    expect(motionOf(exercise)).toEqual(motionOf(calfRaise));
  });

  it('builds the Romanian deadlift from the hinge family', () => {
    const parsed = parsePrompt(RDL);
    expect(parsed.issues.filter((issue) => issue.blocking)).toEqual([]);
    const family = generatorFamily(parsed.intent!.family);
    const variant = family.variant(parsed.intent!) as HingeVariant;
    const exercise = family.build(variant);
    expect(family.id).toBe('hinge');
    expect(exercise).toEqual(hingeFamily(variant));
    expect(family.reference(parsed.intent!)).toBe('dumbbell_romanian_deadlift');
    expect(exercise.equipment.instances.filter((item) => item.kind === 'dumbbell').map((item) => item.mass)).toEqual([16, 16]);
    expect(exercise.tempo).toEqual(TEMPO_PROFILES.controlled);
    expect(EXERCISES.some((entry) => entry.id === exercise.id)).toBe(false);
  });

  it('reproduces the accepted Romanian deadlift motion from the family defaults', () => {
    const parsed = parsePrompt('a Romanian deadlift');
    expect(parsed.issues.filter((issue) => issue.blocking)).toEqual([]);
    const family = generatorFamily(parsed.intent!.family);
    const exercise = family.build(family.variant(parsed.intent!) as HingeVariant);
    expect(motionOf(exercise)).toEqual(motionOf(romanianDeadlift));
  });

  it('builds the bent-over row from the row family', () => {
    const parsed = parsePrompt(ROW);
    expect(parsed.issues.filter((issue) => issue.blocking)).toEqual([]);
    const family = generatorFamily(parsed.intent!.family);
    const variant = family.variant(parsed.intent!) as RowVariant;
    const exercise = family.build(variant);
    expect(family.id).toBe('row');
    expect(exercise).toEqual(rowFamily(variant));
    expect(family.reference(parsed.intent!)).toBe('dumbbell_bent_over_row');
    expect(exercise.equipment.instances.filter((item) => item.kind === 'dumbbell').map((item) => item.mass)).toEqual([16, 16]);
    expect(exercise.tempo).toEqual(TEMPO_PROFILES.controlled);
    expect(EXERCISES.some((entry) => entry.id === exercise.id)).toBe(false);
  });

  it('reproduces the accepted bent-over row motion from the family defaults', () => {
    const parsed = parsePrompt('a dumbbell bent-over row');
    expect(parsed.issues.filter((issue) => issue.blocking)).toEqual([]);
    const family = generatorFamily(parsed.intent!.family);
    const exercise = family.build(family.variant(parsed.intent!) as RowVariant);
    expect(motionOf(exercise)).toEqual(motionOf(bentOverRow));
  });

  it('builds lateral/front raises from the raise family', () => {
    for (const [prompt, direction, reference] of [
      [LATERAL_RAISE, 'lateral', 'dumbbell_lateral_raise'],
      [FRONT_RAISE, 'front', 'dumbbell_front_raise'],
    ] as const) {
      const parsed = parsePrompt(prompt);
      expect(parsed.issues.filter((issue) => issue.blocking)).toEqual([]);
      const family = generatorFamily(parsed.intent!.family);
      const variant = family.variant(parsed.intent!) as RaiseVariant;
      const exercise = family.build(variant);
      expect(family.id).toBe('raise');
      expect(variant.direction).toBe(direction);
      expect(exercise).toEqual(raiseFamily(variant));
      expect(family.reference(parsed.intent!)).toBe(reference);
      expect(exercise.equipment.instances.filter((item) => item.kind === 'dumbbell').map((item) => item.mass)).toEqual([6, 6]);
      expect(exercise.tempo).toEqual(TEMPO_PROFILES.controlled);
      expect(EXERCISES.some((entry) => entry.id === exercise.id)).toBe(false);
    }
  });

  it('reproduces the accepted lateral/front raise motion from family defaults', () => {
    expect(motionOf(generateExercise('a dumbbell lateral raise', options).exercise!))
      .toEqual(motionOf(lateralRaise));
    expect(motionOf(generateExercise('a dumbbell front raise', options).exercise!))
      .toEqual(motionOf(frontRaise));
  });

  it('builds the strict pull-up and overhead extension from their accepted families', () => {
    const pull = generateExercise(PULL_UP, options);
    expect(pull.family?.id).toBe('vertical_pull');
    expect(pull.exercise).toEqual(verticalPullFamily(pull.variant as VerticalPullVariant));
    expect(pull.reference).toBe('pull_up');
    expect(pull.exercise?.equipment.instances.some((item) => item.kind === 'squat_rack')).toBe(true);
    expect(pull.exercise?.tempo).toEqual(TEMPO_PROFILES.controlled);

    const extension = generateExercise(OVERHEAD_EXTENSION, options);
    expect(extension.family?.id).toBe('extension');
    expect(extension.exercise).toEqual(extensionFamily(extension.variant as ExtensionVariant));
    expect(extension.reference).toBe('dumbbell_overhead_triceps_extension');
    expect(extension.exercise?.equipment.instances.filter((item) => item.kind === 'dumbbell').map((item) => item.mass)).toEqual([8, 8]);
    expect(extension.exercise?.tempo).toEqual(TEMPO_PROFILES.controlled);
  });

  it('reproduces accepted pull-up and overhead-extension motion from family defaults', () => {
    expect(motionOf(generateExercise('a pull-up', options).exercise!)).toEqual(motionOf(pullUp));
    expect(motionOf(generateExercise('a dumbbell overhead triceps extension', options).exercise!))
      .toEqual(motionOf(overheadExtension));
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

describe('generating on the clean first-party fallback', () => {
  let character: { build: CharacterBuild; label: string };

  beforeAll(async () => {
    character = {
      build: await proceduralCharacter.build(rig),
      label: proceduralCharacter.label,
    };
  });

  afterAll(() => {
    character.build.dispose();
  });

  it(
    'fully certifies a generated bodyweight squat with no skipped body checks',
    async () => {
      const result = await generateExerciseAsync(SQUAT, { rig, library, character });
      expect(result.family?.id).toBe('squat');
      expect(result.status).toBe('passed');
      expect(result.report?.skipped).toEqual([]);
      expect(result.report?.failed).toEqual([]);
      expect(result.report?.checks.every((check) => check.status === 'pass')).toBe(true);
      expect(result.report?.character).toBe(proceduralCharacter.label);
      expect(result.validations).toBe(1);
    },
    120_000,
  );

  it.each(CLEAN_FALLBACK_CASES)(
    'fully certifies clean-fallback example %s',
    async (prompt, family, reference) => {
      const result = await generateExerciseAsync(prompt, { rig, library, character });
      const detail = JSON.stringify({
        prompt,
        status: result.status,
        failed: result.report?.failed,
        skipped: result.report?.skipped,
        checks: result.report?.checks.map((check) => ({
          id: check.id,
          status: check.status,
          detail: check.detail,
          measured: check.measured,
        })),
        corrections: result.corrections,
        validations: result.validations,
      });
      expect(result.family?.id, detail).toBe(family);
      expect(result.reference, detail).toBe(reference);
      expect(result.status, detail).toBe('passed');
      expect(result.report?.skipped, detail).toEqual([]);
      expect(result.report?.failed, detail).toEqual([]);
      expect(result.report?.checks.every((check) => check.status === 'pass'), detail).toBe(true);
      expect(result.report?.character, detail).toBe(proceduralCharacter.label);
      expect(result.validations, detail).toBeGreaterThan(0);
    },
    60_000,
  );

  it(
    'keeps the accepted row reference clean after generator certification',
    () => {
      for (const exercise of [bentOverRow]) {
        const report = validateCandidate(
          { rig, character, reference: exercise },
          exercise,
          generateClip(rig, exercise),
          (definition) => generateClip(rig, definition),
        );
        const detail = JSON.stringify({
          id: exercise.id,
          passed: report.passed,
          failed: report.failed,
          skipped: report.skipped,
          checks: report.checks.map((check) => ({
            id: check.id,
            status: check.status,
            measured: check.measured,
          })),
        });
        expect(report.skipped, detail).toEqual([]);
        expect(report.failed, detail).toEqual([]);
        expect(report.passed, detail).toBe(true);
      }
    },
    180_000,
  );

  it(
    'keeps accepted lateral/front raise references clean after generator certification',
    () => {
      for (const exercise of [lateralRaise, frontRaise]) {
        const report = validateCandidate(
          { rig, character, reference: exercise },
          exercise,
          generateClip(rig, exercise),
          (definition) => generateClip(rig, definition),
        );
        const detail = JSON.stringify({
          id: exercise.id,
          passed: report.passed,
          failed: report.failed,
          skipped: report.skipped,
          checks: report.checks.map((check) => ({
            id: check.id,
            status: check.status,
            measured: check.measured,
          })),
        });
        expect(report.skipped, detail).toEqual([]);
        expect(report.failed, detail).toEqual([]);
        expect(report.passed, detail).toBe(true);
      }
    },
    180_000,
  );

  it(
    'keeps accepted pull-up and overhead-extension references clean after generator certification',
    () => {
      for (const exercise of [pullUp, overheadExtension]) {
        const report = validateCandidate(
          { rig, character, reference: exercise },
          exercise,
          generateClip(rig, exercise),
          (definition) => generateClip(rig, definition),
        );
        const detail = JSON.stringify({
          id: exercise.id,
          passed: report.passed,
          failed: report.failed,
          skipped: report.skipped,
          checks: report.checks.map((check) => ({
            id: check.id,
            status: check.status,
            measured: check.measured,
          })),
        });
        expect(report.skipped, detail).toEqual([]);
        expect(report.failed, detail).toEqual([]);
        expect(report.passed, detail).toBe(true);
      }
    },
    180_000,
  );

  it(
    'fully certifies a generated loaded hammer curl with clean-body equipment checks',
    async () => {
      const result = await generateExerciseAsync(HAMMER, { rig, library, character });
      const detail = JSON.stringify({
        status: result.status,
        failed: result.report?.failed,
        skipped: result.report?.skipped,
        corrections: result.corrections,
        validations: result.validations,
      });
      expect(result.family?.id).toBe('curl');
      expect(result.status, detail).toBe('passed');
      expect(result.report?.skipped, detail).toEqual([]);
      expect(result.report?.failed, detail).toEqual([]);
      expect(result.report?.checks.every((check) => check.status === 'pass'), detail).toBe(true);
      expect(result.validations).toBeGreaterThan(0);
      expect(result.validations).toBeLessThanOrEqual(40);
      expect(result.corrections.length).toBeLessThanOrEqual(3);
      expect(
        result.report?.checks.find((check) => check.id === 'equipmentClearance')?.status,
      ).toBe('pass');
      expect(
        result.report?.checks.find((check) => check.id === 'armTrunk')?.status,
      ).toBe('pass');
    },
    180_000,
  );
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
