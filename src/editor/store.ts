import { create } from 'zustand';
import { Vector3 } from 'three';
import type { BoneName, Finger } from '../rig/boneNames';
import { mirrorBoneName } from '../rig/boneNames';
import { canonicalSkeleton, PoseEvaluation } from '../rig/skeleton';
import type { Axis, Pose, Vec3 } from '../rig/types';
import {
  clonePose,
  clampRotation,
  mirrorPose,
  mirrorSideInPlace,
  restPose,
} from '../rig/pose';
import type { StudioClip, Keyframe, PoseMarkerKind } from '../animation/clip';
import { sampleClip, sortedKeyframes } from '../animation/clip';
import { generateClip, phaseDuration } from '../animation/generate';
import { validateClip } from '../animation/validate';
import type { ClipValidation } from '../animation/validate';
import { lockAnchors } from '../constraints/locks';
import type { ExerciseDefinition, GripKind, PhaseJointTiming, Tempo } from '../exercises/types';
import { EXERCISES, getExercise } from '../exercises/library';
import type { IKChainId } from '../ik/types';
import { goalFromPose } from '../ik/solve';
import { nextId } from '../core/id';
import { emptyHistory, pushHistory, redo, undo } from './history';
import type { History } from './history';
import type { CameraPresetId } from '../viewer/cameraTypes';
import { normalizeLoopRange, type LoopRange } from './playback';
import type { PoseSnapshot } from './comparison';
import { equipmentSocket, withTwoHandGripWidth } from '../equipment/library';

export type ViewMode = 'skeleton' | 'muscles' | 'combined' | 'character' | 'anatomy';

/**
 * Which modes draw the muscle bellies as separate meshes. The anatomy view is
 * deliberately not one of them: it is a single continuous surface, and a belly
 * floating inside the arm is the thing it exists to replace.
 */
export const showsMuscleBellies = (mode: ViewMode): boolean =>
  mode === 'muscles' || mode === 'combined';

/**
 * The studio's own dark stage, or a clean light one. The light backdrop is what
 * app-facing captures use, so a demonstration frame does not arrive in Home Gym
 * PT with the editor's chrome colours behind it.
 */
export type Backdrop = 'studio' | 'light' | 'void' | 'study';

export interface BackdropStyle {
  background: string;
  ground: string;
  cell: string;
  section: string;
  /**
   * A stage with no floor at all: no grid, no ground plane, no cast shadow, so
   * the figure is the only thing in frame. This is what the anatomy view is
   * meant to be seen on.
   */
  floorless?: boolean;
  /**
   * The stage's own lighting. It belongs to the backdrop rather than to the
   * viewport, because a figure lit for a bright room reads flat against black —
   * relief on an unlit stage has to come from the key and the rim.
   */
  lighting: {
    ambient: number;
    key: number;
    rim: number;
    rimColour: string;
  };
}

const WORKING_LIGHT = { ambient: 0.62, key: 1.5, rim: 0.45, rimColour: '#9fc4ff' };

export const BACKDROPS: Record<Backdrop, BackdropStyle> = {
  studio: {
    background: '#12151a',
    ground: '#171b21',
    cell: '#2a313c',
    section: '#3d4756',
    lighting: WORKING_LIGHT,
  },
  // The ground matches the background, so a capture has no horizon line across
  // it — only the figure and its shadow.
  light: {
    background: '#eef1f5',
    ground: '#eef1f5',
    cell: '#e1e6ed',
    section: '#d5dce6',
    lighting: WORKING_LIGHT,
  },
  void: {
    background: '#000000',
    ground: '#000000',
    cell: '#000000',
    section: '#000000',
    floorless: true,
    // Low ambient and a strong rim: on black, the edge light is what separates
    // the figure from the background and what makes muscle relief legible. The
    // ambient is nonetheless lifted off the floor, because at 0.14 a recess as
    // deep as an eye socket goes to pure black and reads as a hole in the head.
    lighting: { ambient: 0.24, key: 1.7, rim: 1.0, rimColour: '#cfd8e6' },
  },
  study: {
    background: '#000000',
    // Not the background: this is what the hemisphere light fills from below, and
    // a black floor colour is what leaves the underside of every form unlit.
    ground: '#4a4a4a',
    cell: '#000000',
    section: '#000000',
    floorless: true,
    /**
     * Diagnostic lighting. The void rig is a presentation rig — a hard key and a
     * strong rim flatter the figure and can make a chest look fuller than its
     * geometry. This one is deliberately dull: most of the light is ambient, the
     * key is weak enough not to blow a highlight, and what is left is the form
     * itself. Use it to judge shape, not to show the model off.
     */
    lighting: { ambient: 1.05, key: 0.6, rim: 0.28, rimColour: '#ffffff' },
  },
};

/** Everything an undo step restores. Selection and playback are deliberately outside. */
export interface StudioDocument {
  exercise: ExerciseDefinition;
  clip: StudioClip;
}

export interface Selection {
  bone: BoneName | null;
  handle: { chain: IKChainId; kind: 'target' | 'pole' } | null;
  equipmentId: string | null;
  socketId: string | null;
}

interface StudioState {
  document: StudioDocument;
  history: History<StudioDocument>;

  time: number;
  playing: boolean;
  loop: boolean;
  speed: number;
  loopRange: LoopRange | null;
  comparison: { a: PoseSnapshot | null; b: PoseSnapshot | null };
  visualReview: { document: StudioDocument; characterSourceId: string } | null;

  selection: Selection;
  viewMode: ViewMode;
  showJoints: boolean;
  showEquipment: boolean;
  showIkHandles: boolean;
  showGrid: boolean;
  /** Studio dark, or the light backdrop used for app-facing captures. */
  backdrop: Backdrop;
  gizmoMode: 'rotate' | 'translate';
  camera: CameraPresetId;

  clipboard: Pose | null;
  validation: ClipValidation | null;

  // --- playback -----------------------------------------------------------
  setTime: (time: number) => void;
  play: () => void;
  pause: () => void;
  togglePlay: () => void;
  setLoop: (loop: boolean) => void;
  setSpeed: (speed: number) => void;
  setLoopRange: (range: LoopRange | null) => void;
  captureComparison: (slot: 'a' | 'b') => void;
  clearComparison: (slot?: 'a' | 'b') => void;
  markVisualReview: (characterSourceId: string) => void;
  clearVisualReview: () => void;

  // --- selection and display ---------------------------------------------
  selectBone: (bone: BoneName | null) => void;
  selectHandle: (handle: Selection['handle']) => void;
  selectEquipment: (id: string | null) => void;
  selectSocket: (equipmentId: string, socketId: string | null) => void;
  setViewMode: (mode: ViewMode) => void;
  setCamera: (preset: CameraPresetId) => void;
  toggle: (key: 'showJoints' | 'showEquipment' | 'showIkHandles' | 'showGrid') => void;
  setBackdrop: (backdrop: Backdrop) => void;
  setGizmoMode: (mode: 'rotate' | 'translate') => void;

  // --- editing ------------------------------------------------------------
  loadExercise: (id: string) => void;
  regenerate: () => void;
  setBoneAxis: (bone: BoneName, axis: Axis, radians: number) => void;
  setBoneRotation: (bone: BoneName, rotation: Vec3) => void;
  setIKTarget: (chain: IKChainId, kind: 'target' | 'pole', position: Vec3) => void;
  toggleIK: (chain: IKChainId) => void;
  setKeyframe: () => void;
  deleteKeyframe: (id: string) => void;
  moveKeyframe: (id: string, time: number) => void;
  setKeyframeEasing: (id: string, easing: Keyframe['easing']) => void;
  setKeyframeMarker: (id: string, marker: PoseMarkerKind | null) => void;
  setJointTiming: (id: string, bone: BoneName, timing: PhaseJointTiming | null) => void;
  copyJointTimingToOpposite: (id: string, bone: BoneName) => void;
  copyPose: () => void;
  pastePose: () => void;
  mirrorCurrentPose: () => void;
  mirrorSide: (from: 'l' | 'r') => void;
  setDuration: (duration: number) => void;
  setTempo: (tempo: Partial<Tempo>) => void;
  setGripClosure: (closure: number) => void;
  setGripPreset: (preset: GripKind | null) => void;
  setGripDigitClosure: (finger: Finger, closure: number | null) => void;
  clearGripDigitClosures: () => void;
  setEquipmentGripOffset: (instanceId: string, offset: Vec3 | null) => void;
  setEquipmentGripRotation: (instanceId: string, rotation: Vec3 | null) => void;
  setTwoHandGripWidth: (instanceId: string, width: number | null) => void;
  setTwoHandGripRoll: (instanceId: string, degrees: number | null) => void;
  setEquipmentTransform: (instanceId: string, transform: { position?: Vec3; rotation?: Vec3 }) => void;
  setEquipmentSocketTransform: (instanceId: string, socketId: string, transform: { position?: Vec3; rotation?: Vec3 } | null) => void;
  setLockEnabled: (lockId: string, enabled: boolean) => void;
  runValidation: () => void;

  undo: () => void;
  redo: () => void;
}

export const skeleton = canonicalSkeleton;
const evaluation = new PoseEvaluation(skeleton);

function buildDocument(exercise: ExerciseDefinition): StudioDocument {
  return { exercise, clip: generateClip(skeleton, exercise) };
}

/** Keyframe at `time`, within half a frame. */
function keyframeAt(clip: StudioClip, time: number): Keyframe | undefined {
  const tolerance = 0.5 / clip.fps;
  return clip.keyframes.find((frame) => Math.abs(frame.time - time) <= tolerance);
}

/**
 * The keyframe an edit at `time` should land on, creating one from the sampled
 * pose if the playhead is between keys. Editing between keys silently moving a
 * neighbouring key would be worse than making a new one.
 */
function keyframeForEdit(clip: StudioClip, time: number): { clip: StudioClip; keyframe: Keyframe } {
  const existing = keyframeAt(clip, time);
  if (existing) {
    const keyframe = { ...existing, pose: clonePose(existing.pose), ik: { ...existing.ik } };
    return {
      clip: { ...clip, keyframes: clip.keyframes.map((f) => (f.id === existing.id ? keyframe : f)) },
      keyframe,
    };
  }
  const sample = sampleClip(clip, time);
  const previous = sortedKeyframes(clip)
    .filter((frame) => frame.time <= time)
    .at(-1);
  const keyframe: Keyframe = {
    id: nextId('kf'),
    time,
    pose: sample.pose,
    ik: sample.ik,
    easing: previous?.easing ?? 'lift',
    phaseId: sample.phaseId,
  };
  return { clip: { ...clip, keyframes: [...clip.keyframes, keyframe] }, keyframe };
}

export const useStudio = create<StudioState>((set, get) => {
  const commit = (mutate: (document: StudioDocument) => StudioDocument) => {
    const state = get();
    const next = mutate(state.document);
    set({
      document: next,
      history: pushHistory(state.history, state.document),
      validation: null,
    });
  };

  const editClip = (mutate: (clip: StudioClip) => StudioClip) =>
    commit((document) => ({ ...document, clip: mutate(document.clip) }));

  /** Edit the keyframe under the playhead. */
  const editKeyframe = (mutate: (keyframe: Keyframe) => void) => {
    const { time } = get();
    editClip((clip) => {
      const result = keyframeForEdit(clip, time);
      mutate(result.keyframe);
      return result.clip;
    });
  };

  return {
    document: buildDocument(EXERCISES[0]),
    history: emptyHistory<StudioDocument>(),

    time: 0,
    playing: false,
    loop: true,
    speed: 1,
    loopRange: null,
    comparison: { a: null, b: null },
    visualReview: null,

    selection: { bone: null, handle: null, equipmentId: null, socketId: null },
    viewMode: 'combined',
    showJoints: true,
    showEquipment: true,
    showIkHandles: true,
    showGrid: true,
    backdrop: 'studio',
    gizmoMode: 'rotate',
    camera: 'recommended',

    clipboard: null,
    validation: null,

    setTime: (time) => set({ time: Math.max(0, Math.min(get().document.clip.duration, time)) }),
    play: () => set({ playing: true }),
    pause: () => set({ playing: false }),
    togglePlay: () => set({ playing: !get().playing }),
    setLoop: (loop) => set({ loop }),
    setSpeed: (speed) => set({ speed }),
    setLoopRange: (range) => {
      const clip = get().document.clip;
      set({ loopRange: normalizeLoopRange(range, clip.duration, clip.fps) });
    },
    captureComparison: (slot) => {
      const state = get();
      const sample = sampleClip(state.document.clip, state.time);
      const frame = keyframeAt(state.document.clip, state.time);
      const snapshot: PoseSnapshot = {
        pose: clonePose(sample.pose),
        time: state.time,
        ...(frame?.marker ? { marker: frame.marker } : {}),
        ...(frame?.label ? { label: frame.label } : {}),
      };
      set({ comparison: { ...state.comparison, [slot]: snapshot } });
    },
    markVisualReview: (characterSourceId) =>
      set({ visualReview: { document: get().document, characterSourceId } }),
    clearVisualReview: () => set({ visualReview: null }),
    clearComparison: (slot) => {
      const comparison = get().comparison;
      set({
        comparison: slot
          ? { ...comparison, [slot]: null }
          : { a: null, b: null },
      });
    },

    selectBone: (bone) =>
      set({ selection: { bone, handle: null, equipmentId: null, socketId: null } }),
    selectHandle: (handle) => set({ selection: { bone: null, handle, equipmentId: null, socketId: null } }),
    selectEquipment: (equipmentId) =>
      set({ selection: { bone: null, handle: null, equipmentId, socketId: null } }),
    selectSocket: (equipmentId, socketId) =>
      set({ selection: { bone: null, handle: null, equipmentId, socketId } }),
    setViewMode: (viewMode) => set({ viewMode }),
    setBackdrop: (backdrop) => set({ backdrop }),
    setCamera: (camera) => set({ camera }),
    toggle: (key) => set({ [key]: !get()[key] } as Partial<StudioState>),
    setGizmoMode: (gizmoMode) => set({ gizmoMode }),

    loadExercise: (id) => {
      const exercise = getExercise(id);
      set({
        document: buildDocument(exercise),
        history: emptyHistory<StudioDocument>(),
        time: 0,
        playing: false,
        loopRange: null,
        comparison: { a: null, b: null },
        validation: null,
        camera: 'recommended',
        selection: { bone: null, handle: null, equipmentId: null, socketId: null },
      });
    },

    regenerate: () => commit((document) => buildDocument(document.exercise)),

    setBoneAxis: (bone, axis, radians) => {
      const rigBone = skeleton.bone(bone);
      editKeyframe((keyframe) => {
        const current = keyframe.pose.rotations[bone] ?? { x: 0, y: 0, z: 0 };
        keyframe.pose.rotations[bone] = clampRotation(rigBone, { ...current, [axis]: radians });
      });
    },

    setBoneRotation: (bone, rotation) => {
      const rigBone = skeleton.bone(bone);
      editKeyframe((keyframe) => {
        keyframe.pose.rotations[bone] = clampRotation(rigBone, rotation);
      });
    },

    setIKTarget: (chain, kind, position) => {
      editKeyframe((keyframe) => {
        const existing =
          keyframe.ik[chain] ?? goalFromPose(evaluation, keyframe.pose, chain);
        keyframe.ik = {
          ...keyframe.ik,
          [chain]: {
            enabled: true,
            target: kind === 'target' ? { ...position } : { ...existing.target },
            pole: kind === 'pole' ? { ...position } : { ...existing.pole },
            aim: 'aim' in existing ? existing.aim : undefined,
          },
        };
      });
    },

    toggleIK: (chain) => {
      editKeyframe((keyframe) => {
        const existing = keyframe.ik[chain];
        if (existing?.enabled) {
          keyframe.ik = { ...keyframe.ik, [chain]: { ...existing, enabled: false } };
          return;
        }
        const goal = goalFromPose(evaluation, keyframe.pose, chain);
        keyframe.ik = {
          ...keyframe.ik,
          [chain]: { enabled: true, target: goal.target, pole: goal.pole },
        };
      });
    },

    setKeyframe: () => {
      const { time } = get();
      editClip((clip) => keyframeForEdit(clip, time).clip);
    },

    deleteKeyframe: (id) =>
      editClip((clip) => {
        if (clip.keyframes.length <= 2) return clip;
        return { ...clip, keyframes: clip.keyframes.filter((frame) => frame.id !== id) };
      }),

    moveKeyframe: (id, time) =>
      editClip((clip) => ({
        ...clip,
        keyframes: clip.keyframes.map((frame) =>
          frame.id === id
            ? { ...frame, time: Math.max(0, Math.min(clip.duration, time)) }
            : frame,
        ),
      })),

    setKeyframeEasing: (id, easing) =>
      editClip((clip) => ({
        ...clip,
        keyframes: clip.keyframes.map((frame) => (frame.id === id ? { ...frame, easing } : frame)),
      })),

    setKeyframeMarker: (id, marker) =>
      editClip((clip) => ({
        ...clip,
        keyframes: clip.keyframes.map((frame) =>
          frame.id === id ? { ...frame, marker: marker ?? undefined } : frame,
        ),
      })),

    setJointTiming: (id, bone, timing) =>
      editClip((clip) => ({
        ...clip,
        keyframes: clip.keyframes.map((frame) => {
          if (frame.id !== id) return frame;
          const jointTiming: Partial<Record<BoneName, PhaseJointTiming>> = {
            ...(frame.jointTiming ?? {}),
          };
          if (!timing) delete jointTiming[bone];
          else {
            const delay = Math.max(0, Math.min(1, timing.delay ?? 0));
            const finish = Math.max(delay, Math.max(0, Math.min(1, timing.finish ?? 1)));
            jointTiming[bone] = {
              delay,
              finish,
              ...(timing.easing ? { easing: timing.easing } : {}),
            };
          }
          return {
            ...frame,
            jointTiming: Object.keys(jointTiming).length > 0 ? jointTiming : undefined,
          };
        }),
      })),

    copyJointTimingToOpposite: (id, bone) => {
      const opposite = mirrorBoneName(bone);
      if (opposite === bone) return;
      editClip((clip) => ({
        ...clip,
        keyframes: clip.keyframes.map((frame) => {
          if (frame.id !== id) return frame;
          const source = frame.jointTiming?.[bone];
          const jointTiming: Partial<Record<BoneName, PhaseJointTiming>> = {
            ...(frame.jointTiming ?? {}),
          };
          if (source) jointTiming[opposite] = { ...source };
          else delete jointTiming[opposite];
          return {
            ...frame,
            jointTiming: Object.keys(jointTiming).length > 0 ? jointTiming : undefined,
          };
        }),
      }));
    },

    copyPose: () => {
      const { document, time } = get();
      set({ clipboard: sampleClip(document.clip, time).pose });
    },

    pastePose: () => {
      const clipboard = get().clipboard;
      if (!clipboard) return;
      editKeyframe((keyframe) => {
        keyframe.pose = clonePose(clipboard);
      });
    },

    mirrorCurrentPose: () =>
      editKeyframe((keyframe) => {
        keyframe.pose = mirrorPose(skeleton, keyframe.pose);
      }),

    mirrorSide: (from) =>
      editKeyframe((keyframe) => {
        keyframe.pose = mirrorSideInPlace(skeleton, keyframe.pose, from);
      }),

    setDuration: (duration) => {
      const previous = get().document.clip;
      const next = Math.max(0.2, duration);
      editClip((clip) => {
        const scale = next / clip.duration;
        return {
          ...clip,
          duration: next,
          keyframes: clip.keyframes.map((frame) => ({
            ...frame,
            time: Math.round(frame.time * scale * 1e6) / 1e6,
          })),
        };
      });
      const range = get().loopRange;
      const scale = next / previous.duration;
      set({
        time: Math.min(get().time, next),
        loopRange: range
          ? normalizeLoopRange(
              { start: range.start * scale, end: range.end * scale },
              next,
              previous.fps,
            )
          : null,
      });
    },

    setTempo: (tempo) =>
      commit((document) => {
        const exercise = { ...document.exercise, tempo: { ...document.exercise.tempo, ...tempo } };
        return { exercise, clip: generateClip(skeleton, exercise) };
      }),

    setGripClosure: (closure) =>
      commit((document) => {
        const normalized = Math.max(0, Math.min(1, closure));
        const exercise = {
          ...document.exercise,
          hands: { ...document.exercise.hands, closure: normalized },
        };
        return { exercise, clip: generateClip(skeleton, exercise) };
      }),


    setGripPreset: (preset) =>
      commit((document) => {
        const hands = { ...document.exercise.hands };
        if (preset === null || preset === hands.grip) delete hands.gripPreset;
        else hands.gripPreset = preset;
        const exercise = { ...document.exercise, hands };
        return { exercise, clip: generateClip(skeleton, exercise) };
      }),


    setGripDigitClosure: (finger, closure) =>
      commit((document) => {
        const hands = { ...document.exercise.hands };
        const digitClosure = { ...(hands.digitClosure ?? {}) };
        const value = closure === null ? null : Math.max(0, Math.min(1, closure));
        if (value === null || Math.abs(value - hands.closure) < 1e-9) delete digitClosure[finger];
        else digitClosure[finger] = value;
        if (Object.keys(digitClosure).length > 0) hands.digitClosure = digitClosure;
        else delete hands.digitClosure;
        const exercise = { ...document.exercise, hands };
        return { exercise, clip: generateClip(skeleton, exercise) };
      }),

    clearGripDigitClosures: () =>
      commit((document) => {
        if (!document.exercise.hands.digitClosure) return document;
        const hands = { ...document.exercise.hands };
        delete hands.digitClosure;
        const exercise = { ...document.exercise, hands };
        return { exercise, clip: generateClip(skeleton, exercise) };
      }),

    setEquipmentGripOffset: (instanceId, offset) =>
      commit((document) => {
        const instances = document.exercise.equipment.instances.map((instance) => {
          if (instance.id !== instanceId || instance.attachment.mode !== 'hand') return instance;
          if (offset) {
            return {
              ...instance,
              attachment: { ...instance.attachment, gripOffset: { ...offset } },
            };
          }
          const { gripOffset: _gripOffset, ...attachment } = instance.attachment;
          return { ...instance, attachment };
        });
        const exercise = {
          ...document.exercise,
          equipment: { ...document.exercise.equipment, instances },
        };
        return { exercise, clip: generateClip(skeleton, exercise) };
      }),


    setEquipmentGripRotation: (instanceId, rotation) =>
      commit((document) => {
        const instances = document.exercise.equipment.instances.map((instance) => {
          if (instance.id !== instanceId || instance.attachment.mode !== 'hand') return instance;
          if (rotation) {
            return {
              ...instance,
              attachment: { ...instance.attachment, gripRotation: { ...rotation } },
            };
          }
          const { gripRotation: _gripRotation, ...attachment } = instance.attachment;
          return { ...instance, attachment };
        });
        const exercise = {
          ...document.exercise,
          equipment: { ...document.exercise.equipment, instances },
        };
        return { exercise, clip: generateClip(skeleton, exercise) };
      }),


    setTwoHandGripWidth: (instanceId, width) =>
      commit((document) => {
        const instances = document.exercise.equipment.instances.map((instance) =>
          instance.id === instanceId ? withTwoHandGripWidth(instance, width) : instance,
        );
        const exercise = {
          ...document.exercise,
          equipment: { ...document.exercise.equipment, instances },
        };
        return { exercise, clip: generateClip(skeleton, exercise) };
      }),

    setTwoHandGripRoll: (instanceId, degrees) =>
      commit((document) => {
        const instances = document.exercise.equipment.instances.map((instance) => {
          if (instance.id !== instanceId || instance.attachment.mode !== 'hands') return instance;
          if (degrees === null || Math.abs(degrees) < 1e-9) {
            const { gripRoll: _gripRoll, ...attachment } = instance.attachment;
            return { ...instance, attachment };
          }
          return {
            ...instance,
            attachment: { ...instance.attachment, gripRoll: degrees },
          };
        });
        const exercise = {
          ...document.exercise,
          equipment: { ...document.exercise.equipment, instances },
        };
        return { exercise, clip: generateClip(skeleton, exercise) };
      }),

    setEquipmentTransform: (instanceId, transform) => {
      const current = get().document.exercise.equipment.instances.find(
        (instance) => instance.id === instanceId,
      );
      // Hand-driven equipment belongs to the grip/attachment system. A world
      // transform edit would be overwritten by the next resolved frame, so do
      // not create a misleading undo step for it.
      if (!current || current.attachment.mode !== 'static') return;
      commit((document) => {
        const instances = document.exercise.equipment.instances.map((instance) =>
          instance.id === instanceId
            ? {
                ...instance,
                position: transform.position ? { ...transform.position } : { ...instance.position },
                rotation: transform.rotation ? { ...transform.rotation } : { ...instance.rotation },
              }
            : instance,
        );
        const exercise = {
          ...document.exercise,
          equipment: { ...document.exercise.equipment, instances },
        };
        return { exercise, clip: generateClip(skeleton, exercise) };
      });
    },


    setEquipmentSocketTransform: (instanceId, socketId, transform) => {
      const current = get().document.exercise.equipment.instances.find(
        (instance) => instance.id === instanceId,
      );
      // Socket calibration is currently for static equipment. Hand-driven
      // handles remain owned by the Grip workspace to avoid two competing
      // ways of moving the same contact point.
      if (!current || current.attachment.mode !== 'static' || !equipmentSocket(current.kind, socketId)) return;
      commit((document) => {
        const instances = document.exercise.equipment.instances.map((instance) => {
          if (instance.id !== instanceId) return instance;
          const socketOverrides: Partial<Record<string, { position?: Vec3; rotation?: Vec3 }>> = {
            ...(instance.socketOverrides ?? {}),
          };
          if (!transform) {
            delete socketOverrides[socketId];
          } else {
            const previous = socketOverrides[socketId] ?? {};
            socketOverrides[socketId] = {
              ...(transform.position
                ? { position: { ...transform.position } }
                : previous.position
                  ? { position: { ...previous.position } }
                  : {}),
              ...(transform.rotation
                ? { rotation: { ...transform.rotation } }
                : previous.rotation
                  ? { rotation: { ...previous.rotation } }
                  : {}),
            };
          }
          return {
            ...instance,
            socketOverrides: Object.keys(socketOverrides).length > 0 ? socketOverrides : undefined,
          };
        });
        const exercise = {
          ...document.exercise,
          equipment: { ...document.exercise.equipment, instances },
        };
        return { exercise, clip: generateClip(skeleton, exercise) };
      });
    },

    setLockEnabled: (lockId, enabled) =>
      editClip((clip) => ({
        ...clip,
        locks: clip.locks.map((lock) => (lock.id === lockId ? { ...lock, enabled } : lock)),
      })),

    runValidation: () => {
      const { document } = get();
      set({
        validation: validateClip(skeleton, evaluation, document.exercise, document.clip),
      });
    },

    undo: () => {
      const state = get();
      const result = undo(state.history, state.document);
      if (!result) return;
      set({ document: result.value, history: result.history, validation: null });
    },

    redo: () => {
      const state = get();
      const result = redo(state.history, state.document);
      if (!result) return;
      set({ document: result.value, history: result.history, validation: null });
    },
  };
});

/** Contact anchors for the current clip, recomputed when the clip changes. */
export function currentAnchors(clip: StudioClip): Map<string, Vec3> {
  return lockAnchors(new PoseEvaluation(skeleton), sampleClip(clip, 0).pose, clip.locks);
}

export const phaseDurationOf = phaseDuration;
export const emptyPose = restPose;
export const worldVector = (v: Vec3): Vector3 => new Vector3(v.x, v.y, v.z);
