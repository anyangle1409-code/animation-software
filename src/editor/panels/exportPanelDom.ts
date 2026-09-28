import type { ObservableStore } from '../../core/observableStore';
import { downloadBlob, downloadJson } from '../../export/download';
import { exportGlb } from '../../export/glb';
import { exportAnimationJson, exportMetadataJson } from '../../export/json';
import {
  characterStore,
  type CharacterState,
} from '../characterStoreCore';
import {
  skeleton,
  studioStore,
  type StudioState,
} from '../storeCore';

type DocumentPort = Pick<Document, 'createElement'>;
type StudioPort = Pick<ObservableStore<StudioState>, 'getState' | 'subscribe'>;
type CharacterPort = Pick<ObservableStore<CharacterState>, 'getState' | 'subscribe'>;

type ExportStatus = {
  kind: 'idle' | 'busy' | 'done' | 'error';
  message?: string;
};

export interface ExportActions {
  exportGlb: typeof exportGlb;
  exportAnimationJson: typeof exportAnimationJson;
  exportMetadataJson: typeof exportMetadataJson;
  downloadBlob: typeof downloadBlob;
  downloadJson: typeof downloadJson;
}

export interface ExportPanelDom {
  element: HTMLElement;
  dispose(): void;
}

const DEFAULT_ACTIONS: ExportActions = {
  exportGlb,
  exportAnimationJson,
  exportMetadataJson,
  downloadBlob,
  downloadJson,
};

const element = (
  documentRef: DocumentPort,
  tag: string,
  className?: string,
  text?: string,
): HTMLElement => {
  const node = documentRef.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
};

/**
 * React-free Export surface. Sample rate, equipment inclusion and status remain
 * mount-local exactly like the former useState values, so leaving and returning
 * to the tab restores 30 fps / include equipment / idle status.
 */
export function createExportPanelDom(
  documentRef: DocumentPort = document,
  studio: StudioPort = studioStore,
  characters: CharacterPort = characterStore,
  actions: ExportActions = DEFAULT_ACTIONS,
): ExportPanelDom {
  const root = documentRef.createElement('section');
  root.className = 'panel';
  root.dataset.hgptPanel = 'export-first-party';

  let fps = 30;
  let includeEquipment = true;
  let status: ExportStatus = { kind: 'idle' };
  let disposed = false;

  const run = async (
    label: string,
    task: () => Promise<void> | void,
  ): Promise<void> => {
    status = { kind: 'busy', message: `Building ${label}…` };
    render();
    try {
      await task();
      status = { kind: 'done', message: `${label} downloaded.` };
    } catch (error) {
      status = { kind: 'error', message: (error as Error).message };
    }
    if (!disposed) render();
  };

  const button = (
    label: string,
    control: string,
    action: () => Promise<void> | void,
    className = '',
  ): HTMLButtonElement => {
    const node = documentRef.createElement('button');
    node.type = 'button';
    node.textContent = label;
    node.className = className;
    node.dataset.hgptExportControl = control;
    node.addEventListener('click', () => {
      void action();
    });
    return node;
  };

  const render = () => {
    if (disposed) return;
    const state = studio.getState();
    const clip = state.document.clip;
    const exercise = state.document.exercise;
    const sourceId = characters.getState().sourceId;
    const children: HTMLElement[] = [
      element(documentRef, 'h2', undefined, 'Export'),
    ];

    const summary = element(documentRef, 'p', 'panel__note');
    summary.append(
      documentRef.createElement('span'),
    );
    summary.children[0]!.textContent = 'Clip name ';
    const code = documentRef.createElement('code');
    code.textContent = clip.name;
    summary.append(code, documentRef.createElement('span'));
    summary.children[2]!.textContent = `, ${clip.duration.toFixed(2)}s, looping.`;
    children.push(summary);

    const sampleLabel = documentRef.createElement('label');
    sampleLabel.className = 'field';
    sampleLabel.append(element(documentRef, 'span', 'field__label', 'Sample rate'));
    const select = documentRef.createElement('select');
    select.dataset.hgptExportControl = 'sample-rate';
    for (const value of [24, 30, 60]) {
      const option = documentRef.createElement('option');
      option.value = String(value);
      option.textContent = `${value} fps`;
      select.append(option);
    }
    select.value = String(fps);
    select.addEventListener('change', () => {
      fps = Number(select.value);
      render();
    });
    sampleLabel.append(select);
    children.push(sampleLabel);

    const equipmentLabel = documentRef.createElement('label');
    equipmentLabel.className = 'field field--check';
    const equipment = documentRef.createElement('input');
    equipment.type = 'checkbox';
    equipment.checked = includeEquipment;
    equipment.dataset.hgptExportControl = 'include-equipment';
    equipment.addEventListener('change', () => {
      includeEquipment = equipment.checked;
      render();
    });
    equipmentLabel.append(
      equipment,
      element(documentRef, 'span', undefined, 'Include equipment in the GLB'),
    );
    children.push(equipmentLabel);

    children.push(
      element(documentRef, 'h3', undefined, 'Animated GLB'),
      element(
        documentRef,
        'p',
        'panel__note',
        'Rig, animation clip and equipment in one file, ready to drop into the app.',
      ),
      button(
        `Export ${clip.name}.glb`,
        'animated-glb',
        () =>
          run('GLB', async () => {
            const blob = await actions.exportGlb(clip, exercise, {
              fps,
              includeEquipment,
              character: sourceId,
            });
            actions.downloadBlob(blob, `${clip.name}.glb`);
          }),
        'primary',
      ),
      element(documentRef, 'h3', undefined, 'Clip only'),
      element(
        documentRef,
        'p',
        'panel__note',
        'The skeleton and animation without the character mesh, so many exercises can share one downloaded character.',
      ),
    );

    const clipActions = element(documentRef, 'div', 'button-row');
    clipActions.append(
      button('GLB', 'clip-glb', () =>
        run('clip GLB', async () => {
          const blob = await actions.exportGlb(clip, exercise, {
            fps,
            clipOnly: true,
          });
          actions.downloadBlob(blob, `${clip.name}.anim.glb`);
        }),
      ),
      button('JSON', 'clip-json', () =>
        run('clip JSON', () => {
          actions.downloadJson(
            actions.exportAnimationJson(clip, exercise, skeleton, fps),
            `${clip.name}.anim.json`,
          );
        }),
      ),
    );
    children.push(
      clipActions,
      element(documentRef, 'h3', undefined, 'Exercise metadata'),
      element(
        documentRef,
        'p',
        'panel__note',
        'The full definition — phases, muscles, technique rules, camera and common errors — for the Home Gym PT exercise database.',
      ),
      button(
        `Export ${exercise.id}.json`,
        'metadata',
        () =>
          run('metadata', () => {
            actions.downloadJson(
              actions.exportMetadataJson(exercise),
              `${exercise.id}.json`,
            );
          }),
      ),
    );

    if (status.kind !== 'idle') {
      const message = element(
        documentRef,
        'div',
        `status ${status.kind === 'error' ? 'is-warn' : 'is-ok'}`,
        status.message,
      );
      message.dataset.hgptExportStatus = status.kind;
      children.push(message);
    }

    root.replaceChildren(...children);
  };

  const unsubscribeStudio = studio.subscribe(render);
  const unsubscribeCharacter = characters.subscribe(render);
  render();

  return {
    element: root,
    dispose() {
      if (disposed) return;
      disposed = true;
      unsubscribeStudio();
      unsubscribeCharacter();
    },
  };
}
