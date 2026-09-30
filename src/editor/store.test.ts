import { beforeEach, describe, expect, it } from 'vitest';
import { HgVec3 } from '../core/linearMath';
import { resolveFrame } from '../animation/pipeline';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import { studioStore } from './storeCore';

const radians = (degrees: number) => (degrees * Math.PI) / 180;

describe('live grip closure tuning', () => {
  beforeEach(() => {
    studioStore.getState().loadExercise('dumbbell_bicep_curl');
  });

  it('regenerates the deterministic grip while leaving the authored default available to undo', () => {
    expect(studioStore.getState().document.exercise.hands.closure).toBe(0.85);

    studioStore.getState().setGripClosure(0.5);
    const tuned = studioStore.getState().document;
    expect(tuned.exercise.hands.closure).toBe(0.5);
    expect(tuned.clip.keyframes[0].pose.rotations.index_01_l?.z).toBeCloseTo(radians(78 * 0.5), 8);
    expect(tuned.clip.keyframes[0].pose.rotations.index_01_r?.z).toBeCloseTo(-radians(78 * 0.5), 8);

    studioStore.getState().undo();
    expect(studioStore.getState().document.exercise.hands.closure).toBe(0.85);
  });

  it('clamps editor input to the grip generator range', () => {
    studioStore.getState().setGripClosure(2);
    expect(studioStore.getState().document.exercise.hands.closure).toBe(1);
    studioStore.getState().setGripClosure(-1);
    expect(studioStore.getState().document.exercise.hands.closure).toBe(0);
  });
});

describe('animation workspace authoring state', () => {
  beforeEach(() => {
    studioStore.getState().loadExercise('dumbbell_bicep_curl');
  });

  it('authors per-joint segment timing through normal undo history', () => {
    const first = studioStore.getState().document.clip.keyframes[0];
    expect(first.jointTiming?.head).toBeUndefined();

    studioStore.getState().setJointTiming(first.id, 'head', {
      delay: 0.2,
      finish: 0.75,
      easing: 'minimumJerk',
    });
    const timing = studioStore.getState().document.clip.keyframes.find((frame) => frame.id === first.id)
      ?.jointTiming?.head;
    expect(timing).toEqual({ delay: 0.2, finish: 0.75, easing: 'minimumJerk' });

    studioStore.getState().undo();
    expect(
      studioStore.getState().document.clip.keyframes.find((frame) => frame.id === first.id)?.jointTiming
        ?.head,
    ).toBeUndefined();
  });

  it('copies selected joint timing to the anatomical opposite through one undoable edit', () => {
    const first = studioStore.getState().document.clip.keyframes[0];
    studioStore.getState().setJointTiming(first.id, 'upperarm_l', {
      delay: 0.31,
      finish: 0.88,
      easing: 'minimumJerk',
    });
    const beforeCopy = studioStore.getState().document.clip.keyframes.find((frame) => frame.id === first.id)!
      .jointTiming?.upperarm_r;

    studioStore.getState().copyJointTimingToOpposite(first.id, 'upperarm_l');
    const after = studioStore.getState().document.clip.keyframes.find((frame) => frame.id === first.id)!;
    expect(after.jointTiming?.upperarm_r).toEqual(after.jointTiming?.upperarm_l);

    studioStore.getState().undo();
    expect(
      studioStore.getState().document.clip.keyframes.find((frame) => frame.id === first.id)?.jointTiming
        ?.upperarm_r,
    ).toEqual(beforeCopy);
  });

  it('clears opposite custom timing when the selected side uses phase-default timing', () => {
    const first = studioStore.getState().document.clip.keyframes[0];
    studioStore.getState().setJointTiming(first.id, 'hand_r', { delay: 0.4, finish: 0.9 });
    expect(
      studioStore.getState().document.clip.keyframes.find((frame) => frame.id === first.id)?.jointTiming
        ?.hand_r,
    ).toBeDefined();
    studioStore.getState().copyJointTimingToOpposite(first.id, 'hand_l');
    expect(
      studioStore.getState().document.clip.keyframes.find((frame) => frame.id === first.id)?.jointTiming
        ?.hand_r,
    ).toBeUndefined();
  });

  it('normalises invalid joint timing rather than creating an impossible segment', () => {
    const first = studioStore.getState().document.clip.keyframes[0];
    studioStore.getState().setJointTiming(first.id, 'head', { delay: 2, finish: -1 });
    expect(
      studioStore.getState().document.clip.keyframes.find((frame) => frame.id === first.id)?.jointTiming
        ?.head,
    ).toEqual({ delay: 1, finish: 1 });
  });

  it('stores, rescales and resets a custom playback loop independently of the clip', () => {
    const duration = studioStore.getState().document.clip.duration;
    studioStore.getState().setLoopRange({ start: 2, end: 1 });
    expect(studioStore.getState().loopRange).toEqual({ start: 1, end: 2 });

    studioStore.getState().setDuration(duration * 2);
    expect(studioStore.getState().loopRange?.start).toBeCloseTo(2, 8);
    expect(studioStore.getState().loopRange?.end).toBeCloseTo(4, 8);

    studioStore.getState().loadExercise('dumbbell_bicep_curl');
    expect(studioStore.getState().loopRange).toBeNull();
  });
});


describe('pose marker authoring', () => {
  beforeEach(() => {
    studioStore.getState().loadExercise('dumbbell_bicep_curl');
  });

  it('edits a keyframe marker through undoable document history', () => {
    const frame = studioStore.getState().document.clip.keyframes[1];
    expect(frame.marker).toBe('peak');

    studioStore.getState().setKeyframeMarker(frame.id, 'transition');
    expect(studioStore.getState().document.clip.keyframes[1].marker).toBe('transition');

    studioStore.getState().undo();
    expect(studioStore.getState().document.clip.keyframes[1].marker).toBe('peak');
  });

  it('can clear a generated marker without changing the keyframe motion', () => {
    const before = studioStore.getState().document.clip.keyframes[0];
    const x = before.pose.rotations.forearm_l?.x;
    studioStore.getState().setKeyframeMarker(before.id, null);
    const after = studioStore.getState().document.clip.keyframes[0];
    expect(after.marker).toBeUndefined();
    expect(after.pose.rotations.forearm_l?.x).toBe(x);
  });
});


describe('non-destructive pose comparison', () => {
  beforeEach(() => {
    studioStore.getState().loadExercise('dumbbell_bicep_curl');
  });

  it('captures A/B poses without touching the document or undo history', () => {
    const document = studioStore.getState().document;
    const historyCount = studioStore.getState().history.past.length;

    studioStore.getState().setTime(0);
    studioStore.getState().captureComparison('a');
    studioStore.getState().setTime(2);
    studioStore.getState().captureComparison('b');

    const state = studioStore.getState();
    expect(state.document).toBe(document);
    expect(state.history.past.length).toBe(historyCount);
    expect(state.comparison.a?.time).toBe(0);
    expect(state.comparison.b?.time).toBe(2);
    expect(state.comparison.a?.marker).toBe('start');
    expect(state.comparison.b?.marker).toBe('peak');
    expect(state.comparison.a?.pose.rotations.forearm_l?.x).not.toBe(
      state.comparison.b?.pose.rotations.forearm_l?.x,
    );
  });

  it('clears snapshots when a different exercise is loaded', () => {
    studioStore.getState().captureComparison('a');
    expect(studioStore.getState().comparison.a).not.toBeNull();
    studioStore.getState().loadExercise('air_squat');
    expect(studioStore.getState().comparison).toEqual({ a: null, b: null });
  });
});


describe('equipment grip-offset calibration', () => {
  beforeEach(() => {
    studioStore.getState().loadExercise('dumbbell_bicep_curl');
  });

  it('stores an undoable custom hand-local grip centre', () => {
    const custom = { x: -0.02, y: 0.08, z: 0.006 };
    studioStore.getState().setEquipmentGripOffset('dumbbell_l', custom);
    const instance = studioStore.getState().document.exercise.equipment.instances.find(
      (entry) => entry.id === 'dumbbell_l',
    )!;
    expect(instance.attachment.mode).toBe('hand');
    if (instance.attachment.mode !== 'hand') throw new Error('Expected hand attachment');
    expect(instance.attachment.gripOffset).toEqual(custom);

    studioStore.getState().undo();
    const restored = studioStore.getState().document.exercise.equipment.instances.find(
      (entry) => entry.id === 'dumbbell_l',
    )!;
    expect(restored.attachment.mode).toBe('hand');
    if (restored.attachment.mode !== 'hand') throw new Error('Expected hand attachment');
    expect(restored.attachment.gripOffset).toBeUndefined();
  });

  it('moves the resolved dumbbell to the authored local grip centre and can reset it', () => {
    const custom = { x: -0.018, y: 0.082, z: 0.004 };
    studioStore.getState().setEquipmentGripOffset('dumbbell_l', custom);
    const clip = studioStore.getState().document.clip;
    const evaluation = new PoseEvaluation(canonicalSkeleton);
    const frame = resolveFrame(canonicalSkeleton, evaluation, clip, 0);
    evaluation.apply(frame.pose);
    const expected = evaluation.localToWorld('hand_l', custom, new HgVec3());
    expect(frame.equipment.get('dumbbell_l')!.position.distanceTo(expected)).toBeLessThan(1e-9);

    studioStore.getState().setEquipmentGripOffset('dumbbell_l', null);
    const reset = studioStore.getState().document.exercise.equipment.instances.find(
      (entry) => entry.id === 'dumbbell_l',
    )!;
    if (reset.attachment.mode !== 'hand') throw new Error('Expected hand attachment');
    expect(reset.attachment.gripOffset).toBeUndefined();
  });
});


describe('static equipment authoring', () => {
  it('moves static equipment through normal document history and undo', () => {
    studioStore.getState().loadExercise('pull_up');
    const before = studioStore.getState().document;
    const beforeRack = before.exercise.equipment.instances.find((instance) => instance.id === 'rack')!;

    studioStore.getState().setEquipmentTransform('rack', {
      position: { x: 0.12, y: 0.04, z: -0.08 },
      rotation: { x: 0, y: 7, z: 0 },
    });

    const edited = studioStore.getState();
    const rack = edited.document.exercise.equipment.instances.find((instance) => instance.id === 'rack')!;
    const clipRack = edited.document.clip.equipment.find((instance) => instance.id === 'rack')!;
    expect(rack.position).toEqual({ x: 0.12, y: 0.04, z: -0.08 });
    expect(rack.rotation).toEqual({ x: 0, y: 7, z: 0 });
    expect(clipRack.position).toEqual(rack.position);
    expect(clipRack.rotation).toEqual(rack.rotation);
    expect(edited.history.past.at(-1)).toBe(before);

    edited.undo();
    const restored = studioStore.getState().document.exercise.equipment.instances.find(
      (instance) => instance.id === 'rack',
    )!;
    expect(restored.position).toEqual(beforeRack.position);
    expect(restored.rotation).toEqual(beforeRack.rotation);
  });

  it('refuses misleading world-transform edits on hand-driven equipment', () => {
    studioStore.getState().loadExercise('dumbbell_bicep_curl');
    const before = studioStore.getState().document;
    const historyCount = studioStore.getState().history.past.length;

    studioStore.getState().setEquipmentTransform('dumbbell_l', {
      position: { x: 4, y: 4, z: 4 },
      rotation: { x: 45, y: 45, z: 45 },
    });

    expect(studioStore.getState().document).toBe(before);
    expect(studioStore.getState().history.past.length).toBe(historyCount);
  });
});



describe('equipment socket authoring', () => {
  it('moves a static rack socket through the production contact resolver and undo', () => {
    studioStore.getState().loadExercise('pull_up');
    const before = studioStore.getState().document;
    const originalClip = before.clip;
    const evaluation = new PoseEvaluation(canonicalSkeleton);
    const originalFrame = resolveFrame(canonicalSkeleton, evaluation, originalClip, 0);
    const originalTarget = originalFrame.contacts.find((contact) => contact.chain === 'arm_l')!.target.x;

    studioStore.getState().setEquipmentSocketTransform('rack', 'pullup_l', {
      position: { x: -0.30, y: 1.97, z: 0 },
      rotation: { x: 0, y: 90, z: 0 },
    });

    const edited = studioStore.getState();
    const rack = edited.document.exercise.equipment.instances.find((instance) => instance.id === 'rack')!;
    expect(rack.socketOverrides?.pullup_l?.position).toEqual({ x: -0.30, y: 1.97, z: 0 });
    const frame = resolveFrame(canonicalSkeleton, new PoseEvaluation(canonicalSkeleton), edited.document.clip, 0);
    const target = frame.contacts.find((contact) => contact.chain === 'arm_l')!.target.x;
    expect(target).toBeCloseTo(-0.30, 8);
    expect(target).not.toBeCloseTo(originalTarget, 4);

    edited.undo();
    const restored = studioStore.getState().document.exercise.equipment.instances.find(
      (instance) => instance.id === 'rack',
    )!;
    expect(restored.socketOverrides).toBeUndefined();
  });

  it('resets an instance socket to its library default without touching the global definition', () => {
    studioStore.getState().loadExercise('pull_up');
    studioStore.getState().setEquipmentSocketTransform('rack', 'pullup_l', {
      position: { x: -0.31, y: 1.96, z: 0.01 },
    });
    studioStore.getState().setEquipmentSocketTransform('rack', 'pullup_l', null);
    const rack = studioStore.getState().document.exercise.equipment.instances.find(
      (instance) => instance.id === 'rack',
    )!;
    expect(rack.socketOverrides).toBeUndefined();
  });

  it('keeps hand-driven handle calibration owned by the Grip workspace', () => {
    studioStore.getState().loadExercise('dumbbell_bicep_curl');
    const before = studioStore.getState().document;
    const historyCount = studioStore.getState().history.past.length;
    studioStore.getState().setEquipmentSocketTransform('dumbbell_l', 'grip', {
      position: { x: 1, y: 1, z: 1 },
    });
    expect(studioStore.getState().document).toBe(before);
    expect(studioStore.getState().history.past.length).toBe(historyCount);
  });
});



describe('visual review sign-off identity', () => {
  it('binds sign-off to the exact document and character source', () => {
    studioStore.getState().loadExercise('dumbbell_bicep_curl');
    const reviewed = studioStore.getState().document;
    studioStore.getState().markVisualReview('import-v5', 3);
    expect(studioStore.getState().visualReview).toEqual({
      document: reviewed,
      characterSourceId: 'import-v5',
      deformationRevision: 3,
    });

    studioStore.getState().setGripClosure(0.8);
    expect(studioStore.getState().visualReview?.document).not.toBe(studioStore.getState().document);

    studioStore.getState().undo();
    expect(studioStore.getState().document).toBe(reviewed);
    expect(studioStore.getState().visualReview?.characterSourceId).toBe('import-v5');
  });
});



describe('grip profile authoring', () => {
  it('adds an undoable hand-shape override without changing semantic equipment grip', () => {
    studioStore.getState().loadExercise('dumbbell_bicep_curl');
    expect(studioStore.getState().document.exercise.hands.grip).toBe('dumbbell');
    expect(studioStore.getState().document.exercise.hands.gripPreset).toBeUndefined();
    studioStore.getState().setGripPreset('handle');
    expect(studioStore.getState().document.exercise.hands.grip).toBe('dumbbell');
    expect(studioStore.getState().document.exercise.hands.gripPreset).toBe('handle');
    studioStore.getState().undo();
    expect(studioStore.getState().document.exercise.hands.gripPreset).toBeUndefined();
  });

  it('clears a redundant override when reset to the semantic grip', () => {
    studioStore.getState().loadExercise('dumbbell_bicep_curl');
    studioStore.getState().setGripPreset('rope');
    studioStore.getState().setGripPreset('dumbbell');
    expect(studioStore.getState().document.exercise.hands.gripPreset).toBeUndefined();
  });
});



describe('hand-local grip orientation calibration', () => {
  it('rotates a dumbbell in the hand without moving its grip centre and is undoable', () => {
    studioStore.getState().loadExercise('dumbbell_bicep_curl');
    const before = studioStore.getState().document;
    const custom = { x: 8, y: -4, z: 12 };
    studioStore.getState().setEquipmentGripRotation('dumbbell_l', custom);
    const state = studioStore.getState();
    const instance = state.document.exercise.equipment.instances.find((entry) => entry.id === 'dumbbell_l')!;
    if (instance.attachment.mode !== 'hand') throw new Error('Expected hand attachment');
    expect(instance.attachment.gripRotation).toEqual(custom);

    const evaluation = new PoseEvaluation(canonicalSkeleton);
    const frame = resolveFrame(canonicalSkeleton, evaluation, state.document.clip, 0);
    evaluation.apply(frame.pose);
    const expected = evaluation.localToWorld('hand_l', { x: -0.025, y: 0.085, z: 0 }, new HgVec3());
    expect(frame.equipment.get('dumbbell_l')!.position.distanceTo(expected)).toBeLessThan(1e-9);

    state.undo();
    expect(studioStore.getState().document).toBe(before);
  });

  it('can reset orientation independently of the calibrated grip centre', () => {
    studioStore.getState().loadExercise('dumbbell_bicep_curl');
    studioStore.getState().setEquipmentGripOffset('dumbbell_l', { x: -0.02, y: 0.08, z: 0.004 });
    studioStore.getState().setEquipmentGripRotation('dumbbell_l', { x: 0, y: 10, z: 0 });
    studioStore.getState().setEquipmentGripRotation('dumbbell_l', null);
    const instance = studioStore.getState().document.exercise.equipment.instances.find((entry) => entry.id === 'dumbbell_l')!;
    if (instance.attachment.mode !== 'hand') throw new Error('Expected hand attachment');
    expect(instance.attachment.gripRotation).toBeUndefined();
    expect(instance.attachment.gripOffset).toEqual({ x: -0.02, y: 0.08, z: 0.004 });
  });
});



describe('per-digit grip closure authoring', () => {
  it('adds an undoable symmetric digit override and removes redundant values', () => {
    studioStore.getState().loadExercise('dumbbell_bicep_curl');
    expect(studioStore.getState().document.exercise.hands.digitClosure).toBeUndefined();
    studioStore.getState().setGripDigitClosure('pinky', 0.62);
    expect(studioStore.getState().document.exercise.hands.digitClosure?.pinky).toBeCloseTo(0.62, 8);
    studioStore.getState().undo();
    expect(studioStore.getState().document.exercise.hands.digitClosure).toBeUndefined();
    studioStore.getState().redo();
    expect(studioStore.getState().document.exercise.hands.digitClosure?.pinky).toBeCloseTo(0.62, 8);
    studioStore.getState().setGripDigitClosure('pinky', 0.85);
    expect(studioStore.getState().document.exercise.hands.digitClosure).toBeUndefined();
  });

  it('clears all digit trims in one undoable edit', () => {
    studioStore.getState().loadExercise('dumbbell_bicep_curl');
    studioStore.getState().setGripDigitClosure('thumb', 0.7);
    studioStore.getState().setGripDigitClosure('pinky', 0.6);
    studioStore.getState().clearGripDigitClosures();
    expect(studioStore.getState().document.exercise.hands.digitClosure).toBeUndefined();
    studioStore.getState().undo();
    expect(studioStore.getState().document.exercise.hands.digitClosure?.thumb).toBeCloseTo(0.7, 8);
    expect(studioStore.getState().document.exercise.hands.digitClosure?.pinky).toBeCloseTo(0.6, 8);
  });
});


describe('visual review identity', () => {
  it('records character deformation revision and becomes stale after a document edit', () => {
    studioStore.getState().loadExercise('dumbbell_bicep_curl');
    const signedDocument = studioStore.getState().document;
    studioStore.getState().markVisualReview('review-character', 7);
    expect(studioStore.getState().visualReview).toEqual({
      document: signedDocument,
      characterSourceId: 'review-character',
      deformationRevision: 7,
    });

    studioStore.getState().setGripClosure(0.8);
    expect(studioStore.getState().document).not.toBe(signedDocument);
    expect(studioStore.getState().visualReview?.document).toBe(signedDocument);
  });
});
