import { sampleClip } from '../../animation/clip';
import type { ObservableStore } from '../../core/observableStore';
import { IK_CHAINS, IK_CHAIN_IDS } from '../../ik/chains';
import { studioStore, type StudioState } from '../storeCore';

type DocumentPort = Pick<Document, 'createElement'>;
type IKStorePort = Pick<ObservableStore<StudioState>, 'getState' | 'subscribe'>;

export interface IKPanelDom {
  element: HTMLElement;
  dispose(): void;
}

const lockDescription = (mode: string): string => {
  if (mode === 'floor') return 'planted where it starts';
  if (mode === 'equipment') return 'held to equipment';
  return 'held at a fixed point';
};

/** React-free IK/lock editor backed by the existing Studio state/actions. */
export function createIKPanelDom(
  documentRef: DocumentPort = document,
  store: IKStorePort = studioStore,
): IKPanelDom {
  const root = documentRef.createElement('section');
  root.className = 'panel';
  root.dataset.hgptPanel = 'ik-first-party';

  const render = () => {
    const state = store.getState();
    const clip = state.document.clip;
    const sample = sampleClip(clip, state.time);
    const children: HTMLElement[] = [];

    const title = documentRef.createElement('h2');
    title.textContent = 'Inverse kinematics';
    children.push(title);

    const handlesLabel = documentRef.createElement('label');
    handlesLabel.className = 'field field--check';
    const handlesInput = documentRef.createElement('input');
    handlesInput.type = 'checkbox';
    handlesInput.checked = state.showIkHandles;
    handlesInput.dataset.hgptIkControl = 'show-handles';
    handlesInput.addEventListener('change', () => {
      store.getState().toggle('showIkHandles');
    });
    const handlesText = documentRef.createElement('span');
    handlesText.textContent = 'Show handles in viewport';
    handlesLabel.append(handlesInput, handlesText);
    children.push(handlesLabel);

    for (const chainId of IK_CHAIN_IDS) {
      const chain = IK_CHAINS[chainId];
      const goal = sample.ik[chainId];
      const active = Boolean(goal?.enabled);
      const chainRoot = documentRef.createElement('div');
      chainRoot.className = `ik-chain ${active ? 'is-active' : ''}`;
      chainRoot.dataset.hgptIkChain = chainId;

      const head = documentRef.createElement('div');
      head.className = 'ik-chain__head';
      const label = documentRef.createElement('label');
      label.className = 'field field--check';
      const input = documentRef.createElement('input');
      input.type = 'checkbox';
      input.checked = active;
      input.dataset.hgptIkToggle = chainId;
      input.addEventListener('change', () => {
        store.getState().toggleIK(chainId);
      });
      const labelText = documentRef.createElement('span');
      labelText.textContent = chain.label;
      label.append(input, labelText);
      head.append(label);
      chainRoot.append(head);

      if (active && goal) {
        const body = documentRef.createElement('div');
        body.className = 'ik-chain__body';

        const target = documentRef.createElement('button');
        target.type = 'button';
        target.className =
          state.selection.handle?.chain === chainId && state.selection.handle.kind === 'target'
            ? 'is-active'
            : '';
        target.dataset.hgptIkHandle = `${chainId}-target`;
        target.append(documentRef.createTextNode?.('Target ') ?? (() => {
          const span = documentRef.createElement('span');
          span.textContent = 'Target ';
          return span;
        })());
        const targetCode = documentRef.createElement('code');
        targetCode.textContent =
          `${goal.target.x.toFixed(2)}, ${goal.target.y.toFixed(2)}, ${goal.target.z.toFixed(2)}`;
        target.append(targetCode);
        target.addEventListener('click', () => {
          store.getState().selectHandle({ chain: chainId, kind: 'target' });
        });

        const pole = documentRef.createElement('button');
        pole.type = 'button';
        pole.className =
          state.selection.handle?.chain === chainId && state.selection.handle.kind === 'pole'
            ? 'is-active'
            : '';
        pole.dataset.hgptIkHandle = `${chainId}-pole`;
        const poleText = documentRef.createElement('span');
        poleText.textContent = `${chain.poleLabel} pole `;
        pole.append(poleText);
        const poleCode = documentRef.createElement('code');
        poleCode.textContent = `${goal.pole.x.toFixed(2)}, ${goal.pole.y.toFixed(2)}, ${goal.pole.z.toFixed(2)}`;
        pole.append(poleCode);
        pole.addEventListener('click', () => {
          store.getState().selectHandle({ chain: chainId, kind: 'pole' });
        });

        body.append(target, pole);
        chainRoot.append(body);
      }

      children.push(chainRoot);
    }

    const locksTitle = documentRef.createElement('h3');
    locksTitle.textContent = 'Locks';
    children.push(locksTitle);

    if (clip.locks.length === 0) {
      const empty = documentRef.createElement('p');
      empty.className = 'panel__empty';
      empty.textContent = 'This exercise defines no locks.';
      children.push(empty);
    }

    for (const lock of clip.locks) {
      const label = documentRef.createElement('label');
      label.className = 'field field--check';
      const input = documentRef.createElement('input');
      input.type = 'checkbox';
      input.checked = lock.enabled;
      input.dataset.hgptLockId = lock.id;
      input.addEventListener('change', () => {
        store.getState().setLockEnabled(lock.id, input.checked);
      });
      const text = documentRef.createElement('span');
      text.textContent = `${IK_CHAINS[lock.chain].label} — ${lockDescription(lock.mode)}`;
      label.append(input, text);
      children.push(label);
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
