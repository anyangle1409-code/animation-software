import { beforeEach, describe, expect, it } from 'vitest';
import { useStudio } from './store';

const radians = (degrees: number) => (degrees * Math.PI) / 180;

describe('live grip closure tuning', () => {
  beforeEach(() => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
  });

  it('regenerates the deterministic grip while leaving the authored default available to undo', () => {
    expect(useStudio.getState().document.exercise.hands.closure).toBe(0.85);

    useStudio.getState().setGripClosure(0.5);
    const tuned = useStudio.getState().document;
    expect(tuned.exercise.hands.closure).toBe(0.5);
    expect(tuned.clip.keyframes[0].pose.rotations.index_01_l?.z).toBeCloseTo(radians(78 * 0.5), 8);
    expect(tuned.clip.keyframes[0].pose.rotations.index_01_r?.z).toBeCloseTo(-radians(78 * 0.5), 8);

    useStudio.getState().undo();
    expect(useStudio.getState().document.exercise.hands.closure).toBe(0.85);
  });

  it('clamps editor input to the grip generator range', () => {
    useStudio.getState().setGripClosure(2);
    expect(useStudio.getState().document.exercise.hands.closure).toBe(1);
    useStudio.getState().setGripClosure(-1);
    expect(useStudio.getState().document.exercise.hands.closure).toBe(0);
  });
});
