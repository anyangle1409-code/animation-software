import { beforeEach, describe, expect, it } from 'vitest';
import { Vector3 } from 'three';
import { resolveFrame } from '../animation/pipeline';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
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


describe('pose marker authoring', () => {
  beforeEach(() => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
  });

  it('edits a keyframe marker through undoable document history', () => {
    const frame = useStudio.getState().document.clip.keyframes[1];
    expect(frame.marker).toBe('peak');

    useStudio.getState().setKeyframeMarker(frame.id, 'transition');
    expect(useStudio.getState().document.clip.keyframes[1].marker).toBe('transition');

    useStudio.getState().undo();
    expect(useStudio.getState().document.clip.keyframes[1].marker).toBe('peak');
  });

  it('can clear a generated marker without changing the keyframe motion', () => {
    const before = useStudio.getState().document.clip.keyframes[0];
    const x = before.pose.rotations.forearm_l?.x;
    useStudio.getState().setKeyframeMarker(before.id, null);
    const after = useStudio.getState().document.clip.keyframes[0];
    expect(after.marker).toBeUndefined();
    expect(after.pose.rotations.forearm_l?.x).toBe(x);
  });
});


describe('non-destructive pose comparison', () => {
  beforeEach(() => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
  });

  it('captures A/B poses without touching the document or undo history', () => {
    const document = useStudio.getState().document;
    const historyCount = useStudio.getState().history.past.length;

    useStudio.getState().setTime(0);
    useStudio.getState().captureComparison('a');
    useStudio.getState().setTime(2);
    useStudio.getState().captureComparison('b');

    const state = useStudio.getState();
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
    useStudio.getState().captureComparison('a');
    expect(useStudio.getState().comparison.a).not.toBeNull();
    useStudio.getState().loadExercise('air_squat');
    expect(useStudio.getState().comparison).toEqual({ a: null, b: null });
  });
});


describe('equipment grip-offset calibration', () => {
  beforeEach(() => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
  });

  it('stores an undoable custom hand-local grip centre', () => {
    const custom = { x: -0.02, y: 0.08, z: 0.006 };
    useStudio.getState().setEquipmentGripOffset('dumbbell_l', custom);
    const instance = useStudio.getState().document.exercise.equipment.instances.find(
      (entry) => entry.id === 'dumbbell_l',
    )!;
    expect(instance.attachment.mode).toBe('hand');
    if (instance.attachment.mode !== 'hand') throw new Error('Expected hand attachment');
    expect(instance.attachment.gripOffset).toEqual(custom);

    useStudio.getState().undo();
    const restored = useStudio.getState().document.exercise.equipment.instances.find(
      (entry) => entry.id === 'dumbbell_l',
    )!;
    expect(restored.attachment.mode).toBe('hand');
    if (restored.attachment.mode !== 'hand') throw new Error('Expected hand attachment');
    expect(restored.attachment.gripOffset).toBeUndefined();
  });

  it('moves the resolved dumbbell to the authored local grip centre and can reset it', () => {
    const custom = { x: -0.018, y: 0.082, z: 0.004 };
    useStudio.getState().setEquipmentGripOffset('dumbbell_l', custom);
    const clip = useStudio.getState().document.clip;
    const evaluation = new PoseEvaluation(canonicalSkeleton);
    const frame = resolveFrame(canonicalSkeleton, evaluation, clip, 0);
    evaluation.apply(frame.pose);
    const expected = evaluation.localToWorld('hand_l', custom, new Vector3());
    expect(frame.equipment.get('dumbbell_l')!.position.distanceTo(expected)).toBeLessThan(1e-9);

    useStudio.getState().setEquipmentGripOffset('dumbbell_l', null);
    const reset = useStudio.getState().document.exercise.equipment.instances.find(
      (entry) => entry.id === 'dumbbell_l',
    )!;
    if (reset.attachment.mode !== 'hand') throw new Error('Expected hand attachment');
    expect(reset.attachment.gripOffset).toBeUndefined();
  });
});


describe('static equipment authoring', () => {
  it('moves static equipment through normal document history and undo', () => {
    useStudio.getState().loadExercise('pull_up');
    const before = useStudio.getState().document;
    const beforeRack = before.exercise.equipment.instances.find((instance) => instance.id === 'rack')!;

    useStudio.getState().setEquipmentTransform('rack', {
      position: { x: 0.12, y: 0.04, z: -0.08 },
      rotation: { x: 0, y: 7, z: 0 },
    });

    const edited = useStudio.getState();
    const rack = edited.document.exercise.equipment.instances.find((instance) => instance.id === 'rack')!;
    const clipRack = edited.document.clip.equipment.find((instance) => instance.id === 'rack')!;
    expect(rack.position).toEqual({ x: 0.12, y: 0.04, z: -0.08 });
    expect(rack.rotation).toEqual({ x: 0, y: 7, z: 0 });
    expect(clipRack.position).toEqual(rack.position);
    expect(clipRack.rotation).toEqual(rack.rotation);
    expect(edited.history.past.at(-1)).toBe(before);

    edited.undo();
    const restored = useStudio.getState().document.exercise.equipment.instances.find(
      (instance) => instance.id === 'rack',
    )!;
    expect(restored.position).toEqual(beforeRack.position);
    expect(restored.rotation).toEqual(beforeRack.rotation);
  });

  it('refuses misleading world-transform edits on hand-driven equipment', () => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
    const before = useStudio.getState().document;
    const historyCount = useStudio.getState().history.past.length;

    useStudio.getState().setEquipmentTransform('dumbbell_l', {
      position: { x: 4, y: 4, z: 4 },
      rotation: { x: 45, y: 45, z: 45 },
    });

    expect(useStudio.getState().document).toBe(before);
    expect(useStudio.getState().history.past.length).toBe(historyCount);
  });
});



describe('equipment socket authoring', () => {
  it('moves a static rack socket through the production contact resolver and undo', () => {
    useStudio.getState().loadExercise('pull_up');
    const before = useStudio.getState().document;
    const originalClip = before.clip;
    const evaluation = new PoseEvaluation(canonicalSkeleton);
    const originalFrame = resolveFrame(canonicalSkeleton, evaluation, originalClip, 0);
    const originalTarget = originalFrame.contacts.find((contact) => contact.chain === 'arm_l')!.target.x;

    useStudio.getState().setEquipmentSocketTransform('rack', 'pullup_l', {
      position: { x: -0.30, y: 1.97, z: 0 },
      rotation: { x: 0, y: 90, z: 0 },
    });

    const edited = useStudio.getState();
    const rack = edited.document.exercise.equipment.instances.find((instance) => instance.id === 'rack')!;
    expect(rack.socketOverrides?.pullup_l?.position).toEqual({ x: -0.30, y: 1.97, z: 0 });
    const frame = resolveFrame(canonicalSkeleton, new PoseEvaluation(canonicalSkeleton), edited.document.clip, 0);
    const target = frame.contacts.find((contact) => contact.chain === 'arm_l')!.target.x;
    expect(target).toBeCloseTo(-0.30, 8);
    expect(target).not.toBeCloseTo(originalTarget, 4);

    edited.undo();
    const restored = useStudio.getState().document.exercise.equipment.instances.find(
      (instance) => instance.id === 'rack',
    )!;
    expect(restored.socketOverrides).toBeUndefined();
  });

  it('resets an instance socket to its library default without touching the global definition', () => {
    useStudio.getState().loadExercise('pull_up');
    useStudio.getState().setEquipmentSocketTransform('rack', 'pullup_l', {
      position: { x: -0.31, y: 1.96, z: 0.01 },
    });
    useStudio.getState().setEquipmentSocketTransform('rack', 'pullup_l', null);
    const rack = useStudio.getState().document.exercise.equipment.instances.find(
      (instance) => instance.id === 'rack',
    )!;
    expect(rack.socketOverrides).toBeUndefined();
  });

  it('keeps hand-driven handle calibration owned by the Grip workspace', () => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
    const before = useStudio.getState().document;
    const historyCount = useStudio.getState().history.past.length;
    useStudio.getState().setEquipmentSocketTransform('dumbbell_l', 'grip', {
      position: { x: 1, y: 1, z: 1 },
    });
    expect(useStudio.getState().document).toBe(before);
    expect(useStudio.getState().history.past.length).toBe(historyCount);
  });
});



describe('visual review sign-off identity', () => {
  it('binds sign-off to the exact document and character source', () => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
    const reviewed = useStudio.getState().document;
    useStudio.getState().markVisualReview('import-v5');
    expect(useStudio.getState().visualReview).toEqual({ document: reviewed, characterSourceId: 'import-v5' });

    useStudio.getState().setGripClosure(0.8);
    expect(useStudio.getState().visualReview?.document).not.toBe(useStudio.getState().document);

    useStudio.getState().undo();
    expect(useStudio.getState().document).toBe(reviewed);
    expect(useStudio.getState().visualReview?.characterSourceId).toBe('import-v5');
  });
});



describe('grip profile authoring', () => {
  it('adds an undoable hand-shape override without changing semantic equipment grip', () => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
    expect(useStudio.getState().document.exercise.hands.grip).toBe('dumbbell');
    expect(useStudio.getState().document.exercise.hands.gripPreset).toBeUndefined();
    useStudio.getState().setGripPreset('handle');
    expect(useStudio.getState().document.exercise.hands.grip).toBe('dumbbell');
    expect(useStudio.getState().document.exercise.hands.gripPreset).toBe('handle');
    useStudio.getState().undo();
    expect(useStudio.getState().document.exercise.hands.gripPreset).toBeUndefined();
  });

  it('clears a redundant override when reset to the semantic grip', () => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
    useStudio.getState().setGripPreset('rope');
    useStudio.getState().setGripPreset('dumbbell');
    expect(useStudio.getState().document.exercise.hands.gripPreset).toBeUndefined();
  });
});



describe('hand-local grip orientation calibration', () => {
  it('rotates a dumbbell in the hand without moving its grip centre and is undoable', () => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
    const before = useStudio.getState().document;
    const custom = { x: 8, y: -4, z: 12 };
    useStudio.getState().setEquipmentGripRotation('dumbbell_l', custom);
    const state = useStudio.getState();
    const instance = state.document.exercise.equipment.instances.find((entry) => entry.id === 'dumbbell_l')!;
    if (instance.attachment.mode !== 'hand') throw new Error('Expected hand attachment');
    expect(instance.attachment.gripRotation).toEqual(custom);

    const evaluation = new PoseEvaluation(canonicalSkeleton);
    const frame = resolveFrame(canonicalSkeleton, evaluation, state.document.clip, 0);
    evaluation.apply(frame.pose);
    const expected = evaluation.localToWorld('hand_l', { x: -0.025, y: 0.085, z: 0 }, new Vector3());
    expect(frame.equipment.get('dumbbell_l')!.position.distanceTo(expected)).toBeLessThan(1e-9);

    state.undo();
    expect(useStudio.getState().document).toBe(before);
  });

  it('can reset orientation independently of the calibrated grip centre', () => {
    useStudio.getState().loadExercise('dumbbell_bicep_curl');
    useStudio.getState().setEquipmentGripOffset('dumbbell_l', { x: -0.02, y: 0.08, z: 0.004 });
    useStudio.getState().setEquipmentGripRotation('dumbbell_l', { x: 0, y: 10, z: 0 });
    useStudio.getState().setEquipmentGripRotation('dumbbell_l', null);
    const instance = useStudio.getState().document.exercise.equipment.instances.find((entry) => entry.id === 'dumbbell_l')!;
    if (instance.attachment.mode !== 'hand') throw new Error('Expected hand attachment');
    expect(instance.attachment.gripRotation).toBeUndefined();
    expect(instance.attachment.gripOffset).toEqual({ x: -0.02, y: 0.08, z: 0.004 });
  });
});
