import type { ObservableStore } from '../../core/observableStore';
import { resolveFrame } from '../../animation/pipeline';
import { anatomicalGripOffset } from '../../equipment/attach';
import { GRIP_CLOSURE_PRESETS, measureGripFit, measureTwoHandFit } from '../../equipment/gripDiagnostics';
import { equipmentSocketForInstance } from '../../equipment/library';
import { GRIP_PROFILE_LIST } from '../../exercises/gripProfiles';
import { FINGERS } from '../../rig/boneNames';
import { PoseEvaluation } from '../../rig/skeleton';
import { skeleton } from '../storeCore';
import { scanGripWorstCases } from '../gripReview';
import { studioStore, type StudioState } from '../storeCore';

type DocumentPort = Pick<Document, 'createElement'>;
type StudioPort = Pick<ObservableStore<StudioState>, 'getState' | 'subscribe'>;
export interface GripPanelDom { element: HTMLElement; dispose(): void }

/** Grip authoring and production fit diagnostics over the existing Studio actions. */
export function createGripPanelDom(documentRef: DocumentPort = document, store: StudioPort = studioStore): GripPanelDom {
  const root = documentRef.createElement('section');
  root.className = 'panel grip-panel'; root.dataset.hgptPanel = 'grip-first-party';
  let digitsOpen = false;
  const node = (tag: string, cls?: string, value?: string): HTMLElement => {
    const item = documentRef.createElement(tag);
    if (cls) item.className = cls;
    if (value !== undefined) item.textContent = value;
    return item;
  };
  const button = (label: string, action: () => void, id?: string): HTMLButtonElement => {
    const item = documentRef.createElement('button'); item.type = 'button'; item.textContent = label;
    if (id) item.dataset.hgptGripControl = id;
    item.addEventListener('click', action); return item;
  };
  const row = (label: string, control: HTMLElement): HTMLElement => {
    const item = node('label', 'field'); item.append(node('span', 'field__label', label), control); return item;
  };
  const input = (kind: 'number' | 'range', value: number, step: number, id: string, action: (value: number) => void, min?: number, max?: number): HTMLInputElement => {
    const item = documentRef.createElement('input'); item.type = kind; item.step = String(step); item.value = String(value);
    if (min !== undefined) item.min = String(min);
    if (max !== undefined) item.max = String(max);
    item.dataset.hgptGripControl = id;
    item.addEventListener('change', () => action(Number(item.value)));
    return item;
  };
  const spec = (pairs: [string, string][]): HTMLElement => {
    const list = node('dl', 'spec-list');
    for (const [label, value] of pairs) list.append(node('dt', undefined, label), node('dd', undefined, value));
    return list;
  };
  let measuredClip: StudioState['document']['clip'] | null = null;
  let measuredInstances: StudioState['document']['exercise']['equipment']['instances'] | null = null;
  let measuredTime = Number.NaN;
  let frame: ReturnType<typeof resolveFrame> | null = null;
  let evaluation: PoseEvaluation | null = null;
  let worstClip: StudioState['document']['clip'] | null = null;
  let worst = new Map<ReturnType<typeof scanGripWorstCases>[number]['instanceId'], ReturnType<typeof scanGripWorstCases>[number]>();

  const render = () => {
    const state = store.getState();
    const exercise = state.document.exercise;
    const clip = state.document.clip;
    const time = state.time;
    const instances = exercise.equipment.instances;
    if (measuredClip !== clip || measuredInstances !== instances || measuredTime !== time || !frame || !evaluation) {
      measuredClip = clip; measuredInstances = instances; measuredTime = time;
      evaluation = new PoseEvaluation(skeleton);
      frame = resolveFrame(skeleton, evaluation, clip, time);
      evaluation.apply(frame.pose);
    }
    if (worstClip !== clip) {
      worstClip = clip;
      worst = new Map(scanGripWorstCases(skeleton, clip).map((sweep) => [sweep.instanceId, sweep]));
    }
    const children: HTMLElement[] = [node('h2', undefined, 'Grip'), node('p', 'panel__hint', 'Tune the generated hand closure here. Individual thumb and finger segments remain available in Joint → Show individual finger joints for final contact corrections.'), node('h3', undefined, 'Hand shape')];
    const profile = documentRef.createElement('select');
    profile.dataset.hgptGripControl = 'profile';
    for (const item of GRIP_PROFILE_LIST) {
      const option = documentRef.createElement('option'); option.value = item.id; option.textContent = item.label; profile.append(option);
    }
    profile.value = exercise.hands.gripPreset ?? exercise.hands.grip;
    profile.addEventListener('change', () => {
      const value = profile.value as typeof exercise.hands.grip;
      store.getState().setGripPreset(value === exercise.hands.grip ? null : value);
    });
    children.push(row('Grip profile', profile));
    const semantic = node('p', 'panel__note');
    semantic.append(node('span', undefined, 'The exercise still records its semantic grip as '), node('strong', undefined, exercise.hands.grip), node('span', undefined, '. This selector only overrides the generated finger/thumb shape for authoring.'));
    children.push(semantic, node('h3', undefined, 'Closure'));
    children.push(row(`Finger closure · ${Math.round(exercise.hands.closure * 100)}%`, input('range', exercise.hands.closure, 0.01, 'closure', (value) => store.getState().setGripClosure(value), 0, 1)));
    const presets = node('div', 'button-row grip-presets');
    for (const preset of GRIP_CLOSURE_PRESETS) {
      const control = button(`${preset.label} ${Math.round(preset.closure * 100)}%`, () => store.getState().setGripClosure(preset.closure), `preset-${preset.id}`);
      control.className = Math.abs(exercise.hands.closure - preset.closure) < 1e-6 ? 'is-active' : '';
      presets.append(control);
    }
    children.push(presets, node('p', 'panel__note', 'Presets only change deterministic finger closure; they do not move the wrist, equipment or accepted arm animation. Changes remain undoable.'), node('h4', undefined, 'Fine closure A/B'));
    const fine = node('div', 'button-row grip-presets');
    for (const closure of [0.65, 0.7, 0.75, 0.8, 0.85]) {
      const control = button(`${Math.round(closure * 100)}%`, () => store.getState().setGripClosure(closure), `fine-${closure}`);
      control.className = Math.abs(exercise.hands.closure - closure) < 1e-6 ? 'is-active' : '';
      fine.append(control);
    }
    children.push(fine, node('p', 'panel__note', 'Fine presets leave the playhead untouched, so thumb opposition, finger wrap and palm loading can be compared on the exact same pose.'));
    if (exercise.id === 'dumbbell_bicep_curl') {
      children.push(node('h4', undefined, 'Curl review frames'));
      const frames = node('div', 'button-row grip-presets');
      for (const point of [{ label: 'Bottom', time: 0 }, { label: 'Mid lift', time: 1 }, { label: 'Peak', time: 2 }, { label: 'Mid lower', time: 4 }, { label: 'Return', time: 5 }]) {
        const control = button(point.label, () => store.getState().setTime(point.time), `frame-${point.label}`);
        control.className = Math.abs(time - point.time) < 1 / Math.max(1, clip.fps) ? 'is-active' : '';
        frames.append(control);
      }
      children.push(frames, node('p', 'panel__note', 'Review the same closure at bottom, mid-concentric, peak, mid-eccentric and return before accepting a permanent grip change.'));
    }
    const details = node('details', 'grip-digit-details') as HTMLDetailsElement;
    details.open = digitsOpen;
    details.addEventListener('toggle', () => { digitsOpen = details.open; });
    details.append(node('summary', undefined, 'Fine-tune individual digits'), node('p', 'panel__hint', 'Use these only when one digit needs less or more wrap. Unchanged digits continue to follow the global closure above, so the authored grip profile stays deterministic.'));
    for (const finger of FINGERS) {
      const overridden = exercise.hands.digitClosure?.[finger];
      const value = overridden ?? exercise.hands.closure;
      details.append(row(`${finger.charAt(0).toUpperCase() + finger.slice(1)} · ${Math.round(value * 100)}%${overridden !== undefined ? ' · custom' : ''}`, input('range', value, 0.01, `digit-${finger}`, (closure) => store.getState().setGripDigitClosure(finger, closure), 0, 1)));
    }
    const digitActions = node('div', 'button-row');
    const resetDigits = button('Reset all digits to global closure', () => store.getState().clearGripDigitClosures(), 'reset-digits');
    resetDigits.disabled = !exercise.hands.digitClosure;
    digitActions.append(resetDigits); details.append(digitActions); children.push(details);

    children.push(node('h3', undefined, 'Current handle fit'));
    const oneHand = instances.flatMap((instance) => {
      if (instance.attachment.mode !== 'hand') return [];
      const transform = frame!.equipment.get(instance.id);
      if (!transform) return [];
      return [{ instance, label: instance.label ?? instance.id,
        offset: instance.attachment.gripOffset ?? anatomicalGripOffset(instance.attachment.side),
        customOffset: Boolean(instance.attachment.gripOffset),
        rotation: instance.attachment.gripRotation ?? { x: 0, y: 0, z: 0 },
        customRotation: Boolean(instance.attachment.gripRotation),
        fit: measureGripFit(evaluation!, transform, instance.attachment.side),
      }];
    });
    if (oneHand.length) {
      const list = node('div', 'grip-fit-list');
      for (const { instance, label, offset, customOffset, rotation, customRotation, fit } of oneHand) {
        const id = instance.id;
        const card = node('div', 'grip-fit');
        const head = node('div', 'grip-fit__head');
        head.append(node('strong', undefined, label), node('span', fit.withinEnvelope ? 'status-ok' : 'status-warn', fit.withinEnvelope ? 'Within envelope' : 'Review fit'));
        card.append(head);
        const offsets = node('div', 'grip-offset-grid');
        for (const axis of ['x', 'y', 'z'] as const) {
          offsets.append(row(`Grip ${axis.toUpperCase()} · mm`, input('number', Math.round(offset[axis] * 1000), 1, `${id}-offset-${axis}`, (millimetres) => {
            store.getState().setEquipmentGripOffset(id, { ...offset, [axis]: millimetres / 1000 });
          })));
        }
        card.append(offsets, node('h4', undefined, 'Handle orientation'));
        const orientations = node('div', 'grip-offset-grid');
        for (const axis of ['x', 'y', 'z'] as const) {
          orientations.append(row(`Grip ${axis.toUpperCase()} · °`, input('number', Number(rotation[axis].toFixed(1)), 1, `${id}-rotation-${axis}`, (degrees) => {
            store.getState().setEquipmentGripRotation(id, { ...rotation, [axis]: degrees });
          })));
        }
        card.append(orientations);
        const actions = node('div', 'button-row');
        const resetOffset = button('Reset anatomical centre', () => store.getState().setEquipmentGripOffset(id, null), `${id}-reset-offset`);
        resetOffset.disabled = !customOffset;
        const resetRotation = button('Reset orientation', () => store.getState().setEquipmentGripRotation(id, null), `${id}-reset-rotation`);
        resetRotation.disabled = !customRotation;
        actions.append(resetOffset, resetRotation);
        card.append(actions, spec([
          ['Contact reach used', `${Math.round(fit.reachUse * 100)}%`],
          ['Wrap coverage', `${fit.wrapCoverageDeg.toFixed(1)}°`],
          ['Largest open gap', `${fit.widestGapDeg.toFixed(1)}°`],
        ]), node('h4', undefined, 'Digit reach'));
        const reach = node('dl', 'spec-list');
        for (const finger of FINGERS) {
          const pair = node('div', 'spec-list__pair');
          const digit = fit.digitReachUse[finger];
          pair.append(node('dt', undefined, finger.charAt(0).toUpperCase() + finger.slice(1)), node('dd', digit >= 1 ? 'status-warn' : undefined, `${Math.round(digit * 100)}%`));
          reach.append(pair);
        }
        card.append(reach);
        const sweep = worst.get(id);
        if (sweep) {
          card.append(node('h4', undefined, 'Worst points in rep'));
          const points = node('div', 'button-row grip-worst-points');
          for (const finger of FINGERS) {
            const worstPoint = sweep.digits[finger];
            const jump = button(`${finger.charAt(0).toUpperCase() + finger.slice(1)} · ${Math.round(worstPoint.reachUse * 100)}% · ${worstPoint.time.toFixed(2)}s`, () => store.getState().setTime(worstPoint.time), `${id}-worst-${finger}`);
            jump.className = worstPoint.reachUse >= 1 ? 'status-warn' : '';
            jump.title = `Jump to ${finger} worst point`;
            points.append(jump);
          }
          card.append(points, node('p', 'panel__note', `Frame-by-frame at ${clip.fps} fps. Tap a digit to inspect its worst measured frame.`));
        }
        list.append(card);
      }
      children.push(list);
    } else children.push(node('p', 'panel__empty', 'This exercise has no single-hand cylindrical equipment attachment to measure at the playhead.'));
    children.push(node('p', 'panel__hint', 'Grip X/Y/Z is the handle centre in hand-local millimetres; orientation is a hand-local Euler calibration in degrees. “Within envelope” and each digit percentage use the same contact-reach and wrap geometry as the Studio\'s grip regression. Whole-rep worst points scan every authored animation frame at the clip FPS. A digit above 100% has exceeded that authored geometric envelope; this is not a literal mesh-penetration, force or injury-safety score.'));

    const twoHand = instances.flatMap((instance) => {
      if (instance.attachment.mode !== 'hands') return [];
      const transform = frame!.equipment.get(instance.id);
      if (!transform) return [];
      const fit = measureTwoHandFit(evaluation!, instance, transform);
      const left = equipmentSocketForInstance(instance, instance.attachment.leftSocket);
      const right = equipmentSocketForInstance(instance, instance.attachment.rightSocket);
      if (!fit || !left || !right) return [];
      return [{ instance, label: instance.label ?? instance.id, fit,
        width: Math.hypot(right.position.x - left.position.x, right.position.y - left.position.y, right.position.z - left.position.z),
        roll: instance.attachment.gripRoll ?? 0,
        hasWidthOverride: Boolean(instance.socketOverrides?.[instance.attachment.leftSocket]?.position || instance.socketOverrides?.[instance.attachment.rightSocket]?.position),
      }];
    });
    if (twoHand.length) {
      children.push(node('h3', undefined, 'Two-hand rigid fit'));
      const list = node('div', 'grip-fit-list');
      for (const { instance, label, fit, width, roll, hasWidthOverride } of twoHand) {
        const id = instance.id;
        const card = node('div', 'grip-fit');
        const head = node('div', 'grip-fit__head');
        head.append(node('strong', undefined, label), node('span', fit.withinEnvelope ? 'status-ok' : 'status-warn', fit.withinEnvelope ? 'Sockets aligned' : 'Calibrate spacing'));
        card.append(head);
        const grid = node('div', 'grip-offset-grid');
        grid.append(row('Grip width · cm', input('number', Number((width * 100).toFixed(1)), 1, `${id}-width`, (cm) => store.getState().setTwoHandGripWidth(id, cm / 100), 10, 200)));
        grid.append(row('Bar roll · °', input('number', Number(roll.toFixed(1)), 1, `${id}-roll`, (degrees) => store.getState().setTwoHandGripRoll(id, degrees))));
        card.append(grid);
        const actions = node('div', 'button-row');
        const resetWidth = button('Reset grip width', () => store.getState().setTwoHandGripWidth(id, null), `${id}-reset-width`);
        resetWidth.disabled = !hasWidthOverride;
        const resetRoll = button('Reset roll', () => store.getState().setTwoHandGripRoll(id, null), `${id}-reset-roll`);
        resetRoll.disabled = Math.abs(roll) < 1e-9;
        actions.append(resetWidth, resetRoll);
        card.append(actions, spec([
          ['Left socket error', `${(fit.leftError * 1000).toFixed(1)} mm`],
          ['Right socket error', `${(fit.rightError * 1000).toFixed(1)} mm`],
          ['Hands separation', `${(fit.targetSeparation * 100).toFixed(1)} cm`],
          ['Socket separation', `${(fit.socketSeparation * 100).toFixed(1)} cm`],
        ]));
        list.append(card);
      }
      children.push(list, node('p', 'panel__hint', 'Two-hand equipment is always rigid. Grip width moves only the authored contact sockets along the item; the solver never scales the bar or moves wrists/shoulders to hide a mismatch.'));
    }
    root.replaceChildren(...children);
    const currentDetails = root.querySelector?.('.grip-digit-details') as HTMLDetailsElement | null;
    if (currentDetails) currentDetails.open = digitsOpen;
  };
  const unsubscribe = store.subscribe(render);
  render();
  let disposed = false;
  return { element: root, dispose() { if (disposed) return; disposed = true; unsubscribe(); } };
}
