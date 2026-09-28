import type { ObservableStore } from '../../core/observableStore';
import { EQUIPMENT_LIBRARY, equipmentSocketForInstance } from '../../equipment/library';
import type { Vec3 } from '../../rig/types';
import { studioStore, type StudioState } from '../storeCore';

type DocumentPort = Pick<Document, 'createElement'>;
type EquipmentStorePort = Pick<ObservableStore<StudioState>, 'getState' | 'subscribe'>;

export interface EquipmentPanelDom {
  element: HTMLElement;
  dispose(): void;
}

const CM = 100;

const appendNumberField = (
  documentRef: DocumentPort,
  container: HTMLElement,
  labelText: string,
  value: number,
  step: number,
  fieldId: string,
  onInput: (value: number) => void,
): void => {
  const label = documentRef.createElement('label');
  label.className = 'field';
  const caption = documentRef.createElement('span');
  caption.className = 'field__label';
  caption.textContent = labelText;
  const input = documentRef.createElement('input');
  input.type = 'number';
  input.step = String(step);
  input.value = String(value);
  input.dataset.hgptEquipmentField = fieldId;
  input.addEventListener('input', () => onInput(Number(input.value)));
  label.append(caption, input);
  container.append(label);
};

/** React-free equipment transform/socket editor backed by the existing Studio store. */
export function createEquipmentPanelDom(
  documentRef: DocumentPort = document,
  store: EquipmentStorePort = studioStore,
): EquipmentPanelDom {
  const root = documentRef.createElement('section');
  root.className = 'panel equipment-panel';
  root.dataset.hgptPanel = 'equipment-first-party';

  const render = () => {
    const state = store.getState();
    const instances = state.document.exercise.equipment.instances;
    const selection = state.selection;
    const selected = instances.find((instance) => instance.id === selection.equipmentId) ?? null;
    const definition = selected ? EQUIPMENT_LIBRARY[selected.kind] : null;
    const selectedSocket =
      selected && selection.socketId
        ? equipmentSocketForInstance(selected, selection.socketId)
        : null;

    const children: HTMLElement[] = [];

    const title = documentRef.createElement('h2');
    title.textContent = 'Equipment';
    children.push(title);

    const note = documentRef.createElement('p');
    note.className = 'panel__note';
    note.textContent =
      'Select equipment here or in the viewport. Static equipment and its sockets use the normal Studio gizmo and undo history. Hand-driven handle placement stays in Grip.';
    children.push(note);

    if (instances.length === 0) {
      const empty = documentRef.createElement('p');
      empty.className = 'panel__empty';
      empty.textContent = 'This exercise uses no equipment.';
      children.push(empty);
    }

    const list = documentRef.createElement('div');
    list.className = 'equipment-list';
    for (const instance of instances) {
      const button = documentRef.createElement('button');
      button.type = 'button';
      button.className = instance.id === selection.equipmentId ? 'is-active' : '';
      button.dataset.hgptEquipmentId = instance.id;
      const label = documentRef.createElement('span');
      label.textContent = instance.label ?? EQUIPMENT_LIBRARY[instance.kind].label;
      const mode = documentRef.createElement('small');
      mode.textContent = instance.attachment.mode;
      button.append(label, mode);
      button.addEventListener('click', () => store.getState().selectEquipment(instance.id));
      list.append(button);
    }
    children.push(list);

    if (selected && definition) {
      const selectedTitle = documentRef.createElement('h3');
      selectedTitle.textContent = selected.label ?? definition.label;
      children.push(selectedTitle);

      if (selected.attachment.mode === 'static') {
        const hint = documentRef.createElement('p');
        hint.className = 'panel__hint';
        hint.textContent =
          'Use Translate / Rotate in the toolbar for the selected object or socket, or enter exact values below.';
        children.push(hint);

        const grid = documentRef.createElement('div');
        grid.className = 'equipment-transform-grid';
        const positionTitle = documentRef.createElement('strong');
        positionTitle.textContent = 'Object position';
        grid.append(positionTitle);
        for (const axis of ['x', 'y', 'z'] as const) {
          appendNumberField(
            documentRef,
            grid,
            `${axis.toUpperCase()} · cm`,
            Number((selected.position[axis] * CM).toFixed(1)),
            1,
            `position-${axis}`,
            (centimetres) => {
              store.getState().setEquipmentTransform(selected.id, {
                position: { ...selected.position, [axis]: centimetres / CM },
              });
            },
          );
        }

        const rotationTitle = documentRef.createElement('strong');
        rotationTitle.textContent = 'Object rotation';
        grid.append(rotationTitle);
        for (const axis of ['x', 'y', 'z'] as const) {
          appendNumberField(
            documentRef,
            grid,
            `${axis.toUpperCase()} · °`,
            Number(selected.rotation[axis].toFixed(1)),
            1,
            `rotation-${axis}`,
            (degrees) => {
              store.getState().setEquipmentTransform(selected.id, {
                rotation: { ...selected.rotation, [axis]: degrees },
              });
            },
          );
        }
        children.push(grid);
      } else if (selected.attachment.mode === 'cable') {
        const cable = documentRef.createElement('p');
        cable.className = 'panel__note';
        cable.textContent =
          `This cable runs from ${selected.attachment.from.equipment} to ${selected.attachment.to.equipment} and follows them; it has no position of its own.`;
        children.push(cable);
      } else {
        const driven = documentRef.createElement('p');
        driven.className = 'panel__note';
        driven.textContent =
          `This object is driven by ${selected.attachment.mode === 'hand' ? 'one hand' : 'both hands'}. World position/rotation and socket calibration are intentionally owned by Grip/attachment.`;
        children.push(driven);
      }

      const socketsTitle = documentRef.createElement('h3');
      socketsTitle.textContent = 'Sockets';
      children.push(socketsTitle);

      const sockets = documentRef.createElement('div');
      sockets.className = 'equipment-sockets';
      for (const base of definition.sockets) {
        const socket = equipmentSocketForInstance(selected, base.id);
        if (!socket) continue;
        const active = selection.socketId === socket.id;
        const button = documentRef.createElement('button');
        button.type = 'button';
        button.className = `equipment-socket ${active ? 'is-active' : ''}`;
        button.dataset.hgptSocketId = socket.id;
        button.addEventListener('click', () => {
          if (selected.attachment.mode === 'static') {
            store.getState().selectSocket(selected.id, active ? null : socket.id);
          }
        });

        const identity = documentRef.createElement('div');
        const label = documentRef.createElement('strong');
        label.textContent = socket.label;
        const kind = documentRef.createElement('span');
        kind.textContent = socket.kind;
        identity.append(label, kind);

        const position = documentRef.createElement('code');
        position.textContent =
          `${(socket.position.x * CM).toFixed(1)}, ${(socket.position.y * CM).toFixed(1)}, ${(socket.position.z * CM).toFixed(1)} cm`;
        button.append(identity, position);
        sockets.append(button);
      }
      children.push(sockets);

      if (selected.attachment.mode === 'static' && selectedSocket) {
        const editor = documentRef.createElement('div');
        editor.className = 'socket-editor';

        const head = documentRef.createElement('div');
        head.className = 'socket-editor__head';
        const socketTitle = documentRef.createElement('strong');
        socketTitle.textContent = selectedSocket.label;
        const reset = documentRef.createElement('button');
        reset.type = 'button';
        reset.textContent = 'Reset socket';
        reset.dataset.hgptSocketReset = selectedSocket.id;
        reset.addEventListener('click', () => {
          store.getState().setEquipmentSocketTransform(selected.id, selectedSocket.id, null);
        });
        head.append(socketTitle, reset);
        editor.append(head);

        const grid = documentRef.createElement('div');
        grid.className = 'equipment-transform-grid';
        const positionTitle = documentRef.createElement('strong');
        positionTitle.textContent = 'Socket local position';
        grid.append(positionTitle);
        for (const axis of ['x', 'y', 'z'] as const) {
          appendNumberField(
            documentRef,
            grid,
            `${axis.toUpperCase()} · cm`,
            Number((selectedSocket.position[axis] * CM).toFixed(1)),
            0.5,
            `socket-position-${axis}`,
            (centimetres) => {
              store.getState().setEquipmentSocketTransform(selected.id, selectedSocket.id, {
                position: { ...selectedSocket.position, [axis]: centimetres / CM },
              });
            },
          );
        }

        const rotationTitle = documentRef.createElement('strong');
        rotationTitle.textContent = 'Socket local rotation';
        grid.append(rotationTitle);
        for (const axis of ['x', 'y', 'z'] as const) {
          appendNumberField(
            documentRef,
            grid,
            `${axis.toUpperCase()} · °`,
            Number((selectedSocket.rotation?.[axis] ?? 0).toFixed(1)),
            1,
            `socket-rotation-${axis}`,
            (degrees) => {
              store.getState().setEquipmentSocketTransform(selected.id, selectedSocket.id, {
                rotation: {
                  ...(selectedSocket.rotation ?? { x: 0, y: 0, z: 0 }),
                  [axis]: degrees,
                },
              });
            },
          );
        }
        editor.append(grid);
        children.push(editor);
      }
    }

    if (!selected && instances.length > 0) {
      const empty = documentRef.createElement('p');
      empty.className = 'panel__empty';
      empty.textContent = 'Select an equipment object to inspect its transform and sockets.';
      children.push(empty);
    }

    root.replaceChildren(...children);
  };

  const unsubscribe = store.subscribe(render);
  render();

  let disposed = false;
  return {
    element: root,
    dispose() {
      if (disposed) return;
      disposed = true;
      unsubscribe();
    },
  };
}
