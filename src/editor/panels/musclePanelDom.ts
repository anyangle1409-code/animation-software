import type { ObservableStore } from '../../core/observableStore';
import { resolveFrame } from '../../animation/pipeline';
import { ACTIVATION_STYLES } from '../../muscles/activation';
import {
  diagnoseMuscles,
  MUSCLE_ACTIVATION_ORDER,
  type MuscleReading,
} from '../../muscles/diagnostics';
import { PoseEvaluation } from '../../rig/skeleton';
import { skeleton, studioStore, type StudioState } from '../storeCore';
import './MusclePanel.css';

const REGIONS = ['all', 'chest', 'shoulders', 'arms', 'back', 'core', 'legs'] as const;
export type MuscleRegionFilter = (typeof REGIONS)[number];

type MuscleStorePort = Pick<ObservableStore<StudioState>, 'getState' | 'subscribe'>;

export interface MusclePanelControls {
  activeOnly: HTMLInputElement;
  region: HTMLSelectElement;
}

export interface MusclePanelElements {
  hint: HTMLDivElement;
  summary: HTMLDivElement;
  list: HTMLUListElement;
  empty: HTMLParagraphElement;
}

export interface MusclePanelDom {
  element: HTMLElement;
  controls: MusclePanelControls;
  elements: MusclePanelElements;
  dispose(): void;
}

const sideLabel = (reading: MuscleReading): string =>
  reading.side === 'l' ? 'L' : reading.side === 'r' ? 'R' : 'C';

const stateLabel = (reading: MuscleReading): string =>
  reading.state === 'shortened'
    ? 'Shortened'
    : reading.state === 'lengthened'
      ? 'Lengthened'
      : 'Near rest';

const deltaLabel = (reading: MuscleReading): string => {
  const value = reading.deltaPercent;
  const sign = value > 0.05 ? '+' : value < -0.05 ? '−' : '';
  return `${sign}${Math.abs(value).toFixed(1)}%`;
};

const regionLabel = (region: MuscleRegionFilter): string =>
  region === 'all' ? 'All regions' : region[0].toUpperCase() + region.slice(1);

/**
 * React-free live muscle diagnostics panel.
 *
 * It reads finished-frame biomechanics from the existing Studio pipeline and
 * keeps only its two UI filters locally, matching the former React component.
 */
export function createMusclePanelDom(
  documentRef: Pick<Document, 'createElement'> = document,
  store: MuscleStorePort = studioStore,
): MusclePanelDom {
  let activeOnly = false;
  let region: MuscleRegionFilter = 'all';
  let disposed = false;

  const root = documentRef.createElement('section');
  root.className = 'panel';
  root.dataset.hgptPanel = 'muscles-first-party';

  const heading = documentRef.createElement('h2');
  heading.textContent = 'Muscle diagnostics';

  const hint = documentRef.createElement('div');
  hint.className = 'panel__hint';

  const summary = documentRef.createElement('div');
  summary.className = 'muscle-diagnostics__summary';

  const filters = documentRef.createElement('div');
  filters.className = 'muscle-diagnostics__filters';

  const activeLabel = documentRef.createElement('label');
  activeLabel.className = 'field field--check';
  const activeInput = documentRef.createElement('input');
  activeInput.type = 'checkbox';
  activeInput.checked = false;
  const activeText = documentRef.createElement('span');
  activeText.textContent = 'Active only';
  activeLabel.append(activeInput, activeText);

  const regionLabelElement = documentRef.createElement('label');
  regionLabelElement.className = 'field';
  const regionCaption = documentRef.createElement('span');
  regionCaption.className = 'field__label';
  regionCaption.textContent = 'Region';
  const regionSelect = documentRef.createElement('select');
  for (const value of REGIONS) {
    const option = documentRef.createElement('option');
    option.value = value;
    option.textContent = regionLabel(value);
    regionSelect.append(option);
  }
  regionSelect.value = 'all';
  regionLabelElement.append(regionCaption, regionSelect);
  filters.append(activeLabel, regionLabelElement);

  const list = documentRef.createElement('ul');
  list.className = 'muscle-diagnostics';

  const empty = documentRef.createElement('p');
  empty.className = 'panel__empty';
  empty.textContent = 'No muscle groups match this filter.';
  empty.hidden = true;

  root.append(heading, hint, summary, filters, list, empty);

  const render = () => {
    if (disposed) return;
    const state = store.getState();
    const clip = state.document.clip;
    const exercise = state.document.exercise;
    const time = state.time;

    const evaluation = new PoseEvaluation(skeleton);
    const frame = resolveFrame(skeleton, evaluation, clip, time);
    evaluation.apply(frame.pose);
    const diagnostics = diagnoseMuscles(evaluation, exercise.muscles);

    const visible = diagnostics
      .filter((entry) => !activeOnly || entry.activation !== 'inactive')
      .filter((entry) => region === 'all' || entry.region === region)
      .sort((a, b) => {
        const role =
          MUSCLE_ACTIVATION_ORDER[a.activation] -
          MUSCLE_ACTIVATION_ORDER[b.activation];
        return role || a.label.localeCompare(b.label);
      });

    const activeCount = diagnostics.filter(
      (entry) => entry.activation !== 'inactive',
    ).length;

    hint.textContent =
      `Live functional path length at ${time.toFixed(2)}s. Length is geometric, not a force or EMG estimate: ` +
      'a stabiliser can work hard while remaining near-isometric.';

    const activeStrong = documentRef.createElement('strong');
    activeStrong.textContent = String(activeCount);
    const activeSuffix = documentRef.createElement('span');
    activeSuffix.textContent = ' active groups · ';
    const totalStrong = documentRef.createElement('strong');
    totalStrong.textContent = String(diagnostics.length);
    const totalSuffix = documentRef.createElement('span');
    totalSuffix.textContent = ' modelled groups';
    summary.replaceChildren(activeStrong, activeSuffix, totalStrong, totalSuffix);

    const items: HTMLLIElement[] = [];
    for (const entry of visible) {
      const style = ACTIVATION_STYLES[entry.activation];
      const item = documentRef.createElement('li');
      item.className = 'muscle-diagnostic';

      const head = documentRef.createElement('div');
      head.className = 'muscle-diagnostic__head';
      const swatch = documentRef.createElement('span');
      swatch.className = 'swatch';
      swatch.style.background = style.colour;
      const name = documentRef.createElement('span');
      name.className = 'muscle-diagnostic__name';
      name.textContent = entry.label;
      const role = documentRef.createElement('span');
      role.className = 'muscle-diagnostic__role';
      role.textContent = style.label;
      head.append(swatch, name, role);

      const readings = documentRef.createElement('div');
      readings.className = 'muscle-diagnostic__readings';
      for (const reading of entry.readings) {
        const readingElement = documentRef.createElement('span');
        readingElement.className = `muscle-reading muscle-reading--${reading.state}`;
        readingElement.title = `${(reading.stretch * 100).toFixed(1)}% of rest length`;

        const side = documentRef.createElement('b');
        side.textContent = sideLabel(reading);
        const detail = documentRef.createElement('span');
        detail.textContent =
          ` ${deltaLabel(reading)} · ${stateLabel(reading)}` +
          (reading.pathPoints > 2 ? ' · wrapped path' : '');
        readingElement.append(side, detail);
        readings.append(readingElement);
      }

      item.append(head, readings);
      items.push(item);
    }

    list.replaceChildren(...items);
    empty.hidden = visible.length !== 0;
  };

  const onActiveOnlyChange = () => {
    activeOnly = activeInput.checked;
    render();
  };
  const onRegionChange = () => {
    region = regionSelect.value as MuscleRegionFilter;
    render();
  };
  activeInput.addEventListener('change', onActiveOnlyChange);
  regionSelect.addEventListener('change', onRegionChange);

  const unsubscribe = store.subscribe(render);
  render();

  return {
    element: root,
    controls: { activeOnly: activeInput, region: regionSelect },
    elements: { hint, summary, list, empty },
    dispose() {
      if (disposed) return;
      disposed = true;
      unsubscribe();
      activeInput.removeEventListener('change', onActiveOnlyChange);
      regionSelect.removeEventListener('change', onRegionChange);
    },
  };
}
