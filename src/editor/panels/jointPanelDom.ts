import type { ObservableStore } from '../../core/observableStore';
import { sortedKeyframes, sampleClip } from '../../animation/clip';
import { EASING_LABELS } from '../../animation/easing';
import { toDeg, toRad } from '../../core/math';
import { boneLabel, isFingerBone, mirrorBoneName, type BoneName } from '../../rig/boneNames';
import { AXES, type Axis } from '../../rig/types';
import type { EasingKind, PhaseJointTiming } from '../../exercises/types';
import { skeleton } from '../store';
import { studioStore, type StudioState } from '../storeCore';
import { measureJointMotion, measureJointTransitions, measureBilateralMotionSymmetry, measureJointPath } from '../motionDiagnostics';
import { measureJointCoordination } from '../coordinationDiagnostics';

type DocumentPort = Pick<Document, 'createElement'>;
type StudioPort = Pick<ObservableStore<StudioState>, 'getState' | 'subscribe'>;
export interface JointPanelDom { element: HTMLElement; dispose(): void }

/** Limit-aware joint editor and diagnostics backed by the existing Studio actions. */
export function createJointPanelDom(documentRef: DocumentPort = document, store: StudioPort = studioStore): JointPanelDom {
  const root = documentRef.createElement('section');
  root.className = 'panel';
  root.dataset.hgptPanel = 'joint-first-party';
  let showFingerJoints = false;
  let cachedClip: StudioState['document']['clip'] | null = null;
  let cachedBone: BoneName | null = null;
  let cachedMotion: ReturnType<typeof measureJointMotion> | null = null;
  let cachedTransitions: ReturnType<typeof measureJointTransitions> | null = null;
  let cachedBilateral: ReturnType<typeof measureBilateralMotionSymmetry> | null = null;
  let cachedPath: ReturnType<typeof measureJointPath> | null = null;
  const node = (tag: string, cls?: string, value?: string): HTMLElement => {
    const item = documentRef.createElement(tag);
    if (cls) item.className = cls;
    if (value !== undefined) item.textContent = value;
    return item;
  };
  const button = (label: string, action: () => void, id?: string): HTMLButtonElement => {
    const item = documentRef.createElement('button');
    item.type = 'button'; item.textContent = label;
    if (id) item.dataset.hgptJointControl = id;
    item.addEventListener('click', action);
    return item;
  };
  const row = (label: string, control: HTMLElement, cls = 'field'): HTMLElement => {
    const item = node('label', cls);
    item.append(node('span', 'field__label', label), control);
    return item;
  };
  const spec = (entries: [string, string][]): HTMLElement => {
    const list = node('dl', 'spec-list');
    for (const [key, value] of entries) list.append(node('dt', undefined, key), node('dd', undefined, value));
    return list;
  };
  const numberInput = (value: number, min: number, max: number, step: number, id: string, action: (value: number) => void): HTMLInputElement => {
    const input = documentRef.createElement('input');
    input.type = 'number'; input.value = String(value); input.min = String(min); input.max = String(max); input.step = String(step);
    input.dataset.hgptJointControl = id;
    input.addEventListener('change', () => action(Number(input.value)));
    return input;
  };
  const rangeInput = (value: number, min: number, max: number, step: number, id: string, action: (value: number) => void): HTMLInputElement => {
    const input = documentRef.createElement('input');
    input.type = 'range'; input.value = String(value); input.min = String(min); input.max = String(max); input.step = String(step);
    input.dataset.hgptJointControl = id;
    input.addEventListener('change', () => action(Number(input.value)));
    return input;
  };
  const render = () => {
    const state = store.getState();
    const { clip } = state.document;
    const selected = state.selection.bone;
    const time = state.time;
    const selectedRotation = selected ? sampleClip(clip, time).pose.rotations[selected] : undefined;
    if (cachedClip !== clip || cachedBone !== selected) {
      cachedClip = clip; cachedBone = selected;
      cachedMotion = selected ? measureJointMotion(clip, selected) : null;
      cachedTransitions = selected ? measureJointTransitions(clip, selected) : null;
      cachedBilateral = selected ? measureBilateralMotionSymmetry(clip, skeleton, selected) : null;
      cachedPath = selected ? measureJointPath(clip, skeleton, selected) : null;
    }
    const motion = cachedMotion;
    const transitions = cachedTransitions;
    const bilateral = cachedBilateral;
    const jointPath = cachedPath;
    const frames = sortedKeyframes(clip);
    let segmentIndex = 0;
    for (let i = 0; i < frames.length; i += 1) if (frames[i].time <= time + 1e-9) segmentIndex = i;
    const segmentFrom = frames[segmentIndex];
    const segmentTo = frames[segmentIndex + 1];
    const timing = selected && segmentFrom ? segmentFrom.jointTiming?.[selected] : undefined;
    const oppositeBone = selected ? mirrorBoneName(selected) : null;
    const oppositeTiming = oppositeBone && oppositeBone !== selected && segmentFrom ? segmentFrom.jointTiming?.[oppositeBone] : undefined;
    const timingMatchesOpposite = Boolean(oppositeBone && oppositeBone !== selected &&
      (timing?.delay ?? 0) === (oppositeTiming?.delay ?? 0) &&
      (timing?.finish ?? 1) === (oppositeTiming?.finish ?? 1) &&
      (timing?.easing ?? '') === (oppositeTiming?.easing ?? ''));
    const parentBone = selected ? skeleton.bone(selected).parent : null;
    const coordination = selected && parentBone && segmentFrom && segmentTo
      ? measureJointCoordination(clip, selected, parentBone, segmentFrom.time, segmentTo.time) : null;
    const updateTiming = (patch: Partial<PhaseJointTiming>) => {
      if (!selected || !segmentFrom) return;
      store.getState().setJointTiming(segmentFrom.id, selected, {
        delay: timing?.delay ?? 0, finish: timing?.finish ?? 1,
        ...(timing?.easing ? { easing: timing.easing } : {}), ...patch,
      });
    };
    const children: HTMLElement[] = [node('h2', undefined, 'Joint')];
    const select = documentRef.createElement('select');
    select.dataset.hgptJointControl = 'bone';
    const none = documentRef.createElement('option'); none.value = ''; none.textContent = '— none —'; select.append(none);
    for (const bone of skeleton.names.filter((name) => name !== 'root' && (showFingerJoints || !isFingerBone(name) || name === selected))) {
      const option = documentRef.createElement('option'); option.value = bone; option.textContent = boneLabel(bone); select.append(option);
    }
    select.value = selected ?? '';
    select.addEventListener('change', () => store.getState().selectBone((select.value || null) as BoneName | null));
    children.push(row('Selected bone', select));
    const fingerToggle = documentRef.createElement('input');
    fingerToggle.type = 'checkbox'; fingerToggle.checked = showFingerJoints;
    fingerToggle.dataset.hgptJointControl = 'fingers';
    fingerToggle.addEventListener('change', () => { showFingerJoints = fingerToggle.checked; render(); });
    const fingerRow = node('label', 'field field--check');
    fingerRow.append(fingerToggle, node('span', undefined, 'Show individual finger joints'));
    children.push(fingerRow, node('p', 'panel__hint', 'Fine hand mode exposes all 30 thumb/finger segments. They use the same anatomical limits, keyframing, undo/redo, mirroring and Focus selected camera as the larger joints.'));
    if (selected) {
      children.push(node('div', 'panel__hint', 'Rotations apply to the keyframe under the playhead; editing between keys creates one.'));
      for (const axis of AXES) {
        const limit = skeleton.bone(selected).definition.limits[axis];
        if (!limit) {
          const locked = node('div', 'axis axis--locked');
          locked.append(node('span', 'axis__name', axis.toUpperCase()), node('span', 'axis__locked', `Locked — this joint has no ${axis} axis`));
          children.push(locked); continue;
        }
        const degrees = toDeg(selectedRotation?.[axis] ?? 0);
        const direction = degrees >= 0 ? limit.positive : limit.negative;
        const edit = (value: number) => store.getState().setBoneAxis(selected, axis as Axis, toRad(value));
        const axisNode = node('div', 'axis');
        const head = node('div', 'axis__head');
        const numeric = numberInput(Number(degrees.toFixed(1)), limit.min, limit.max, 1, `axis-${axis}-number`, edit);
        numeric.className = 'axis__number';
        head.append(node('span', 'axis__name', axis.toUpperCase()), node('span', 'axis__direction', direction), numeric, node('span', 'axis__unit', '°'));
        const slider = rangeInput(degrees, limit.min, limit.max, 0.5, `axis-${axis}-slider`, edit);
        slider.className = 'axis__slider';
        const range = node('div', 'axis__range');
        range.append(node('span', undefined, `${limit.min}° ${limit.negative}`), node('span', undefined, `${limit.positive} ${limit.max}°`));
        axisNode.append(head, slider, range); children.push(axisNode);
      }
    } else children.push(node('p', 'panel__empty', 'Click a joint in the viewport, or choose one above, to rotate it.'));

    children.push(node('h3', undefined, 'Motion quality'));
    if (selected && motion) {
      const card = node('div', 'joint-motion-diagnostic');
      card.append(node('p', 'panel__hint', `Frame-by-frame at ${motion.fps} fps using shortest-path joint angles. These are animation diagnostics, not force or injury thresholds.`));
      const readings: [string, string][] = [
        ['Highest angular speed', `${motion.maxSpeed.value.toFixed(1)}°/s · ${motion.maxSpeed.axis.toUpperCase()} · ${motion.maxSpeed.time.toFixed(2)}s`],
        ['Highest angular acceleration', `${motion.maxAcceleration.value.toFixed(0)}°/s² · ${motion.maxAcceleration.axis.toUpperCase()} · ${motion.maxAcceleration.time.toFixed(2)}s`],
        ['Largest keyframe velocity jump', transitions?.maxJump
          ? `${transitions.maxJump.velocityJumpDegPerSec.toFixed(1)}°/s · ${transitions.maxJump.axis.toUpperCase()} · ${transitions.maxJump.time.toFixed(2)}s${transitions.maxJump.label ? ` · ${transitions.maxJump.label}` : ''}`
          : 'No interior keyframe boundary'],
      ];
      if (bilateral) readings.push(['Bilateral mirror mismatch', `${bilateral.maxError.value.toFixed(2)}° max · ${bilateral.rmsErrorDeg.toFixed(2)}° RMS · ${bilateral.maxError.time.toFixed(2)}s`]);
      if (jointPath) readings.push(
        ['Joint drift from parent', `${(jointPath.maxDriftMetres * 1000).toFixed(1)} mm max · ${jointPath.maxDriftTime.toFixed(2)}s`],
        ['Relative joint path', `${(jointPath.pathLengthMetres * 1000).toFixed(1)} mm travelled · ${(jointPath.returnErrorMetres * 1000).toFixed(1)} mm return error`],
      );
      card.append(spec(readings));
      const jumps = node('div', 'button-row');
      jumps.append(button('Jump to fastest frame', () => store.getState().setTime(motion.maxSpeed.time)), button('Jump to sharpest change', () => store.getState().setTime(motion.maxAcceleration.time)));
      if (transitions?.maxJump) jumps.append(button('Jump to worst keyframe transition', () => store.getState().setTime(transitions.maxJump!.time)));
      if (bilateral) jumps.append(button('Jump to worst bilateral mismatch', () => store.getState().setTime(bilateral.maxError.time)));
      if (jointPath) jumps.append(button('Jump to maximum joint drift', () => store.getState().setTime(jointPath.maxDriftTime)));
      card.append(jumps);
      if (transitions?.maxJump) card.append(node('p', 'panel__note', `At that boundary: incoming ${transitions.maxJump.incomingDegPerSec.toFixed(1)}°/s, outgoing ${transitions.maxJump.outgoingDegPerSec.toFixed(1)}°/s. A stop into a hold can be intentional; use this to locate the transition, not as an automatic failure.`));
      if (bilateral) card.append(node('p', 'panel__note', `Bilateral comparison uses the rig's exact mirror transform against ${boneLabel(bilateral.opposite)} at every authored frame. Zero means an exact mirror; asymmetry may still be intentional for unilateral exercises.`));
      if (jointPath) card.append(node('p', 'panel__note', `Spatial drift is the selected joint head relative to ${boneLabel(jointPath.parent)}, so whole-body/root translation is removed. Selecting a forearm measures elbow wander relative to its shoulder; pure elbow flexion alone does not move that joint point.`));
      const details = node('details');
      details.append(node('summary', undefined, 'Per-axis motion'));
      const axesList = node('dl', 'spec-list');
      for (const axis of AXES) {
        const pair = node('div', 'spec-list__pair');
        pair.append(node('dt', undefined, axis.toUpperCase()), node('dd', undefined, `${motion.axes[axis].maxSpeedDegPerSec.toFixed(1)}°/s · ${motion.axes[axis].maxAccelerationDegPerSec2.toFixed(0)}°/s²`));
        axesList.append(pair);
      }
      details.append(axesList); card.append(details); children.push(card);
    } else children.push(node('p', 'panel__empty', 'Select a joint to inspect its motion through the full rep.'));

    children.push(node('h3', undefined, 'Joint coordination'));
    if (selected && parentBone && coordination) {
      const card = node('div', 'joint-coordination');
      const hint = node('p', 'panel__hint');
      hint.append(node('span', undefined, 'Current segment · '), node('strong', undefined, boneLabel(selected)), node('span', undefined, ' compared with its parent'), node('strong', undefined, ` ${boneLabel(parentBone)}`), node('span', undefined, '. Onset is the first meaningful movement, not a pass/fail judgement.'));
      card.append(hint, spec([
        [`${boneLabel(selected)} excursion`, `${coordination.lead.excursionDeg.toFixed(1)}°`],
        [`${boneLabel(selected)} onset`, coordination.lead.onsetPercent === null ? 'Near-isometric' : `${Math.round(coordination.lead.onsetPercent * 100)}% · ${coordination.lead.onsetTime!.toFixed(2)}s`],
        [`${boneLabel(parentBone)} excursion`, `${coordination.support.excursionDeg.toFixed(1)}°`],
        [`${boneLabel(parentBone)} onset`, coordination.support.onsetPercent === null ? 'Near-isometric' : `${Math.round(coordination.support.onsetPercent * 100)}% · ${coordination.support.onsetTime!.toFixed(2)}s`],
        ['Parent onset lag', coordination.onsetLagSeconds === null ? '—' : `${coordination.onsetLagSeconds >= 0 ? '+' : ''}${coordination.onsetLagSeconds.toFixed(2)}s`],
      ]));
      const actions = node('div', 'button-row');
      actions.append(button('Select parent to tune timing', () => store.getState().selectBone(parentBone)));
      if (coordination.support.onsetTime !== null) actions.append(button('Jump to parent onset', () => store.getState().setTime(coordination.support.onsetTime!)));
      card.append(actions, node('p', 'panel__note', 'For a curl, selecting the forearm compares elbow flexion with upper-arm contribution. Use Segment timing on the parent to delay or soften that secondary movement.'));
      children.push(card);
    } else children.push(node('p', 'panel__empty', 'Select a non-root joint before the final keyframe to compare its timing with its parent.'));

    children.push(node('h3', undefined, 'Segment timing'));
    if (selected && segmentFrom && segmentTo) {
      const card = node('div', 'joint-timing');
      const hint = node('p', 'panel__hint');
      hint.append(node('span', undefined, `${segmentFrom.label ?? `${segmentFrom.time.toFixed(2)}s`} → ${segmentTo.label ?? `${segmentTo.time.toFixed(2)}s`}. Timing affects only `), node('strong', undefined, boneLabel(selected)), node('span', undefined, ' in this segment.'));
      card.append(hint);
      const enabled = documentRef.createElement('input');
      enabled.type = 'checkbox'; enabled.checked = Boolean(timing); enabled.dataset.hgptJointControl = 'custom-timing';
      enabled.addEventListener('change', () => store.getState().setJointTiming(segmentFrom.id, selected, enabled.checked ? { delay: 0, finish: 1 } : null));
      const check = node('label', 'field field--check'); check.append(enabled, node('span', undefined, 'Custom timing for this joint')); card.append(check);
      if (timing) {
        card.append(row(`Start delay · ${Math.round((timing.delay ?? 0) * 100)}%`, rangeInput(timing.delay ?? 0, 0, timing.finish ?? 1, 0.01, 'timing-delay', (value) => updateTiming({ delay: value }))));
        card.append(row(`Finish · ${Math.round((timing.finish ?? 1) * 100)}%`, rangeInput(timing.finish ?? 1, timing.delay ?? 0, 1, 0.01, 'timing-finish', (value) => updateTiming({ finish: value }))));
        const easing = documentRef.createElement('select');
        easing.dataset.hgptJointControl = 'timing-easing';
        const fallback = documentRef.createElement('option'); fallback.value = ''; fallback.textContent = `Use phase easing (${EASING_LABELS[segmentFrom.easing]})`; easing.append(fallback);
        for (const [kind, label] of Object.entries(EASING_LABELS)) {
          const option = documentRef.createElement('option'); option.value = kind; option.textContent = label; easing.append(option);
        }
        easing.value = timing.easing ?? '';
        easing.addEventListener('change', () => updateTiming({ easing: (easing.value || undefined) as EasingKind | undefined }));
        card.append(row('Joint easing', easing), node('p', 'panel__note', 'Use this for sequencing secondary joints—such as allowing the elbow to lead before the shoulder joins a curl—without inserting stop/start keyframes.'));
      }
      if (oppositeBone && oppositeBone !== selected) {
        const symmetry = node('div', 'joint-timing-symmetry');
        symmetry.append(node('h4', undefined, 'Left/right timing'));
        const description = node('p', 'panel__hint');
        description.append(node('span', undefined, 'Opposite joint: '), node('strong', undefined, boneLabel(oppositeBone)), node('span', undefined, ' · '), node('span', timingMatchesOpposite ? 'status-ok' : 'status-warn', timingMatchesOpposite ? 'Timing matched' : 'Timing differs'));
        symmetry.append(description);
        const copy = button('Copy selected timing to opposite side', () => store.getState().copyJointTimingToOpposite(segmentFrom.id, selected), 'copy-timing');
        copy.disabled = timingMatchesOpposite;
        symmetry.append(copy, node('p', 'panel__note', 'Copies delay, finish and easing only. Pose angles stay untouched, and the edit uses normal undo/redo history. If this side uses phase-default timing, the opposite side is reset to the same default.'));
        card.append(symmetry);
      }
      children.push(card);
    } else children.push(node('p', 'panel__empty', selected ? 'Move the playhead before the final keyframe to edit timing for a segment.' : 'Select a joint to edit its timing through the current segment.'));

    children.push(node('h3', undefined, 'Pose'));
    const clipboard = node('div', 'button-row');
    clipboard.append(button('Copy pose', () => store.getState().copyPose(), 'copy-pose'));
    const paste = button('Paste pose', () => store.getState().pastePose(), 'paste-pose');
    paste.disabled = state.clipboard === null; clipboard.append(paste); children.push(clipboard);
    const mirror = node('div', 'button-row');
    mirror.append(button('Mirror pose', () => store.getState().mirrorCurrentPose(), 'mirror-pose'), button('Left → right', () => store.getState().mirrorSide('l')), button('Right → left', () => store.getState().mirrorSide('r')));
    children.push(mirror);
    root.replaceChildren(...children);
  };
  const unsubscribe = store.subscribe(render);
  render();
  let disposed = false;
  return { element: root, dispose() { if (disposed) return; disposed = true; unsubscribe(); } };
}
