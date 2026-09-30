import { beforeEach, describe, expect, it } from 'vitest';
import { getExercise } from '../exercises/library';
import type { GenerationResult } from '../generation/generate';
import { parsePrompt } from '../generation/parse';
import {
  generationStore,
  type Candidate,
} from './generationStoreCore';
import { studioStore } from './storeCore';

const PROMPT = 'Create a standing hammer curl with 12 kg dumbbells and controlled tempo.';
const SQUAT = 'Create a bodyweight squat with a slow tempo.';

const candidate = (
  key: string,
  status: GenerationResult['status'] = 'passed',
  withExercise = true,
): Candidate => ({
  key,
  prompt: PROMPT,
  approved: false,
  result: {
    parsed: parsePrompt(PROMPT),
    status,
    ...(withExercise ? { exercise: getExercise('dumbbell_hammer_curl') } : {}),
    attempts: [],
    corrections: [],
    validations: 1,
  },
});

beforeEach(() => {
  studioStore.getState().loadExercise('air_squat');
  generationStore.setState({
    prompt: PROMPT,
    running: false,
    progress: [],
    candidates: [],
    selected: null,
    validationCharacter: null,
  });
});

describe('framework-neutral generation session store', () => {
  it('previews through the Studio document, approves passed candidates and discards session state', () => {
    const entry = candidate('candidate_test');
    generationStore.setState({ candidates: [entry] });

    generationStore.getState().preview(entry.key);
    expect(generationStore.getState().selected).toBe(entry.key);
    expect(studioStore.getState().document.exercise.id).toBe('dumbbell_hammer_curl');

    generationStore.getState().approve(entry.key);
    expect(generationStore.getState().candidates[0]?.approved).toBe(true);

    generationStore.getState().discard(entry.key);
    expect(generationStore.getState().candidates).toEqual([]);
    expect(generationStore.getState().selected).toBeNull();
  });

  it('does not preview candidates without an exercise or approve non-passing candidates', () => {
    const blocked = candidate('candidate_blocked', 'blocked', false);
    const failed = candidate('candidate_failed', 'failed', true);
    generationStore.setState({ candidates: [blocked, failed] });

    const beforeExercise = studioStore.getState().document.exercise.id;
    generationStore.getState().preview(blocked.key);
    expect(generationStore.getState().selected).toBeNull();
    expect(studioStore.getState().document.exercise.id).toBe(beforeExercise);

    generationStore.getState().approve(failed.key);
    expect(
      generationStore.getState().candidates.find((entry) => entry.key === failed.key)?.approved,
    ).toBe(false);
  });
  it(
    'fully validates supported prompts on the clean first-party fallback',
    async () => {
      generationStore.getState().setPrompt(SQUAT);
      await generationStore.getState().generate();

      const state = generationStore.getState();
      expect(state.running).toBe(false);
      expect(state.validationCharacter).toBe('Home Gym PT clean scaffold');
      expect(state.candidates).toHaveLength(1);
      expect(state.candidates[0]?.result.status).toBe('passed');
      expect(state.candidates[0]?.result.report?.skipped).toEqual([]);
      expect(state.candidates[0]?.result.report?.failed).toEqual([]);
      expect(state.candidates[0]?.result.report?.character).toBe(
        'Home Gym PT clean scaffold',
      );
      expect(studioStore.getState().document.exercise.id).toMatch(/^generated_/);
    },
    120_000,
  );

});
