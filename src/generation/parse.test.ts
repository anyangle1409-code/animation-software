import { describe, expect, it } from 'vitest';
import { parsePrompt } from './parse';
import { TEMPO_PROFILES } from './intent';
import { GENERATOR_FAMILIES } from './families';

const blocking = (prompt: string) =>
  parsePrompt(prompt)
    .issues.filter((issue) => issue.blocking)
    .map((issue) => issue.code);

describe('parsing a request into an ExerciseIntent', () => {
  it('reads the standing hammer curl', () => {
    const parsed = parsePrompt('Create a standing hammer curl with 12 kg dumbbells and controlled tempo.');
    expect(parsed.issues).toEqual([]);
    expect(parsed.intent).toMatchObject({
      family: 'curl',
      grip: 'neutral',
      support: 'standing',
      load: 12,
      equipment: 'dumbbell',
      execution: 'bilateral',
      tempo: { profile: 'controlled' },
    });
  });

  it('reads the incline curl at 45 degrees', () => {
    const parsed = parsePrompt('Create an incline dumbbell curl at 45 degrees with 8 kg dumbbells.');
    expect(parsed.issues).toEqual([]);
    expect(parsed.intent).toMatchObject({ family: 'curl', grip: 'supinated', support: 'incline', benchAngle: 45, load: 8 });
    // The defaults it chose are written down, not silent.
    expect(parsed.assumptions.join(' ')).toMatch(/supinated grip/);
    expect(parsed.assumptions.join(' ')).toMatch(/family's own tempo/);
  });

  it('reads the seated shoulder press', () => {
    const parsed = parsePrompt('Create a seated dumbbell shoulder press with 10 kg dumbbells.');
    expect(parsed.issues).toEqual([]);
    expect(parsed.intent).toMatchObject({ family: 'overhead_press', grip: 'pronated', support: 'seated', load: 10 });
  });

  it('accepts the exact exercise-command form', () => {
    const parsed = parsePrompt('exercise: dumbbell shoulder press');
    expect(parsed.issues).toEqual([]);
    expect(parsed.intent).toMatchObject({
      family: 'overhead_press',
      grip: 'pronated',
      support: 'standing',
      equipment: 'dumbbell',
    });
  });

  it('reads the flat dumbbell bench press and fly as the certified supine family', () => {
    const press = parsePrompt('exercise: dumbbell bench press with 16 kg dumbbells and controlled tempo');
    expect(press.issues).toEqual([]);
    expect(press.intent).toMatchObject({
      family: 'supine',
      equipment: 'dumbbell',
      execution: 'bilateral',
      grip: 'pronated',
      support: 'supine',
      supineMotion: 'press',
      load: 16,
      tempo: { profile: 'controlled' },
    });

    const fly = parsePrompt('exercise: dumbbell fly with 10 kg dumbbells');
    expect(fly.issues).toEqual([]);
    expect(fly.intent).toMatchObject({
      family: 'supine',
      equipment: 'dumbbell',
      execution: 'bilateral',
      grip: 'neutral',
      support: 'supine',
      supineMotion: 'fly',
      load: 10,
    });
  });

  it('reads the standard push-up as the certified horizontal-press family', () => {
    const parsed = parsePrompt('Create a standard push-up with controlled tempo.');
    expect(parsed.issues).toEqual([]);
    expect(parsed.intent).toMatchObject({
      family: 'horizontal_press',
      equipment: 'bodyweight',
      support: 'floor',
      load: 0,
      tempo: { profile: 'controlled' },
    });
    expect(parsed.intent?.grip).toBeUndefined();
  });

  it('reads the bodyweight crunch and sit-up as the certified trunk-flexion family', () => {
    const crunch = parsePrompt('exercise: bodyweight crunch with controlled tempo');
    expect(crunch.issues).toEqual([]);
    expect(crunch.intent).toMatchObject({
      family: 'trunk_flexion',
      equipment: 'bodyweight',
      execution: 'bilateral',
      support: 'floor',
      trunkFlexionMotion: 'crunch',
      load: 0,
      tempo: { profile: 'controlled' },
    });

    const situp = parsePrompt('exercise: sit-up on the floor');
    expect(situp.issues).toEqual([]);
    expect(situp.intent).toMatchObject({
      family: 'trunk_flexion',
      equipment: 'bodyweight',
      support: 'floor',
      trunkFlexionMotion: 'situp',
      load: 0,
    });

    expect(parsePrompt('lying crunch').issues).toEqual([]);
    expect(parsePrompt('lying crunch').intent?.support).toBe('floor');
  });

  it('reads the certified cable woodchop and Pallof press', () => {
    const woodchop = parsePrompt('exercise: cable woodchop with controlled tempo');
    expect(woodchop.issues).toEqual([]);
    expect(woodchop.intent).toMatchObject({
      family: 'rotation',
      equipment: 'cable',
      execution: 'bilateral',
      support: 'standing',
      rotationSetup: 'cable',
      load: 0,
      tempo: { profile: 'controlled' },
    });

    const pallof = parsePrompt('exercise: Pallof press with controlled tempo');
    expect(pallof.issues).toEqual([]);
    expect(pallof.intent).toMatchObject({
      family: 'anti_rotation',
      equipment: 'cable',
      execution: 'bilateral',
      support: 'standing',
      load: 0,
      tempo: { profile: 'controlled' },
    });
  });

  it('reads the seated bodyweight Russian twist', () => {
    const parsed = parsePrompt('exercise: Russian twist with controlled tempo');
    expect(parsed.issues).toEqual([]);
    expect(parsed.intent).toMatchObject({
      family: 'rotation',
      equipment: 'bodyweight',
      execution: 'bilateral',
      support: 'seated',
      load: 0,
      tempo: { profile: 'controlled' },
    });
    expect(parsePrompt('seated Russian twist on the floor').issues).toEqual([]);
  });

  it("reads the bilateral dumbbell farmer's walk", () => {
    const parsed = parsePrompt("exercise: farmer's walk with 24 kg dumbbells");
    expect(parsed.issues).toEqual([]);
    expect(parsed.intent).toMatchObject({
      family: 'carry',
      equipment: 'dumbbell',
      execution: 'bilateral',
      grip: 'neutral',
      support: 'standing',
      load: 24,
      tempo: { profile: 'family' },
    });
  });

  it('reads the bodyweight squat', () => {
    const parsed = parsePrompt('Create a bodyweight squat with a slow tempo.');
    expect(parsed.issues).toEqual([]);
    expect(parsed.intent).toMatchObject({
      family: 'squat',
      equipment: 'bodyweight',
      support: 'standing',
      load: 0,
      tempo: { profile: 'slow' },
    });
    expect(parsed.intent?.grip).toBeUndefined();
  });

  it('reads the bodyweight standing calf raise', () => {
    const parsed = parsePrompt('Create a standing calf raise with a slow tempo.');
    expect(parsed.issues).toEqual([]);
    expect(parsed.intent).toMatchObject({
      family: 'calf',
      equipment: 'bodyweight',
      support: 'standing',
      load: 0,
      tempo: { profile: 'slow' },
    });
  });

  it('reads the three lunge variants', () => {
    expect(parsePrompt('Create a split squat.').intent).toMatchObject({ family: 'lunge', step: undefined });
    expect(parsePrompt('Create a forward lunge.').intent).toMatchObject({ family: 'lunge', step: 'forward' });
    const parsed = parsePrompt('Create a reverse lunge with controlled tempo.');
    expect(parsed.issues).toEqual([]);
    expect(parsed.intent).toMatchObject({
      family: 'lunge',
      equipment: 'bodyweight',
      step: 'back',
      support: 'standing',
      load: 0,
      tempo: { profile: 'controlled' },
    });
  });

  it('defaults a bare lunge to stepping forward, and says so', () => {
    const parsed = parsePrompt('Create a lunge.');
    expect(parsed.issues).toEqual([]);
    expect(parsed.intent).toMatchObject({ family: 'lunge', step: 'forward' });
    expect(parsed.assumptions.join(' ')).toMatch(/forward lunge/);
  });

  it('blocks ambiguous free-weight wording instead of silently assuming dumbbells', () => {
    expect(blocking('exercise: free weights shoulder press')).toContain('equipment');
    expect(blocking('exercise: free-weight Romanian deadlift')).toContain('equipment');
  });

  it('blocks unilateral arm/hand wording instead of silently substituting bilateral motion', () => {
    expect(blocking('exercise: one-handed dumbbell curl')).toContain('execution');
    expect(blocking("exercise: left-hand farmer's walk")).toContain('execution');
    expect(blocking('exercise: right-arm dumbbell shoulder press')).toContain('execution');
  });

  it('recognises common equipment spellings so defaults cannot hide the requested implement', () => {
    expect(parsePrompt('exercise: dumbell calf raise with 14 kg').issues.filter((issue) => issue.blocking)).toEqual([]);
    expect(parsePrompt('exercise: dumbell calf raise with 14 kg').intent?.equipment).toBe('dumbbell');

    expect(blocking('exercise: barbel shoulder press')).toContain('equipment');
    expect(blocking('exercise: bar bell shoulder press')).toContain('equipment');
    expect(blocking('exercise: body weight shoulder press')).toContain('equipment');
    expect(blocking('exercise: kettle bell shoulder press')).toContain('equipment');
  });

  it('normalises mobile punctuation before deterministic parsing', () => {
    const cases = [
      ['exercise: farmer’s walk', 'carry'],
      ['exercise: push‑up', 'horizontal_press'],
      ['exercise: sit‑up', 'trunk_flexion'],
      ['exercise: bent‑over dumbbell row', 'row'],
      ['exercise: Romanian dead‑lift', 'hinge'],
      ['exercise: cable triceps press‑down', 'extension'],
    ] as const;

    for (const [prompt, family] of cases) {
      const parsed = parsePrompt(prompt);
      expect(parsed.issues.filter((issue) => issue.blocking), prompt).toEqual([]);
      expect(parsed.intent?.family, prompt).toBe(family);
    }
  });

  it('accepts safe naming aliases without changing biomechanics', () => {
    const aliases = [
      ['exercise: Romanian dead lift', 'hinge', 'dumbbell_romanian_deadlift'],
      ["exercise: farmer's carries", 'carry', 'farmers_walk'],
      ['exercise: heel raise', 'calf', 'standing_calf_raise'],
      ['exercise: cable triceps pressdown', 'extension', 'cable_triceps_pushdown'],
      ['exercise: tricep press down', 'extension', 'cable_triceps_pushdown'],
      ['exercise: press up', 'horizontal_press', 'push_up'],
      ['exercise: RDL', 'hinge', 'dumbbell_romanian_deadlift'],
      ['exercise: OHP', 'overhead_press', 'dumbbell_shoulder_press'],
    ] as const;

    for (const [prompt, familyId, reference] of aliases) {
      const parsed = parsePrompt(prompt);
      expect(parsed.issues.filter((issue) => issue.blocking), prompt).toEqual([]);
      expect(parsed.intent?.family, prompt).toBe(familyId);
      expect(GENERATOR_FAMILIES.find((family) => family.id === familyId)?.reference(parsed.intent!), prompt)
        .toBe(reference);
    }
  });

  it('fills sensible defaults and says so', () => {
    const parsed = parsePrompt('a dumbbell curl');
    expect(parsed.intent).toMatchObject({ grip: 'supinated', support: 'standing', load: 10, tempo: { profile: 'family' } });
    expect(parsed.assumptions.length).toBeGreaterThanOrEqual(3);
  });

  it('does not silently replace unsupported support, stance or grip-width modifiers with family defaults', () => {
    expect(blocking('exercise: kneeling dumbbell shoulder press')).toEqual(['support']);
    expect(blocking('exercise: half-kneeling dumbbell curl')).toEqual(['support']);
    expect(blocking('exercise: quadruped dumbbell row')).toEqual(['support']);
    expect(blocking('exercise: pull-up from all fours')).toEqual(['support']);
    expect(blocking('exercise: wide stance squat')).toEqual(['variant']);
    expect(blocking('exercise: narrow stance Romanian deadlift')).toEqual(['variant']);
    expect(blocking("exercise: farmer's walk feet together")).toEqual(['variant']);
    expect(blocking('exercise: wide grip pull-up')).toEqual(['grip']);
    expect(blocking('exercise: push-up hands close')).toEqual(['grip']);
  });

  it('does not invert negated movement, grip, support or tempo wording', () => {
    expect(blocking('exercise: not a squat')).toEqual(['family']);
    expect(blocking('exercise: no pull-up')).toEqual(['family']);
    expect(blocking("exercise: without a farmer's walk")).toEqual(['family']);
    expect(blocking('exercise: not dumbbell bench press')).toEqual(['family']);
    expect(blocking('exercise: curl not underhand')).toEqual(['grip']);
    expect(blocking('exercise: push-up not palms down')).toEqual(['grip']);
    expect(blocking('exercise: shoulder press not seated')).toEqual(['support']);
    expect(blocking('exercise: incline curl not inclined')).toEqual(['support']);
    expect(blocking('exercise: dumbbell curl not slow')).toEqual(['tempo']);
    expect(blocking('exercise: shoulder press not fast')).toEqual(['tempo']);
    expect(blocking('exercise: squat not controlled')).toEqual(['tempo']);
  });

  it('blocks isometric, pause, hold and eccentric-emphasis wording that is not encoded by the family clip', () => {
    expect(blocking('exercise: isometric squat')).toEqual(['variant']);
    expect(blocking('exercise: paused dumbbell bench press')).toEqual(['variant']);
    expect(blocking('exercise: dumbbell curl hold at the top')).toEqual(['variant']);
    expect(blocking('exercise: negative pull-up')).toEqual(['variant']);
    expect(blocking('exercise: eccentric calf raise')).toEqual(['variant']);
    expect(parsePrompt('exercise: dumbbell curl tempo 3-1-2-0').issues.filter((issue) => issue.blocking)).toEqual([]);
  });

  it('does not replace generic weighted bodyweight requests with the plain family default', () => {
    const weightedCases = [
      'exercise: weighted push-up',
      'exercise: weighted squat',
      'exercise: loaded sit-up',
      'exercise: Russian twist holding weights',
    ];
    for (const prompt of weightedCases) {
      const codes = blocking(prompt);
      expect(codes.length, prompt).toBeGreaterThan(0);
      expect(codes.some((code) => code === 'load' || code === 'variant' || code === 'equipment'), prompt).toBe(true);
    }

    expect(parsePrompt('exercise: bodyweight squat').issues.filter((issue) => issue.blocking)).toEqual([]);
    expect(parsePrompt('exercise: push-up').issues.filter((issue) => issue.blocking)).toEqual([]);
  });

  it('does not replace qualitative load requests with arbitrary family defaults', () => {
    expect(blocking('exercise: dumbbell curl with heavy dumbbells')).toContain('load');
    expect(blocking('exercise: shoulder press with moderate load')).toContain('load');
    expect(blocking('exercise: Pallof press with light cable resistance')).toContain('load');

    expect(parsePrompt('exercise: dumbbell curl with heavy 12 kg dumbbells').issues.filter((issue) => issue.blocking)).toEqual([]);
    expect(parsePrompt('exercise: dumbbell curl').issues.filter((issue) => issue.blocking)).toEqual([]);
  });

  it('does not treat negated equipment wording as permission to use the family default', () => {
    expect(blocking('exercise: shoulder press without dumbbells')).toContain('equipment');
    expect(blocking('exercise: dumbbell curl with no weights')).toContain('equipment');
    expect(blocking('exercise: unweighted dumbbell Romanian deadlift')).toContain('equipment');
    expect(blocking("exercise: empty-handed farmer's walk")).toContain('equipment');
    expect(blocking('exercise: Pallof press without cable')).toContain('equipment');

    expect(parsePrompt('exercise: shoulder press with dumbbells').issues.filter((issue) => issue.blocking)).toEqual([]);
    expect(parsePrompt('exercise: Pallof press with cable').issues.filter((issue) => issue.blocking)).toEqual([]);
  });

  it('does not turn an explicit single dumbbell into a paired-dumbbell exercise', () => {
    expect(blocking('exercise: shoulder press with one dumbbell')).toContain('equipment');
    expect(blocking('exercise: single dumbbell Romanian deadlift')).toContain('equipment');
    expect(blocking("exercise: farmer's walk with 1 dumbbell")).toContain('equipment');

    expect(parsePrompt('exercise: curl with one dumbbell per hand').issues.filter((issue) => issue.blocking)).toEqual([]);
    expect(parsePrompt('exercise: shoulder press with one dumbbell in each hand').issues.filter((issue) => issue.blocking)).toEqual([]);
    expect(parsePrompt('exercise: dumbbell curl with two dumbbells').issues.filter((issue) => issue.blocking)).toEqual([]);
    expect(blocking('exercise: dumbbell curl with three dumbbells')).toContain('equipment');
    expect(blocking('exercise: shoulder press with 4 dumbbells')).toContain('equipment');
    expect(blocking('exercise: dumbbell row with two dumbbells per hand')).toContain('equipment');
  });

  it('does not ignore written carry distance prescriptions', () => {
    expect(blocking("exercise: farmer's walk for ten metres")).toContain('variant');
    expect(blocking("exercise: farmer's walk for twenty-five meters")).toContain('variant');
  });

  it('does not reinterpret total dumbbell load as a per-hand load', () => {
    expect(blocking('exercise: dumbbell curl with 20 kg total')).toContain('load');
    expect(blocking('exercise: dumbbell shoulder press with ten kg combined')).toContain('load');
    expect(blocking('exercise: dumbbell row with 24 kg between both hands')).toContain('load');
    expect(blocking('exercise: dumbbell curl with combined load 20 kg')).toContain('load');

    expect(parsePrompt('exercise: dumbbell curl with 10 kg per hand').issues.filter((issue) => issue.blocking)).toEqual([]);
    expect(parsePrompt('exercise: dumbbell curl with ten kg each').issues.filter((issue) => issue.blocking)).toEqual([]);
    expect(parsePrompt('exercise: dumbbell curl with 10 kg combined with slow tempo').issues.filter((issue) => issue.blocking)).toEqual([]);
  });

  it('reads grips, loads and tempo in several phrasings', () => {
    expect(parsePrompt('curl, palms facing each other').intent?.grip).toBe('neutral');
    expect(parsePrompt('overhand curl').intent?.grip).toBe('pronated');
    expect(parsePrompt('reverse curl').intent?.grip).toBe('pronated');
    expect(parsePrompt('curl with 25 lb dumbbells').intent?.load).toBe(11.5);
    expect(parsePrompt('curl with ten kg dumbbells').intent?.load).toBe(10);
    expect(parsePrompt('curl with ten point five kg dumbbells').intent?.load).toBe(10.5);
    expect(parsePrompt('curl with 10,5 kg dumbbells').intent?.load).toBe(10.5);
    expect(parsePrompt('curl with twenty-five pounds dumbbells').intent?.load).toBe(11.5);
    expect(parsePrompt('curl with one hundred kg dumbbells').issues.map((issue) => issue.code)).toContain('load');
    expect(parsePrompt('incline curl at forty-five degrees').intent?.benchAngle).toBe(45);
    expect(parsePrompt('incline curl at forty-five point five degrees').intent?.benchAngle).toBe(45.5);
    expect(blocking('incline curl at forty-five point five degrees')).toEqual(['angle']);
    expect(parsePrompt('incline curl at 45,5 degrees').intent?.benchAngle).toBe(45.5);
    expect(blocking('incline curl at 45,5 degrees')).toEqual(['angle']);
    expect(blocking('incline curl at thirty degrees')).toEqual(['angle']);
    expect(parsePrompt('slow curl').intent?.tempo).toEqual({ profile: 'slow' });
    expect(parsePrompt('curl, tempo 3-1-2-0').intent?.tempo).toEqual({
      explicit: { eccentric: 3, pauseStretched: 1, concentric: 2, pauseContracted: 0 },
    });
    expect(parsePrompt('curl, tempo 3010').intent?.tempo).toEqual({
      explicit: { eccentric: 3, pauseStretched: 0, concentric: 1, pauseContracted: 0 },
    });
    expect(TEMPO_PROFILES.controlled.eccentric).toBeGreaterThan(TEMPO_PROFILES.controlled.concentric);
  });

  it('does not ignore explicit left/right lower-limb execution wording', () => {
    expect(blocking('exercise: forward lunge with right leg')).toEqual(['execution']);
    expect(blocking('exercise: left-foot split squat')).toEqual(['execution']);
    expect(blocking('exercise: calf raise on the right foot')).toEqual(['execution']);
    expect(blocking('exercise: Romanian deadlift using left leg')).toEqual(['execution']);
  });

  it('does not silently discard malformed or unsupported tempo directives', () => {
    expect(blocking('exercise: dumbbell curl tempo 30x0')).toEqual(['tempo']);
    expect(blocking('exercise: dumbbell curl tempo 3-1-2')).toEqual(['tempo']);
    expect(blocking('exercise: dumbbell curl cadence 3-1-2-0')).toEqual(['tempo']);
    expect(blocking('exercise: dumbbell curl tempo 0000')).toEqual(['tempo']);
    expect(blocking('exercise: dumbbell curl tempo 0-1-2-0')).toEqual(['tempo']);
    expect(parsePrompt('exercise: dumbbell curl tempo 3-0-1-0').issues.filter((issue) => issue.blocking)).toEqual([]);
    expect(parsePrompt('exercise: dumbbell curl controlled tempo').issues.filter((issue) => issue.blocking)).toEqual([]);
    expect(parsePrompt('exercise: dumbbell curl slow cadence').issues.filter((issue) => issue.blocking)).toEqual([]);
  });

  it('does not silently drop phase-specific timing that the clip cannot encode independently', () => {
    expect(blocking('exercise: dumbbell curl 3-second lowering')).toEqual(['tempo']);
    expect(blocking('exercise: dumbbell curl lowering for three seconds')).toEqual(['tempo']);
    expect(blocking('exercise: shoulder press 2 sec up')).toEqual(['tempo']);
    expect(parsePrompt('exercise: dumbbell curl tempo 3-0-1-0').issues.filter((issue) => issue.blocking)).toEqual([]);
  });

  it('blocks set, repetition-count and workout-programming prescriptions that have no output field yet', () => {
    expect(blocking('exercise: dumbbell curl for 10 reps')).toEqual(['programming']);
    expect(blocking('exercise: 3 sets dumbbell shoulder press')).toEqual(['programming']);
    expect(blocking('exercise: ten reps dumbbell calf raise')).toEqual(['programming']);
    expect(blocking('exercise: squat for 30 seconds')).toEqual(['programming']);
    expect(blocking('exercise: dumbbell curl 3x10')).toEqual(['programming']);
    expect(blocking('exercise: squat 5×5')).toEqual(['programming']);
    expect(blocking('exercise: dumbbell curl AMRAP')).toEqual(['programming']);
    expect(blocking('exercise: push-up to failure')).toEqual(['programming']);
    expect(blocking('exercise: squat RPE 8')).toEqual(['programming']);
    expect(blocking('exercise: dumbbell row RIR 2')).toEqual(['programming']);
    expect(blocking('exercise: shoulder press rest 60 seconds')).toEqual(['programming']);
    expect(blocking('exercise: squat 3 rounds')).toEqual(['programming']);
    expect(blocking('exercise: dumbbell curl sets of ten')).toEqual(['programming']);
    expect(blocking('exercise: dumbbell curl drop set')).toEqual(['programming']);
    expect(blocking('exercise: shoulder press superset')).toEqual(['programming']);
  });

  it('blocks rep-style modifiers that would otherwise be silently replaced by a full repetition', () => {
    expect(blocking('exercise: half-rep dumbbell curl')).toEqual(['variant']);
    expect(blocking('exercise: partial squat')).toEqual(['variant']);
    expect(blocking('exercise: top half dumbbell bench press')).toEqual(['variant']);
    expect(blocking('exercise: eccentric-only pull-up')).toEqual(['variant']);
    expect(blocking('exercise: 1.5 reps dumbbell shoulder press')).toEqual(['variant']);
  });

  it('asks only when the answer changes the exercise', () => {
    // Contradictions.
    expect(blocking('hammer curl with palms up')).toEqual(['grip']);
    expect(blocking('curl with 10 kg and 12 kg')).toEqual(['load']);
    // Things no certified family does, declined rather than approximated.
    expect(blocking('alternating hammer curl')).toEqual(['execution']);
    // The bench adjusts (`EquipmentInstance.backAngle`), but only 45° has
    // actually passed every check on the production character — 30° and 60°
    // were both tried and refused (`families.ts`'s `CERTIFIED_INCLINE_ANGLES`,
    // `generate.test.ts`'s production-character tests). An angle the bench
    // can be built at is still refused if no candidate there is certified.
    expect(blocking('incline curl at 30 degrees')).toEqual(['angle']);
    expect(blocking('incline curl at 60 degrees')).toEqual(['angle']);
    expect(blocking('seated curl')).toEqual(['support']);
    expect(blocking('barbell curl')).toEqual(['equipment']);
    expect(blocking('preacher curl')).toEqual(['variant']);
    expect(blocking('neutral grip shoulder press')).toEqual(['grip']);
    expect(blocking('arnold press')).toEqual(['family']);
    // Squat and lunge names that share a word with a certified family but are
    // not built by it, declined with the reason rather than approximated.
    expect(blocking('goblet squat')).toEqual(['variant']);
    expect(blocking('pistol squat')).toEqual(['variant']);
    expect(blocking('walking lunge')).toEqual(['variant']);
    expect(blocking('a squat with 20 kg dumbbells')).toEqual(['equipment', 'load']);
    expect(blocking('a split squat and a forward lunge')).toEqual(['variant']);
    expect(blocking('diamond push-up')).toEqual(['variant']);
    expect(blocking('knee push-up')).toEqual(['variant']);
    expect(blocking('incline push-up')).toEqual(['support']);
    expect(blocking('push-up with feet elevated')).toEqual(['variant']);
    expect(blocking('push-up with hands on a bench')).toEqual(['variant']);
    expect(blocking('elevated push-up')).toEqual(['variant']);
    expect(blocking('push-up with 10 kg dumbbells')).toEqual(['equipment', 'load']);
    expect(blocking('single-leg calf raise')).toEqual(['variant']);
    expect(blocking('seated calf raise')).toEqual(['support']);
    expect(blocking('weighted calf raise')).toEqual(['variant']);
    expect(blocking('dumbbell calf raise with palms down')).toEqual(['grip']);
    expect(blocking('single-leg RDL')).toEqual(['variant']);
    expect(blocking('barbell Romanian deadlift')).toEqual(['equipment']);
    expect(blocking('neutral grip Romanian deadlift')).toEqual(['grip']);
    expect(blocking('conventional deadlift')).toEqual(['family']);
    expect(blocking('good morning')).toEqual(['family']);
    expect(blocking('one-arm dumbbell row')).toContain('variant');
    expect(blocking('pronated bent-over row')).toContain('grip');
    expect(blocking('barbell bent-over row')).toContain('equipment');
    expect(blocking('Pendlay row')).toEqual(['family']);
    expect(blocking('single-arm lateral raise')).toContain('variant');
    expect(blocking('pronated lateral raise')).toContain('grip');
    expect(blocking('neutral grip front raise')).toContain('grip');
    expect(blocking('rear delt raise')).toEqual(['family']);
    expect(blocking('chin-up')).toEqual(['family']);
    expect(blocking('weighted pull-up')).toContain('variant');
    expect(blocking('neutral grip pull-up')).toContain('variant');
    expect(blocking('chest-to-bar pull-up')).toContain('variant');
    expect(blocking('L-sit pull-up')).toContain('variant');
    expect(blocking('commando pull-up')).toContain('variant');
    expect(blocking('single-arm overhead triceps extension')).toContain('variant');
    expect(blocking('rope cable pushdown')).toContain('variant');
    expect(blocking('single-arm cable pushdown')).toContain('variant');
    expect(blocking('underhand cable pushdown')).toContain('variant');
    expect(blocking('dumbbell cable pushdown')).toEqual(['equipment']);
    expect(blocking('cable pushdown with 10 kg')).toEqual(['load']);
    expect(blocking('barbell bench press')).toEqual(['equipment']);
    expect(blocking('incline dumbbell bench press')).toEqual(['support']);
    expect(blocking('single-arm dumbbell bench press')).toEqual(['execution']);
    expect(blocking('dumbbell fly with palms down')).toEqual(['grip']);
    expect(blocking('reverse dumbbell fly')).toContain('variant');
    expect(blocking('floor press')).toEqual(['family']);
    expect(blocking('bicycle crunch')).toEqual(['variant']);
    expect(blocking('reverse crunch')).toEqual(['variant']);
    expect(blocking('weighted crunch')).toEqual(['variant']);
    expect(blocking('decline sit-up')).toEqual(['variant']);
    expect(blocking('standing crunch')).toEqual(['support']);
    expect(blocking('crunch with 10 kg')).toEqual(['load']);
    expect(blocking('crunch with palms down')).toEqual(['grip']);
    expect(blocking("single-arm farmer's walk")).toEqual(['execution']);
    expect(blocking("barbell farmer's walk")).toEqual(['equipment']);
    expect(blocking("seated farmer's walk")).toEqual(['support']);
    expect(blocking("farmer's walk with palms down")).toEqual(['grip']);
    expect(blocking("farmer's walk with controlled tempo")).toEqual(['tempo']);
    expect(blocking("farmer's walk for 20 m")).toEqual(['variant']);
    expect(blocking('suitcase carry')).toEqual(['family']);
    expect(blocking('weighted Russian twist')).toEqual(['variant']);
    expect(blocking('Russian twist with a medicine ball')).toEqual(['variant']);
    expect(blocking('Russian twist with feet raised')).toEqual(['variant']);
    expect(blocking('standing Russian twist')).toEqual(['support']);
    expect(blocking('Russian twist with 10 kg')).toEqual(['load']);
    expect(blocking('Russian twist with palms down')).toEqual(['grip']);
    expect(blocking('Russian twist at 30 degrees')).toEqual(['angle']);
    expect(blocking('dumbbell cable woodchop')).toEqual(['equipment']);
    expect(blocking('cable woodchop with 10 kg')).toEqual(['load']);
    expect(blocking('seated cable woodchop')).toEqual(['support']);
    expect(blocking('low-to-high cable woodchop')).toEqual(['variant']);
    expect(blocking('left-side cable woodchop')).toEqual(['variant']);
    expect(blocking('cable woodchop with palms down')).toEqual(['grip']);
    expect(blocking('dumbbell Pallof press')).toEqual(['equipment']);
    expect(blocking('Pallof press with 10 kg')).toEqual(['load']);
    expect(blocking('kneeling Pallof press')).toEqual(['support']);
    expect(blocking('right-side Pallof press')).toEqual(['variant']);
    expect(blocking('single-arm Pallof press')).toEqual(['execution']);
    expect(blocking('Pallof press with neutral grip')).toEqual(['grip']);
  });

  it('says why an uncertified incline angle is refused, not just that it is', () => {
    const parsed = parsePrompt('Create an incline dumbbell curl at 30 degrees with 8 kg dumbbells.');
    const issue = parsed.issues.find((issue) => issue.code === 'angle');
    expect(issue?.blocking).toBe(true);
    expect(issue?.message).toMatch(/not certified/);
    expect(issue?.message).toMatch(/45°/);
  });

  it('recognises the rest of the library and declines it with the reason', () => {
    for (const prompt of ['upright row', 'rear delt raise', 'chin-up', 'leg curl']) {
      const parsed = parsePrompt(prompt);
      expect(parsed.intent, prompt).toBeNull();
      expect(parsed.issues.map((issue) => issue.code), prompt).toEqual(['family']);
    }
    expect(parsePrompt('make me something nice').issues[0].message).toMatch(/No certified movement/);
  });

  it('reads the loaded calf raise and cable pushdown from their existing families', () => {
    const calf = parsePrompt('exercise: dumbbell calf raise with 14 kg dumbbells and controlled tempo');
    expect(calf.issues).toEqual([]);
    expect(calf.intent).toMatchObject({
      family: 'calf',
      equipment: 'dumbbell',
      execution: 'bilateral',
      grip: 'neutral',
      support: 'standing',
      load: 14,
      tempo: { profile: 'controlled' },
    });

    const pushdown = parsePrompt('exercise: cable triceps pushdown with controlled tempo');
    expect(pushdown.issues).toEqual([]);
    expect(pushdown.intent).toMatchObject({
      family: 'extension',
      equipment: 'cable',
      execution: 'bilateral',
      grip: 'pronated',
      support: 'standing',
      load: 0,
      tempo: { profile: 'controlled' },
    });
  });

  it('parses only the certified Romanian-deadlift hinge variant', () => {
    const parsed = parsePrompt('Create a dumbbell Romanian deadlift with 20 kg dumbbells and controlled tempo.');
    expect(parsed.issues.filter((issue) => issue.blocking)).toEqual([]);
    expect(parsed.intent).toMatchObject({
      family: 'hinge',
      equipment: 'dumbbell',
      execution: 'bilateral',
      grip: 'pronated',
      support: 'standing',
      load: 20,
      tempo: { profile: 'controlled' },
    });
  });

  it('parses only the certified bent-over row variant', () => {
    const parsed = parsePrompt('exercise: dumbbell bent-over row with 16 kg dumbbells and controlled tempo');
    expect(parsed.issues.filter((issue) => issue.blocking)).toEqual([]);
    expect(parsed.intent).toMatchObject({
      family: 'row',
      equipment: 'dumbbell',
      execution: 'bilateral',
      grip: 'neutral',
      support: 'standing',
      load: 16,
      tempo: { profile: 'controlled' },
    });
  });

  it('parses the certified lateral and front raise directions', () => {
    const lateral = parsePrompt('exercise: dumbbell lateral raise with 7 kg dumbbells');
    expect(lateral.issues.filter((issue) => issue.blocking)).toEqual([]);
    expect(lateral.intent).toMatchObject({
      family: 'raise',
      equipment: 'dumbbell',
      grip: 'neutral',
      support: 'standing',
      raiseDirection: 'lateral',
      load: 7,
    });

    const front = parsePrompt('exercise: dumbbell front raise with 5 kg dumbbells');
    expect(front.issues.filter((issue) => issue.blocking)).toEqual([]);
    expect(front.intent).toMatchObject({
      family: 'raise',
      equipment: 'dumbbell',
      grip: 'pronated',
      support: 'standing',
      raiseDirection: 'front',
      load: 5,
    });
  });

  it('parses only the certified strict pull-up and overhead extension', () => {
    const pull = parsePrompt('exercise: strict pull-up with controlled tempo');
    expect(pull.issues.filter((issue) => issue.blocking)).toEqual([]);
    expect(pull.intent).toMatchObject({
      family: 'vertical_pull',
      equipment: 'bodyweight',
      grip: 'pronated',
      support: 'hanging',
      load: 0,
      tempo: { profile: 'controlled' },
    });

    const extension = parsePrompt('exercise: dumbbell overhead triceps extension with 9 kg dumbbells');
    expect(extension.issues.filter((issue) => issue.blocking)).toEqual([]);
    expect(extension.intent).toMatchObject({
      family: 'extension',
      equipment: 'dumbbell',
      grip: 'neutral',
      support: 'standing',
      load: 9,
    });
  });

  it('is deterministic', () => {
    const prompt = 'Create a standing hammer curl with 12 kg dumbbells and controlled tempo.';
    expect(parsePrompt(prompt)).toEqual(parsePrompt(prompt));
  });
});
