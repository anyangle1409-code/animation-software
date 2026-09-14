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

describe('animation workspace authoring state', () => {
  beforeEach(() => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
  });

  it('authors per-joint segment timing through normal undo history', () => {
    const first = useStudio.getState().document.clip.keyframes[0];
    expect(first.jointTiming?.head).toBeUndefined();

    useStudio.getState().setJointTiming(first.id, 'head', {
      delay: 0.2,
      finish: 0.75,
      easing: 'minimumJerk',
    });
    const timing = useStudio.getState().document.clip.keyframes.find((frame) => frame.id === first.id)
      ?.jointTiming?.head;
    expect(timing).toEqual({ delay: 0.2, finish: 0.75, easing: 'minimumJerk' });

    useStudio.getState().undo();
    expect(
      useStudio.getState().document.clip.keyframes.find((frame) => frame.id === first.id)?.jointTiming
        ?.head,
    ).toBeUndefined();
  });

  it('normalises invalid joint timing rather than creating an impossible segment', () => {
    const first = useStudio.getState().document.clip.keyframes[0];
    useStudio.getState().setJointTiming(first.id, 'head', { delay: 2, finish: -1 });
    expect(
      useStudio.getState().document.clip.keyframes.find((frame) => frame.id === first.id)?.jointTiming
        ?.head,
    ).toEqual({ delay: 1, finish: 1 });
  });

  it('stores, rescales and resets a custom playback loop independently of the clip', () => {
    const duration = useStudio.getState().document.clip.duration;
    useStudio.getState().setLoopRange({ start: 2, end: 1 });
    expect(useStudio.getState().loopRange).toEqual({ start: 1, end: 2 });

    useStudio.getState().setDuration(duration * 2);
    expect(useStudio.getState().loopRange?.start).toBeCloseTo(2, 8);
    expect(useStudio.getState().loopRange?.end).toBeCloseTo(4, 8);

    useStudio.getState().loadExercise('dumbbell_bicep_curl');
    expect(useStudio.getState().loopRange).toBeNull();
  });
});
