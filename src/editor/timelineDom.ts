import type { ObservableStore } from '../core/observableStore';
import { EASING_LABELS } from '../animation/easing';
import { sortedKeyframes, type Keyframe, type PoseMarkerKind, type StudioClip } from '../animation/clip';
import { phaseBoundaries } from '../animation/generate';
import type { EasingKind, ExerciseDefinition } from '../exercises/types';
import { studioStore, type StudioState } from './storeCore';

type TimelineStorePort = Pick<ObservableStore<StudioState>, 'getState' | 'subscribe'>;

const PHASE_COLOURS: Record<string, string> = {
  concentric: '#2f5d4a',
  eccentric: '#3a4a6b',
  isometric: '#4a4030',
};

const POSE_MARKER_LABELS: Record<PoseMarkerKind, string> = {
  start: 'Start',
  transition: 'Transition',
  peak: 'Peak',
  return: 'Return',
};

const SPEEDS = [0.25, 0.5, 1, 1.5, 2] as const;

export interface StudioTimelineControls {
  play: HTMLButtonElement;
  previousFrame: HTMLButtonElement;
  nextFrame: HTMLButtonElement;
  timeReadout: HTMLSpanElement;
  frameReadout: HTMLSpanElement;
  speed: HTMLSelectElement;
  loop: HTMLInputElement;
  setIn: HTMLButtonElement;
  setOut: HTMLButtonElement;
  clearRange: HTMLButtonElement;
  rangeReadout: HTMLSpanElement;
  duration: HTMLInputElement;
  setKeyframe: HTMLButtonElement;
  deleteKeyframe: HTMLButtonElement;
  marker: HTMLSelectElement;
  easing: HTMLSelectElement;
  track: HTMLDivElement;
  playhead: HTMLDivElement;
}

export interface StudioTimelineDom {
  element: HTMLElement;
  controls: StudioTimelineControls;
  dispose(): void;
}

const option = (
  documentRef: Pick<Document, 'createElement'>,
  value: string,
  label: string,
): HTMLOptionElement => {
  const element = documentRef.createElement('option');
  element.value = value;
  element.textContent = label;
  return element;
};

const button = (
  documentRef: Pick<Document, 'createElement'>,
  label: string,
  title?: string,
): HTMLButtonElement => {
  const element = documentRef.createElement('button');
  element.type = 'button';
  element.textContent = label;
  if (title) element.title = title;
  return element;
};

const field = (
  documentRef: Pick<Document, 'createElement'>,
  labelText: string,
  control: HTMLElement,
  className = 'field field--inline',
): HTMLLabelElement => {
  const label = documentRef.createElement('label');
  label.className = className;
  const text = documentRef.createElement('span');
  text.className = 'field__label';
  text.textContent = labelText;
  label.append(text, control);
  return label;
};

const currentKeyframe = (clip: StudioClip, time: number): Keyframe | undefined =>
  sortedKeyframes(clip).find((frame) => Math.abs(frame.time - time) < 0.5 / clip.fps);

/**
 * React-free Timeline DOM/controller backed directly by the framework-neutral
 * Studio store. Structural track content is rebuilt only when the clip or
 * exercise changes; playback-time updates only move live indicators.
 */
export function createStudioTimelineDom(
  documentRef: Pick<Document, 'createElement'> = document,
  store: TimelineStorePort = studioStore,
): StudioTimelineDom {
  const cleanups: Array<() => void> = [];
  let keyCleanups: Array<() => void> = [];

  const root = documentRef.createElement('section');
  root.className = 'timeline';
  root.dataset.hgptTimeline = 'first-party';

  const controls = documentRef.createElement('div');
  controls.className = 'timeline__controls';

  const play = button(documentRef, 'Play');
  play.className = 'primary';
  const previousFrame = button(documentRef, '‹ Frame', 'Previous animation frame (Left Arrow)');
  const nextFrame = button(documentRef, 'Frame ›', 'Next animation frame (Right Arrow)');

  const timeReadout = documentRef.createElement('span');
  timeReadout.className = 'timeline__time';
  const frameReadout = documentRef.createElement('span');
  frameReadout.className = 'timeline__time';

  const speed = documentRef.createElement('select');
  for (const value of SPEEDS) speed.append(option(documentRef, String(value), `${value}×`));

  const loop = documentRef.createElement('input');
  loop.type = 'checkbox';
  const loopField = documentRef.createElement('label');
  loopField.className = 'field field--inline field--check';
  const loopText = documentRef.createElement('span');
  loopText.textContent = 'Loop';
  loopField.append(loop, loopText);

  const rangeControls = documentRef.createElement('div');
  rangeControls.className = 'timeline__range-controls';
  rangeControls.setAttribute('aria-label', 'Loop range controls');
  const setIn = button(documentRef, 'Set In', 'Set loop start to playhead');
  const setOut = button(documentRef, 'Set Out', 'Set loop end to playhead');
  const clearRange = button(documentRef, 'Clear range');
  const rangeReadout = documentRef.createElement('span');
  rangeReadout.className = 'timeline__range-readout';
  rangeControls.append(setIn, setOut, clearRange, rangeReadout);

  const duration = documentRef.createElement('input');
  duration.type = 'number';
  duration.min = '0.5';
  duration.max = '30';
  duration.step = '0.1';

  const spacer = documentRef.createElement('div');
  spacer.className = 'timeline__spacer';

  const setKeyframe = button(documentRef, 'Set keyframe');
  const deleteKeyframe = button(documentRef, 'Delete keyframe');

  const marker = documentRef.createElement('select');
  marker.append(option(documentRef, '', 'None'));
  for (const [kind, label] of Object.entries(POSE_MARKER_LABELS)) {
    marker.append(option(documentRef, kind, label));
  }
  const markerField = field(documentRef, 'Marker', marker);

  const easing = documentRef.createElement('select');
  for (const [kind, label] of Object.entries(EASING_LABELS)) {
    easing.append(option(documentRef, kind, label));
  }
  const easingField = field(documentRef, 'Easing', easing);

  controls.append(
    play, previousFrame, nextFrame, timeReadout, frameReadout,
    field(documentRef, 'Speed', speed), loopField, rangeControls,
    field(documentRef, 'Duration', duration), spacer,
    setKeyframe, deleteKeyframe, markerField, easingField,
  );

  const track = documentRef.createElement('div');
  track.className = 'timeline__track';
  const loopRangeElement = documentRef.createElement('div');
  loopRangeElement.className = 'timeline__loop-range';
  const playhead = documentRef.createElement('div');
  playhead.className = 'timeline__playhead';
  root.append(controls, track);

  let structuralClip: StudioClip | null = null;
  let structuralExercise: ExerciseDefinition | null = null;
  let keyElements: Array<{ frame: Keyframe; element: HTMLButtonElement }> = [];

  const clearKeyListeners = () => {
    for (const cleanup of keyCleanups) cleanup();
    keyCleanups = [];
  };

  const rebuildTrack = (state: StudioState) => {
    const clip = state.document.clip;
    const exercise = state.document.exercise;
    structuralClip = clip;
    structuralExercise = exercise;
    keyElements = [];
    clearKeyListeners();

    const children: HTMLElement[] = [];
    for (const { phase, start, end } of phaseBoundaries(exercise)) {
      const element = documentRef.createElement('div');
      element.className = 'timeline__phase';
      element.style.left = `${(start / clip.duration) * 100}%`;
      element.style.width = `${((end - start) / clip.duration) * 100}%`;
      element.style.background = PHASE_COLOURS[phase.contraction] ?? '#333a45';
      element.title = `${phase.label} — ${(end - start).toFixed(2)}s ${phase.contraction}`;
      const label = documentRef.createElement('span');
      label.textContent = phase.label;
      element.append(label);
      children.push(element);
    }

    children.push(loopRangeElement);

    for (const frame of sortedKeyframes(clip)) {
      const element = button(documentRef, '');
      element.className = 'timeline__key';
      if (frame.marker) {
        element.classList.add('has-marker', `marker-${frame.marker}`);
        element.dataset.markerLabel = POSE_MARKER_LABELS[frame.marker];
      }
      element.style.left = `${(frame.time / clip.duration) * 100}%`;
      element.title = `${frame.marker ? `${POSE_MARKER_LABELS[frame.marker]} · ` : ''}${frame.label ?? 'Keyframe'} at ${frame.time.toFixed(2)}s`;
      const onPointerDown = (event: PointerEvent) => {
        event.stopPropagation();
        store.getState().setTime(frame.time);
      };
      element.addEventListener('pointerdown', onPointerDown);
      keyCleanups.push(() => element.removeEventListener('pointerdown', onPointerDown));
      keyElements.push({ frame, element });
      children.push(element);
    }

    children.push(playhead);
    track.replaceChildren(...children);
  };

  const sync = () => {
    const state = store.getState();
    const clip = state.document.clip;
    if (clip !== structuralClip || state.document.exercise !== structuralExercise) rebuildTrack(state);

    const current = currentKeyframe(clip, state.time);
    play.textContent = state.playing ? 'Pause' : 'Play';
    previousFrame.disabled = state.time <= 0;
    nextFrame.disabled = state.time >= clip.duration;
    timeReadout.textContent = `${state.time.toFixed(2)}s / ${clip.duration.toFixed(2)}s`;
    frameReadout.textContent = `${Math.round(state.time * clip.fps)}f / ${Math.round(clip.duration * clip.fps)}f`;
    speed.value = String(state.speed);
    loop.checked = state.loop;
    duration.value = String(clip.duration);

    clearRange.disabled = !state.loopRange;
    rangeReadout.hidden = !state.loopRange;
    rangeReadout.textContent = state.loopRange
      ? `${state.loopRange.start.toFixed(2)}–${state.loopRange.end.toFixed(2)}s`
      : '';

    loopRangeElement.hidden = !state.loopRange;
    loopRangeElement.classList.toggle('is-active', Boolean(state.loopRange && state.loop));
    if (state.loopRange) {
      loopRangeElement.style.left = `${(state.loopRange.start / clip.duration) * 100}%`;
      loopRangeElement.style.width = `${((state.loopRange.end - state.loopRange.start) / clip.duration) * 100}%`;
      loopRangeElement.title = `Loop range ${state.loopRange.start.toFixed(2)}–${state.loopRange.end.toFixed(2)}s`;
    }

    deleteKeyframe.disabled = !current || clip.keyframes.length <= 2;
    markerField.hidden = !current;
    easingField.hidden = !current;
    marker.value = current?.marker ?? '';
    easing.value = current?.easing ?? 'lift';
    for (const entry of keyElements) {
      entry.element.classList.toggle('is-current', entry.frame.id === current?.id);
    }
    playhead.style.left = `${(state.time / clip.duration) * 100}%`;
  };

  const onPlay = () => store.getState().togglePlay();
  const stepFrame = (frames: number) => {
    const state = store.getState();
    state.pause();
    state.setTime(state.time + frames / state.document.clip.fps);
  };
  const onSpeed = () => store.getState().setSpeed(Number(speed.value));
  const onLoop = () => store.getState().setLoop(loop.checked);
  const onSetIn = () => {
    const state = store.getState();
    const oneFrame = 1 / state.document.clip.fps;
    const end = Math.max(state.loopRange?.end ?? state.document.clip.duration, state.time + oneFrame);
    state.setLoopRange({ start: state.time, end });
    state.setLoop(true);
  };
  const onSetOut = () => {
    const state = store.getState();
    const oneFrame = 1 / state.document.clip.fps;
    const start = Math.min(state.loopRange?.start ?? 0, state.time - oneFrame);
    state.setLoopRange({ start, end: state.time });
    state.setLoop(true);
  };
  const onDeleteKeyframe = () => {
    const state = store.getState();
    const current = currentKeyframe(state.document.clip, state.time);
    if (current) state.deleteKeyframe(current.id);
  };
  const onMarker = () => {
    const state = store.getState();
    const current = currentKeyframe(state.document.clip, state.time);
    if (current) state.setKeyframeMarker(current.id, marker.value ? (marker.value as PoseMarkerKind) : null);
  };
  const onEasing = () => {
    const state = store.getState();
    const current = currentKeyframe(state.document.clip, state.time);
    if (current) state.setKeyframeEasing(current.id, easing.value as EasingKind);
  };
  const scrub = (event: PointerEvent) => {
    const bounds = track.getBoundingClientRect();
    if (bounds.width <= 0) return;
    const ratio = (event.clientX - bounds.left) / bounds.width;
    store.getState().setTime(Math.max(0, Math.min(1, ratio)) * store.getState().document.clip.duration);
  };
  const onPointerDown = (event: PointerEvent) => {
    track.setPointerCapture?.(event.pointerId);
    scrub(event);
  };
  const onPointerMove = (event: PointerEvent) => {
    if (event.buttons === 1) scrub(event);
  };

  const listeners: Array<[EventTarget, string, EventListener]> = [
    [play, 'click', onPlay],
    [previousFrame, 'click', () => stepFrame(-1)],
    [nextFrame, 'click', () => stepFrame(1)],
    [speed, 'change', onSpeed],
    [loop, 'change', onLoop],
    [setIn, 'click', onSetIn],
    [setOut, 'click', onSetOut],
    [clearRange, 'click', () => store.getState().setLoopRange(null)],
    [duration, 'change', () => store.getState().setDuration(Number(duration.value))],
    [setKeyframe, 'click', () => store.getState().setKeyframe()],
    [deleteKeyframe, 'click', onDeleteKeyframe],
    [marker, 'change', onMarker],
    [easing, 'change', onEasing],
    [track, 'pointerdown', onPointerDown as EventListener],
    [track, 'pointermove', onPointerMove as EventListener],
  ];
  for (const [target, type, listener] of listeners) {
    target.addEventListener(type, listener);
    cleanups.push(() => target.removeEventListener(type, listener));
  }

  const unsubscribe = store.subscribe(sync);
  sync();

  let disposed = false;
  return {
    element: root,
    controls: {
      play, previousFrame, nextFrame, timeReadout, frameReadout, speed, loop,
      setIn, setOut, clearRange, rangeReadout, duration, setKeyframe,
      deleteKeyframe, marker, easing, track, playhead,
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      unsubscribe();
      clearKeyListeners();
      for (const cleanup of cleanups.splice(0)) cleanup();
    },
  };
}
