import type { ObservableStore } from '../../core/observableStore';
import { correctiveDiagnostics } from '../../character/correctiveDiagnostics';
import { meshStrainDiagnostics, type MeshStrainDiagnostic } from '../../character/meshStrain';
import { characterStore, type CharacterState } from '../characterStoreCore';
import { skeleton, studioStore, type StudioState } from '../storeCore';
import {
  scanDeformationControlSweep,
  scanMeshStrainWorstCases,
  type CorrectiveSweepPoint,
  type MeshStrainWorstPoint,
} from '../strainReview';

type DocumentPort = Pick<Document, 'createElement'>;
type CharacterPort = Pick<ObservableStore<CharacterState>, 'getState' | 'subscribe'>;
type StudioPort = Pick<ObservableStore<StudioState>, 'getState' | 'subscribe'>;

export interface CorrectivePanelDom { element: HTMLElement; dispose(): void }
const mm = (metres: number): string => `${(metres * 1000).toFixed(1)} mm`;

/** Keeps diagnostic scans and preview actions on the existing character and Studio stores. */
export function createCorrectivePanelDom(
  documentRef: DocumentPort = document,
  characters: CharacterPort = characterStore,
  studio: StudioPort = studioStore,
): CorrectivePanelDom {
  const root = documentRef.createElement('section');
  root.className = 'panel corrective-panel';
  root.dataset.hgptPanel = 'correctives-first-party';
  const el = (tag: string, className?: string, content?: string): HTMLElement => {
    const node = documentRef.createElement(tag);
    if (className) node.className = className;
    if (content !== undefined) node.textContent = content;
    return node;
  };
  const button = (label: string, action: () => void, id?: string): HTMLButtonElement => {
    const node = documentRef.createElement('button');
    node.type = 'button';
    node.textContent = label;
    if (id) node.dataset.hgptCorrectiveControl = id;
    node.addEventListener('click', action);
    return node;
  };
  const row = (...children: HTMLElement[]): HTMLElement => {
    const node = el('div', 'button-row');
    node.append(...children);
    return node;
  };
  let strain: MeshStrainDiagnostic[] = [];
  let wholeRep: { enabled: boolean; items: MeshStrainWorstPoint[] } | null = null;
  let sweep: { controlId: string; points: CorrectiveSweepPoint[] } | null = null;
  let activeBefore = characters.getState().active;
  let enabledBefore = characters.getState().correctivesPreview;
  let clipBefore = studio.getState().document.clip;
  let disposed = false;
  let timer: ReturnType<typeof setInterval> | null = null;

  const updateStrain = () => {
    if (disposed) return;
    const active = characters.getState().active;
    strain = active ? meshStrainDiagnostics(active.meshes) : [];
    render();
  };
  const restartSampling = () => {
    if (timer !== null) clearInterval(timer);
    timer = null;
    updateStrain();
    if (characters.getState().active) timer = setInterval(updateStrain, 200);
  };
  const render = () => {
    if (disposed) return;
    const character = characters.getState();
    const active = character.active;
    const enabled = character.correctivesPreview;
    const controls = active?.deformation?.controls ?? [];
    const diagnostics = active ? correctiveDiagnostics(active.meshes) : [];
    const children: HTMLElement[] = [
      el('h2', undefined, 'Correctives'),
      el('p', 'panel__note', 'Mesh-specific joint correctives at the current playhead. The bypass below is viewport-only; it never changes the clip, source mesh or exported animation.'),
    ];
    const modes = el('div', 'corrective-ab');
    const on = button('Correctives on', () => characters.getState().setCorrectivesPreview(true), 'on');
    const raw = button('Raw skinning', () => characters.getState().setCorrectivesPreview(false), 'raw');
    on.className = enabled ? 'is-active' : '';
    raw.className = !enabled ? 'is-active' : '';
    modes.append(on, raw);
    children.push(modes);

    if (controls.length) {
      children.push(el('h3', undefined, 'Corrective tuning'));
      children.push(el('p', 'panel__hint', 'Character-specific and export-aware. These controls change neither the exercise clip nor the source skin weights; the active character and GLB export share the same value.'));
      for (const control of controls) {
        const card = el('div', 'strain-card');
        card.append(el('strong', undefined, `${control.label} · ${Math.round(control.value * 100)}%`));
        const input = documentRef.createElement('input');
        input.type = 'range';
        input.min = String(control.min); input.max = String(control.max);
        input.step = String(control.step); input.value = String(control.value);
        input.dataset.hgptCorrectiveControl = `tune-${control.id}`;
        input.addEventListener('change', () => {
          wholeRep = null;
          characters.getState().setDeformationControl(control.id, Number(input.value));
          render();
        });
        card.append(input);
        const presets = row();
        for (const fraction of [0, 0.25, 0.5, 0.75, 1]) {
          const preset = control.min + (control.max - control.min) * fraction;
          const presetButton = button(`${Math.round(fraction * 100)}%`, () => {
            wholeRep = null;
            characters.getState().setDeformationControl(control.id, preset);
            render();
          }, `preset-${control.id}-${fraction}`);
          presetButton.className = Math.abs(control.value - preset) < 1e-9 ? 'is-active' : '';
          presets.append(presetButton);
        }
        card.append(presets);
        card.append(el('small', undefined, 'Preset comparison changes only corrective strength; the playhead stays on the same frame for a fair silhouette A/B.'));
        if (control.note) card.append(el('small', undefined, control.note));
        const reset = button('Reset authored value', () => {
          wholeRep = null; sweep = null;
          characters.getState().setDeformationControl(control.id, control.defaultValue);
          render();
        }, `reset-${control.id}`);
        reset.disabled = Math.abs(control.value - control.defaultValue) < 1e-9;
        const compare = button('Compare 0–100%', () => {
          const current = characters.getState();
          if (!current.active) return;
          const points = scanDeformationControlSweep(current.active, control, skeleton,
            studio.getState().document.clip, current.correctivesPreview, studio.getState().time);
          sweep = { controlId: control.id, points };
          render();
        }, `compare-${control.id}`);
        compare.disabled = !active || !enabled;
        card.append(row(reset, compare));
        if (!enabled) card.append(el('small', undefined, 'Enable Correctives on before comparing candidate strengths.'));
        if (sweep?.controlId === control.id) {
          const list = el('div', 'strain-list');
          for (const point of sweep.points) {
            const item = el('div', 'strain-card');
            item.append(el('strong', undefined, `${Math.round(point.value * 100)}%`));
            item.append(el('span', undefined, `Worst P99 ${point.p99 ? `${(point.p99.value * 100).toFixed(1)}% · ${point.p99.time.toFixed(2)}s` : '—'}`));
            item.append(el('span', undefined, `Worst edge ${point.max ? `${(point.max.value * 100).toFixed(1)}% · ${point.max.time.toFixed(2)}s` : '—'}`));
            const review = button('Review this value at worst P99', () => {
              wholeRep = null;
              characters.getState().setDeformationControl(control.id, point.value);
              if (point.p99) studio.getState().setTime(point.p99.time);
              render();
            }, `review-${control.id}-${point.value}`);
            review.disabled = !point.p99;
            item.append(review);
            list.append(item);
          }
          card.append(list, el('small', undefined, 'The sweep restores the value that was active before scanning. Results measure strain only; silhouette and natural motion still require visual review.'));
        }
        children.push(card);
      }
    }

    if (!active) children.push(el('p', 'panel__empty', 'No active character is mounted.'));
    if (active && !diagnostics.length) children.push(el('p', 'panel__empty', 'This character exposes no Home Gym PT corrective morphs.'));
    children.push(el('h3', undefined, 'Surface strain'));
    children.push(el('p', 'panel__hint', 'Sampled edge-length change versus bind geometry. P95/P99 are robust whole-surface signals; severe counts are edges compressed or stretched by more than 20%.'));
    const scan = button('Scan full rep', () => {
      const current = characters.getState();
      if (!current.active) return;
      wholeRep = {
        enabled: current.correctivesPreview,
        items: scanMeshStrainWorstCases(current.active, skeleton, studio.getState().document.clip,
          current.correctivesPreview, studio.getState().time),
      };
      render();
    }, 'scan');
    scan.disabled = !active;
    children.push(row(scan));
    if (wholeRep) {
      const list = el('div', 'strain-list');
      for (const item of wholeRep.items) {
        const card = el('div', 'strain-card');
        card.append(el('strong', undefined, `${item.mesh} · ${wholeRep.enabled ? 'Correctives on' : 'Raw skinning'}`));
        card.append(el('span', undefined, `Worst P99 ${(item.p99.value * 100).toFixed(1)}% · ${item.p99.time.toFixed(2)}s`));
        card.append(el('span', undefined, `Worst max ${(item.max.value * 100).toFixed(1)}% · ${item.max.time.toFixed(2)}s`));
        card.append(el('span', undefined, `Worst compression count · ${item.severeCompression.value.toFixed(0)} · ${item.severeCompression.time.toFixed(2)}s`));
        card.append(el('span', undefined, `Worst stretch count · ${item.severeStretch.value.toFixed(0)} · ${item.severeStretch.time.toFixed(2)}s`));
        card.append(row(button('Jump to worst P99', () => studio.getState().setTime(item.p99.time)),
          button('Jump to worst edge', () => studio.getState().setTime(item.max.time))));
        card.append(el('small', undefined, `${item.sampledEdges} sampled edges per frame`));
        list.append(card);
      }
      children.push(list);
    }
    children.push(el('p', 'panel__hint', 'Full-rep scan runs only when requested, follows the clip FPS, restores the current playhead pose, and uses a bounded edge sample so it remains an authoring locator rather than a simulation.'));
    const strains = el('div', 'strain-list');
    for (const item of strain) {
      const card = el('div', 'strain-card');
      card.append(el('strong', undefined, item.mesh));
      card.append(el('span', undefined, `P95 ${(item.p95 * 100).toFixed(1)}%`));
      card.append(el('span', undefined, `P99 ${(item.p99 * 100).toFixed(1)}%`));
      card.append(el('span', undefined, `Max ${(item.max * 100).toFixed(1)}%`));
      card.append(el('span', undefined, `Compression >20% · ${item.severeCompression}`));
      card.append(el('span', undefined, `Stretch >20% · ${item.severeStretch}`));
      card.append(el('small', undefined, `${item.sampledEdges} sampled edges`));
      strains.append(card);
    }
    children.push(strains, el('h3', undefined, 'Corrective morphs'));
    const morphs = el('div', 'corrective-list');
    for (const item of diagnostics) {
      const card = el('article', 'corrective-card');
      const head = el('div', 'corrective-card__head');
      head.append(el('strong', undefined, item.name.replace('homeGymPT_', '').replaceAll('_', ' ')),
        el('span', undefined, `${Math.round(item.influence * 100)}%`));
      const metrics = el('div', 'corrective-metrics');
      metrics.append(el('span', undefined, `Live displacement ${mm(item.liveMaxDisplacement)}`),
        el('span', undefined, `Authored maximum ${mm(item.maxDisplacement)}`),
        el('span', undefined, `Affected vertices ${item.affectedVertices}`),
        el('span', undefined, `Mesh ${item.mesh}`));
      card.append(head, metrics);
      morphs.append(card);
    }
    children.push(morphs);
    root.replaceChildren(...children);
  };
  const onCharacter = () => {
    const current = characters.getState();
    if (current.active !== activeBefore || current.correctivesPreview !== enabledBefore) {
      activeBefore = current.active;
      enabledBefore = current.correctivesPreview;
      wholeRep = null; sweep = null;
      restartSampling();
    } else render();
  };
  const onStudio = () => {
    const clip = studio.getState().document.clip;
    if (clip !== clipBefore) { clipBefore = clip; wholeRep = null; sweep = null; }
    render();
  };
  const unsubscribeCharacter = characters.subscribe(onCharacter);
  const unsubscribeStudio = studio.subscribe(onStudio);
  restartSampling();
  return { element: root, dispose() {
    if (disposed) return;
    disposed = true;
    if (timer !== null) clearInterval(timer);
    unsubscribeCharacter(); unsubscribeStudio();
  } };
}
