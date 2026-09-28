import type { ObservableStore } from '../../core/observableStore';
import { toDeg } from '../../core/math';
import { boneLabel, type BoneName } from '../../rig/boneNames';
import type { Pose } from '../../rig/types';
import { frontPoseDiagram, type PoseSnapshot } from '../comparison';
import { studioStore, type StudioState } from '../storeCore';

type DocumentPort = Pick<Document, 'createElement' | 'createElementNS'>;
type ComparisonStorePort = Pick<ObservableStore<StudioState>, 'getState' | 'subscribe'>;

export interface ComparisonPanelControls {
  captureA: HTMLButtonElement;
  captureB: HTMLButtonElement;
  clear: HTMLButtonElement;
}

export interface ComparisonPanelElements {
  aCard: HTMLDivElement;
  bCard: HTMLDivElement;
  detail: HTMLDivElement;
}

export interface ComparisonPanelDom {
  element: HTMLElement;
  controls: ComparisonPanelControls;
  elements: ComparisonPanelElements;
  dispose(): void;
}

const SVG_NS = ['http:', '', 'www.w3.org', '2000', 'svg'].join('/');

const rotation = (pose: Pose, bone: BoneName) =>
  pose.rotations[bone] ?? { x: 0, y: 0, z: 0 };

const createButton = (
  documentRef: DocumentPort,
  label: string,
): HTMLButtonElement => {
  const button = documentRef.createElement('button');
  button.type = 'button';
  button.textContent = label;
  return button;
};

const renderPoseCard = (
  documentRef: DocumentPort,
  card: HTMLDivElement,
  snapshot: PoseSnapshot | null,
  title: string,
): void => {
  const head = documentRef.createElement('div');
  head.className = 'comparison-card__head';
  const heading = documentRef.createElement('strong');
  heading.textContent = title;
  head.append(heading);

  if (snapshot) {
    const time = documentRef.createElement('span');
    time.textContent =
      `${snapshot.time.toFixed(2)}s${snapshot.marker ? ` · ${snapshot.marker}` : ''}`;
    head.append(time);

    const svg = documentRef.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('class', 'comparison-card__diagram');
    svg.setAttribute('viewBox', '0 0 160 220');
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', `${title} pose`);

    for (const line of frontPoseDiagram(snapshot.pose)) {
      const element = documentRef.createElementNS(SVG_NS, 'line');
      element.setAttribute('data-bone', line.bone);
      element.setAttribute('x1', String(line.x1 * 160));
      element.setAttribute('y1', String(line.y1 * 220));
      element.setAttribute('x2', String(line.x2 * 160));
      element.setAttribute('y2', String(line.y2 * 220));
      svg.append(element);
    }
    card.replaceChildren(head, svg);
    return;
  }

  const empty = documentRef.createElement('div');
  empty.className = 'comparison-card__empty';
  empty.textContent = 'Capture a pose at the playhead.';
  card.replaceChildren(head, empty);
};

/**
 * React-free Pose A/B review surface. Comparison snapshots remain review-only:
 * actions delegate directly to the existing Studio comparison state and never
 * edit the document or undo history.
 */
export function createComparisonPanelDom(
  documentRef: DocumentPort = document,
  store: ComparisonStorePort = studioStore,
): ComparisonPanelDom {
  const root = documentRef.createElement('section');
  root.className = 'panel comparison-panel';
  root.dataset.hgptPanel = 'compare-first-party';

  const heading = documentRef.createElement('h2');
  heading.textContent = 'Pose A/B';

  const note = documentRef.createElement('p');
  note.className = 'muted';
  note.textContent =
    'Reference and candidate snapshots are review-only. Capturing them never edits the clip or its undo history.';

  const buttons = documentRef.createElement('div');
  buttons.className = 'button-row';
  const captureA = createButton(documentRef, 'Capture A');
  const captureB = createButton(documentRef, 'Capture B');
  const clear = createButton(documentRef, 'Clear both');
  buttons.append(captureA, captureB, clear);

  const grid = documentRef.createElement('div');
  grid.className = 'comparison-grid';
  const aCard = documentRef.createElement('div');
  aCard.className = 'comparison-card';
  const bCard = documentRef.createElement('div');
  bCard.className = 'comparison-card';
  grid.append(aCard, bCard);

  const detail = documentRef.createElement('div');

  root.append(heading, note, buttons, grid, detail);

  const render = () => {
    const state = store.getState();
    const a = state.comparison.a;
    const b = state.comparison.b;
    const selectedBone = state.selection.bone;

    clear.disabled = !a && !b;
    renderPoseCard(documentRef, aCard, a, 'A · Reference');
    renderPoseCard(documentRef, bCard, b, 'B · Candidate');

    if (selectedBone && a && b) {
      const angles = {
        a: rotation(a.pose, selectedBone),
        b: rotation(b.pose, selectedBone),
      };
      const delta = documentRef.createElement('div');
      delta.className = 'comparison-delta';
      const deltaHeading = documentRef.createElement('h3');
      deltaHeading.textContent = `${boneLabel(selectedBone)} angles`;

      const values = documentRef.createElement('div');
      values.className = 'comparison-delta__grid';
      for (const label of ['Axis', 'A', 'B', 'Δ']) {
        const span = documentRef.createElement('span');
        span.textContent = label;
        values.append(span);
      }

      for (const axis of ['x', 'y', 'z'] as const) {
        const aDeg = toDeg(angles.a[axis]);
        const bDeg = toDeg(angles.b[axis]);
        const row = documentRef.createElement('div');
        row.className = 'comparison-delta__row';
        for (const value of [
          axis.toUpperCase(),
          `${aDeg.toFixed(1)}°`,
          `${bDeg.toFixed(1)}°`,
          `${(bDeg - aDeg).toFixed(1)}°`,
        ]) {
          const span = documentRef.createElement('span');
          span.textContent = value;
          row.append(span);
        }
        values.append(row);
      }

      delta.append(deltaHeading, values);
      detail.replaceChildren(delta);
    } else if (!selectedBone && a && b) {
      const hint = documentRef.createElement('p');
      hint.className = 'muted';
      hint.textContent = 'Select a joint to see exact A/B angle differences.';
      detail.replaceChildren(hint);
    } else {
      detail.replaceChildren();
    }
  };

  const onCaptureA = () => store.getState().captureComparison('a');
  const onCaptureB = () => store.getState().captureComparison('b');
  const onClear = () => store.getState().clearComparison();
  captureA.addEventListener('click', onCaptureA);
  captureB.addEventListener('click', onCaptureB);
  clear.addEventListener('click', onClear);

  const unsubscribe = store.subscribe(render);
  render();

  let disposed = false;
  return {
    element: root,
    controls: { captureA, captureB, clear },
    elements: { aCard, bCard, detail },
    dispose() {
      if (disposed) return;
      disposed = true;
      unsubscribe();
      captureA.removeEventListener('click', onCaptureA);
      captureB.removeEventListener('click', onCaptureB);
      clear.removeEventListener('click', onClear);
    },
  };
}
