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

  it('reads a strict bodyweight pull-up through the vertical-pull family', () => {
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
    expect(parsed.assumptions.join(' ')).toMatch(/pronated grip/);
    expect(parsed.assumptions.join(' ')).toMatch(/Hanging/);
  });

  it('reads both certified triceps-extension setups', () => {
    const overhead = parsePrompt('Create an overhead dumbbell triceps extension with 8 kg dumbbells and slow tempo.');
    expect(overhead.issues).toEqual([]);
    expect(overhead.intent).toMatchObject({
      family: 'extension',
      extensionPosition: 'overhead',
      equipment: 'dumbbell',
      grip: 'neutral',
      support: 'standing',
      load: 8,
      tempo: { profile: 'slow' },
    });

    const pushdown = parsePrompt('Create a cable triceps pushdown with controlled tempo.');
    expect(pushdown.issues).toEqual([]);
    expect(pushdown.intent).toMatchObject({
      family: 'extension',
      extensionPosition: 'pushdown',
      equipment: 'cable',
      grip: 'pronated',
      support: 'standing',
      load: 0,
      tempo: { profile: 'controlled' },
    });
  });

  it('reads both certified shoulder-raise directions', () => {
    const lateral = parsePrompt('Create a lateral raise with 7 kg dumbbells and controlled tempo.');
    expect(lateral.issues).toEqual([]);
    expect(lateral.intent).toMatchObject({
      family: 'raise',
      raiseDirection: 'lateral',
      equipment: 'dumbbell',
      grip: 'neutral',
      support: 'standing',
      load: 7,
      tempo: { profile: 'controlled' },
    });

    const front = parsePrompt('Create a front raise with 5 kg dumbbells.');
    expect(front.issues).toEqual([]);
    expect(front.intent).toMatchObject({
      family: 'raise',
      raiseDirection: 'front',
      equipment: 'dumbbell',
      grip: 'pronated',
      support: 'standing',
      load: 5,
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
    expect(blocking('neutral grip pull-up')).toEqual(['grip']);
    expect(blocking('weighted pull-up with 10 kg')).toContain('variant');
    expect(blocking('kipping pull-up')).toEqual(['variant']);
    expect(blocking('chin-up')).toEqual(['family']);
    expect(blocking('lat pulldown')).toEqual(['family']);
    expect(blocking('triceps extension')).toEqual(['variant']);
    expect(blocking('rope triceps pushdown')).toEqual(['variant']);
    expect(blocking('single-arm cable pushdown')).toContain('variant');
    expect(blocking('cable pushdown with 25 kg')).toEqual(['load']);
    expect(blocking('skull crusher')).toEqual(['family']);
    expect(blocking('single-arm lateral raise')).toContain('variant');
    expect(blocking('cable lateral raise')).toContain('variant');
    expect(blocking('plate front raise')).toEqual(['variant']);
    expect(blocking('lateral raise with palms down')).toEqual(['grip']);
    expect(blocking('lateral raise and front raise')).toEqual(['variant']);
  });

  it('says why an uncertified incline angle is refused, not just that it is', () => {
    const parsed = parsePrompt('Create an incline dumbbell curl at 30 degrees with 8 kg dumbbells.');
    const issue = parsed.issues.find((issue) => issue.code === 'angle');
    expect(issue?.blocking).toBe(true);
    expect(issue?.message).toMatch(/not certified/);
    expect(issue?.message).toMatch(/45°/);
  });

  it('recognises the rest of the library and declines it with the reason', () => {
    for (const prompt of ['lateral raise', 'dumbbell bench press', 'leg curl']) {
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
