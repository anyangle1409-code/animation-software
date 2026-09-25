import { describe, expect, it } from 'vitest';
import { parsePrompt } from './parse';
import { TEMPO_PROFILES } from './intent';

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

  it('reads a dumbbell Romanian deadlift through the hinge family', () => {
    const parsed = parsePrompt('Create a dumbbell Romanian deadlift with 18 kg dumbbells and slow tempo.');
    expect(parsed.issues).toEqual([]);
    expect(parsed.intent).toMatchObject({
      family: 'hinge',
      equipment: 'dumbbell',
      grip: 'pronated',
      support: 'standing',
      load: 18,
      tempo: { profile: 'slow' },
    });
    expect(parsed.assumptions.join(' ')).toMatch(/pronated grip/);
  });

  it('reads a two-arm dumbbell bent-over row', () => {
    const parsed = parsePrompt('Create a dumbbell bent-over row with 16 kg dumbbells and controlled tempo.');
    expect(parsed.issues).toEqual([]);
    expect(parsed.intent).toMatchObject({
      family: 'row',
      equipment: 'dumbbell',
      grip: 'neutral',
      support: 'standing',
      load: 16,
      tempo: { profile: 'controlled' },
    });
    expect(parsed.assumptions.join(' ')).toMatch(/neutral grip/);
  });

  it('reads a strict pronated pull-up', () => {
    const parsed = parsePrompt('Create a strict pull-up with controlled tempo.');
    expect(parsed.issues).toEqual([]);
    expect(parsed.intent).toMatchObject({
      family: 'vertical_pull',
      equipment: 'bodyweight',
      grip: 'pronated',
      support: 'hanging',
      load: 0,
      tempo: { profile: 'controlled' },
    });
  });

  it('reads lateral and front dumbbell raises', () => {
    const lateral = parsePrompt('Create a lateral raise with 6 kg dumbbells.');
    expect(lateral.issues).toEqual([]);
    expect(lateral.intent).toMatchObject({
      family: 'raise',
      raiseDirection: 'lateral',
      equipment: 'dumbbell',
      grip: 'neutral',
      support: 'standing',
      load: 6,
    });

    const front = parsePrompt('Create a front raise with 7 kg dumbbells and slow tempo.');
    expect(front.issues).toEqual([]);
    expect(front.intent).toMatchObject({
      family: 'raise',
      raiseDirection: 'front',
      grip: 'pronated',
      load: 7,
      tempo: { profile: 'slow' },
    });
  });

  it('reads a standing dumbbell overhead triceps extension', () => {
    const parsed = parsePrompt('Create a standing dumbbell triceps extension with 8 kg dumbbells.');
    expect(parsed.issues).toEqual([]);
    expect(parsed.intent).toMatchObject({
      family: 'extension',
      equipment: 'dumbbell',
      grip: 'neutral',
      support: 'standing',
      load: 8,
    });
  });

  it('reads the standard push-up', () => {
    const parsed = parsePrompt('Create a standard push-up with controlled tempo.');
    expect(parsed.issues).toEqual([]);
    expect(parsed.intent).toMatchObject({
      family: 'horizontal_press',
      equipment: 'bodyweight',
      grip: 'pronated',
      support: 'floor',
      load: 0,
      tempo: { profile: 'controlled' },
    });
  });

  it('reads bodyweight and dumbbell calf raises', () => {
    const bodyweight = parsePrompt('Create a standing calf raise.');
    expect(bodyweight.issues).toEqual([]);
    expect(bodyweight.intent).toMatchObject({
      family: 'calf',
      equipment: 'bodyweight',
      support: 'standing',
      load: 0,
    });

    const loaded = parsePrompt('Create a calf raise with 18 kg dumbbells and slow tempo.');
    expect(loaded.issues).toEqual([]);
    expect(loaded.intent).toMatchObject({
      family: 'calf',
      equipment: 'dumbbell',
      grip: 'neutral',
      support: 'standing',
      load: 18,
      tempo: { profile: 'slow' },
    });
  });

  it('reads crunch and sit-up as one trunk-flexion family', () => {
    expect(parsePrompt('Create a crunch.').intent).toMatchObject({
      family: 'trunk_flexion',
      trunkMotion: 'crunch',
      support: 'floor',
      equipment: 'bodyweight',
    });
    const situp = parsePrompt('Create a sit-up with controlled tempo.');
    expect(situp.issues).toEqual([]);
    expect(situp.intent).toMatchObject({
      family: 'trunk_flexion',
      trunkMotion: 'situp',
      support: 'floor',
      tempo: { profile: 'controlled' },
    });
  });

  it('reads flat dumbbell bench press and fly through the supine family', () => {
    const press = parsePrompt('Create a dumbbell bench press with 20 kg dumbbells and controlled tempo.');
    expect(press.issues).toEqual([]);
    expect(press.intent).toMatchObject({
      family: 'supine',
      supineMotion: 'press',
      equipment: 'dumbbell',
      grip: 'pronated',
      support: 'bench',
      load: 20,
      tempo: { profile: 'controlled' },
    });

    const fly = parsePrompt('Create a dumbbell fly with 10 kg dumbbells.');
    expect(fly.issues).toEqual([]);
    expect(fly.intent).toMatchObject({
      family: 'supine',
      supineMotion: 'fly',
      grip: 'neutral',
      support: 'bench',
      load: 10,
    });
  });

  it("reads a farmer's walk with paired dumbbells", () => {
    const parsed = parsePrompt("Create a farmer's walk with 26 kg dumbbells.");
    expect(parsed.issues).toEqual([]);
    expect(parsed.intent).toMatchObject({
      family: 'carry',
      equipment: 'dumbbell',
      grip: 'neutral',
      support: 'walking',
      load: 26,
      tempo: { profile: 'family' },
    });
  });

  it('fills sensible defaults and says so', () => {
    const parsed = parsePrompt('a dumbbell curl');
    expect(parsed.intent).toMatchObject({ grip: 'supinated', support: 'standing', load: 10, tempo: { profile: 'family' } });
    expect(parsed.assumptions.length).toBeGreaterThanOrEqual(3);
  });

  it('reads grips, loads and tempo in several phrasings', () => {
    expect(parsePrompt('curl, palms facing each other').intent?.grip).toBe('neutral');
    expect(parsePrompt('overhand curl').intent?.grip).toBe('pronated');
    expect(parsePrompt('reverse curl').intent?.grip).toBe('pronated');
    expect(parsePrompt('curl with 25 lb dumbbells').intent?.load).toBe(11.5);
    expect(parsePrompt('slow curl').intent?.tempo).toEqual({ profile: 'slow' });
    expect(parsePrompt('curl, tempo 3-1-2-0').intent?.tempo).toEqual({
      explicit: { eccentric: 3, pauseStretched: 1, concentric: 2, pauseContracted: 0 },
    });
    expect(TEMPO_PROFILES.controlled.eccentric).toBeGreaterThan(TEMPO_PROFILES.controlled.concentric);
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
    expect(blocking('conventional deadlift')).toEqual(['variant']);
    expect(blocking('sumo deadlift')).toContain('variant');
    expect(blocking('good morning')).toEqual(['variant']);
    expect(blocking('single-leg RDL')).toEqual(['variant']);
    expect(blocking('dumbbell row')).toEqual(['variant']);
    expect(blocking('one-arm bent-over row')).toContain('variant');
    expect(blocking('barbell bent-over row')).toContain('variant');
    expect(blocking('seated cable row')).toContain('variant');
    expect(blocking('chin-up')).toEqual(['family']);
    expect(blocking('weighted pull-up')).toContain('variant');
    expect(blocking('cable lateral raise')).toContain('variant');
    expect(blocking('seated front raise')).toContain('variant');
    expect(blocking('cable triceps pushdown')).toEqual(['family']);
    expect(blocking('skull crusher')).toEqual(['family']);
    expect(blocking('incline push-up')).toContain('variant');
    expect(blocking('one-arm push-up')).toContain('variant');
    expect(blocking('seated calf raise')).toContain('variant');
    expect(blocking('single-leg calf raise')).toContain('variant');
    expect(blocking('weighted crunch with 10 kg dumbbell')).toContain('variant');
    expect(blocking('bicycle crunch')).toContain('variant');
    expect(blocking('incline dumbbell bench press')).toEqual(['family']);
    expect(blocking('barbell bench press')).toContain('variant');
    expect(blocking('floor press')).toEqual(['family']);
    expect(blocking('suitcase carry')).toEqual(['family']);
    expect(blocking("farmer's walk with slow tempo")).toContain('tempo');
  });

  it('says why an uncertified incline angle is refused, not just that it is', () => {
    const parsed = parsePrompt('Create an incline dumbbell curl at 30 degrees with 8 kg dumbbells.');
    const issue = parsed.issues.find((issue) => issue.code === 'angle');
    expect(issue?.blocking).toBe(true);
    expect(issue?.message).toMatch(/not certified/);
    expect(issue?.message).toMatch(/45°/);
  });

  it('recognises the rest of the library and declines it with the reason', () => {
    for (const prompt of ['dumbbell bench press', 'leg curl']) {
      const parsed = parsePrompt(prompt);
      expect(parsed.intent, prompt).toBeNull();
      expect(parsed.issues.map((issue) => issue.code), prompt).toEqual(['family']);
    }
    expect(parsePrompt('make me something nice').issues[0].message).toMatch(/No certified movement/);
  });

  it('is deterministic', () => {
    const prompt = 'Create a standing hammer curl with 12 kg dumbbells and controlled tempo.';
    expect(parsePrompt(prompt)).toEqual(parsePrompt(prompt));
  });
});
