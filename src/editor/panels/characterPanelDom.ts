import type { ObservableStore } from '../../core/observableStore';
import { characterSources } from '../../character';
import { boneLabel, type BoneName } from '../../rig/boneNames';
import { REQUIRED_BONES } from '../../retargeting/boneMap';
import { characterStore, type BindMode, type CharacterState } from '../characterStoreCore';
import { studioStore, type StudioState } from '../storeCore';

type DocumentPort = Pick<Document, 'createElement'>;
type CharacterPort = Pick<ObservableStore<CharacterState>, 'getState' | 'subscribe'>;
type StudioPort = Pick<ObservableStore<StudioState>, 'getState' | 'subscribe'>;

export interface CharacterPanelDom { element: HTMLElement; dispose(): void }

/** Character source/import/mapping controls over the framework-neutral stores. */
export function createCharacterPanelDom(
  documentRef: DocumentPort = document,
  characters: CharacterPort = characterStore,
  studio: StudioPort = studioStore,
): CharacterPanelDom {
  const root = documentRef.createElement('section');
  root.className = 'panel';
  root.dataset.hgptPanel = 'character-first-party';
  const element = (tag: string, className?: string, content?: string): HTMLElement => {
    const node = documentRef.createElement(tag);
    if (className) node.className = className;
    if (content !== undefined) node.textContent = content;
    return node;
  };
  const button = (text: string, action: () => void, id?: string): HTMLButtonElement => {
    const node = documentRef.createElement('button');
    node.type = 'button';
    node.textContent = text;
    if (id) node.dataset.hgptCharacterControl = id;
    node.addEventListener('click', action);
    return node;
  };
  const render = () => {
    const state = characters.getState();
    const children: HTMLElement[] = [element('h2', undefined, 'Character')];
    children.push(element('p', 'panel__note', 'Animation is authored on the canonical skeleton and driven onto whichever character is selected, so an exercise never has to be re-animated per model.'));

    const sourceRow = element('label', 'mapping-row');
    sourceRow.append(element('span', 'mapping-row__name', 'Character'));
    const source = documentRef.createElement('select');
    source.dataset.hgptCharacterControl = 'source';
    source.value = state.sourceId;
    for (const item of characterSources()) {
      const option = documentRef.createElement('option');
      option.value = item.id;
      option.textContent = item.label;
      source.append(option);
    }
    source.value = state.sourceId;
    source.addEventListener('change', () => characters.getState().setSource(source.value));
    sourceRow.append(source);
    children.push(sourceRow);
    if (state.sourceStatus.kind === 'error') children.push(element('div', 'status is-warn', state.sourceStatus.message));

    const bindRow = element('label', 'mapping-row');
    bindRow.append(element('span', 'mapping-row__name', 'Imports bind by'));
    const bind = documentRef.createElement('select');
    bind.dataset.hgptCharacterControl = 'bind-mode';
    for (const [value, label] of [
      ['preserve', 'Preserving the model (recommended)'],
      ['rebind', 'Rebinding onto the studio rig (diagnostic)'],
    ]) {
      const option = documentRef.createElement('option');
      option.value = value;
      option.textContent = label;
      bind.append(option);
    }
    bind.value = state.bindMode;
    bind.addEventListener('change', () => characters.getState().setBindMode(bind.value as BindMode));
    bindRow.append(bind);
    children.push(bindRow);

    const input = documentRef.createElement('input');
    input.type = 'file';
    input.accept = '.glb,.gltf,model/gltf-binary';
    input.style.display = 'none';
    input.dataset.hgptCharacterControl = 'file';
    input.addEventListener('change', async () => {
      const file = input.files?.[0];
      if (!file) return;
      await characters.getState().load(file);
      studio.getState().setViewMode('character');
      input.value = '';
    });
    children.push(input);
    const actions = element('div', 'button-row');
    const importButton = button('Import rigged GLB', () => input.click(), 'import');
    importButton.className = 'primary';
    actions.append(importButton);
    if (state.name) actions.append(button('Remove', () => characters.getState().clear(), 'remove'));
    children.push(actions);

    if (state.status.kind === 'loading') children.push(element('div', 'status is-ok', state.status.message));
    if (state.status.kind === 'error') children.push(element('div', 'status is-warn', state.status.message));
    if (state.imported) {
      const report = state.imported;
      const card = element('div', `status ${report.mapping.missingRequired.length === 0 ? 'is-ok' : 'is-warn'}`);
      card.append(element('strong', undefined, state.name ?? ''));
      card.append(element('div', 'status__row', `${report.vertices} vertices and ${report.bones} bones, kept as authored. ${report.height.toFixed(2)} m tall, scaled ×${report.scale.toFixed(2)}.`));
      card.append(element('div', 'status__row', `${report.driven} bones driven by the rig; ${report.passive} left at rest — twists, helpers and the face rig, riding their parents as authored.`));
      if (report.mapping.missingRequired.length) card.append(element('div', 'status__row', `Still unmapped: ${report.mapping.missingRequired.join(', ')}.`));
      children.push(card);
    }
    if (state.rebind?.length) {
      const card = element('div', 'status is-ok');
      card.append(element('strong', undefined, state.name ?? ''));
      card.append(element('div', 'status__row', `${state.rebind.reduce((total, part) => total + part.vertices, 0)} vertices rebound onto ${state.rebind[0].mappedBones.length} mapped bones, scaled ×${state.rebind[0].scale.toFixed(2)}.`));
      if (state.rebind.some((part) => part.orphaned > 0)) card.append(element('div', 'status__row', `${state.rebind.reduce((total, part) => total + part.orphaned, 0)} vertices carried no usable weight and were bound rigidly to the nearest bone — a gap in the file's own weighting, not in the import.`));
      children.push(card);
    }
    if (!state.imported && !state.rebind) children.push(element('p', 'panel__empty', 'No character imported — the viewport shows the selected built-in character.'));
    if (state.mapping && state.report) {
      const mapping = state.mapping;
      const save = element('div', 'button-row');
      save.append(button('Save mapping for reuse', () => characters.getState().persist(), 'persist'));
      children.push(save, element('h3', undefined, 'Bone mapping'), element('p', 'panel__note', 'Anything the guesser could not identify is left blank rather than matched to something that merely looks right.'));
      const list = element('div', 'mapping-list');
      for (const bone of REQUIRED_BONES as readonly BoneName[]) {
        const row = element('label', 'mapping-row');
        row.append(element('span', 'mapping-row__name', boneLabel(bone)));
        const select = documentRef.createElement('select');
        select.dataset.hgptCharacterBone = bone;
        select.className = mapping.bones[bone] ? '' : 'is-missing';
        const blank = documentRef.createElement('option');
        blank.value = '';
        blank.textContent = '— unmapped —';
        select.append(blank);
        for (const target of Object.values(mapping.bones).filter((candidate): candidate is string => Boolean(candidate))) {
          const option = documentRef.createElement('option');
          option.value = target;
          option.textContent = target;
          select.append(option);
        }
        select.value = mapping.bones[bone] ?? '';
        select.addEventListener('change', () => characters.getState().setBone(bone, select.value || null));
        row.append(select);
        list.append(row);
      }
      children.push(list);
    }
    root.replaceChildren(...children);
  };
  const unsubscribe = characters.subscribe(render);
  render();
  let disposed = false;
  return { element: root, dispose() { if (disposed) return; disposed = true; unsubscribe(); } };
}
