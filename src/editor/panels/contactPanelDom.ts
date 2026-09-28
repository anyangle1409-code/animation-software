import type { ObservableStore } from '../../core/observableStore';
import { contactDiagnostics, type ContactDiagnostic } from '../../constraints/contactDiagnostics';
import { IK_CHAINS } from '../../ik/chains';
import { PoseEvaluation } from '../../rig/skeleton';
import type { Vec3 } from '../../rig/types';
import { currentAnchors, skeleton, studioStore, type StudioState } from '../storeCore';

type DocumentPort = Pick<Document, 'createElement'>;
type ContactStorePort = Pick<ObservableStore<StudioState>, 'getState' | 'subscribe'>;

export interface ContactPanelDom {
  element: HTMLElement;
  dispose(): void;
}

const point = (value: Vec3 | null): string =>
  value ? `${value.x.toFixed(3)}, ${value.y.toFixed(3)}, ${value.z.toFixed(3)}` : '—';

const statusLabel = (diagnostic: ContactDiagnostic): string => {
  if (diagnostic.status === 'disabled') return 'Disabled';
  if (diagnostic.status === 'unresolved') return 'Target unresolved';
  if (diagnostic.status === 'overextended') return 'Over-extended';
  if (diagnostic.status === 'limited') return 'Limited by solve';
  return 'Reached';
};

const appendMetric = (
  documentRef: DocumentPort,
  list: HTMLDListElement,
  label: string,
  value: string,
  code = false,
): void => {
  const term = documentRef.createElement('dt');
  term.textContent = label;
  const detail = documentRef.createElement('dd');
  if (code) {
    const codeElement = documentRef.createElement('code');
    codeElement.textContent = value;
    detail.append(codeElement);
  } else {
    detail.textContent = value;
  }
  list.append(term, detail);
};

const reachability = (diagnostic: ContactDiagnostic): string => {
  if (diagnostic.reached === null) return '—';
  if (diagnostic.overExtended) return 'Outside physical reach';
  if (diagnostic.reached) return 'Solver reached target';
  return 'Joint limits prevented exact reach';
};

/** React-free live inspection surface for the existing production contact solver. */
export function createContactPanelDom(
  documentRef: DocumentPort = document,
  store: ContactStorePort = studioStore,
): ContactPanelDom {
  const root = documentRef.createElement('section');
  root.className = 'panel contact-panel';
  root.dataset.hgptPanel = 'contacts-first-party';

  const render = () => {
    const state = store.getState();
    const clip = state.document.clip;
    const time = state.time;
    const diagnostics = contactDiagnostics(
      skeleton,
      new PoseEvaluation(skeleton),
      clip,
      time,
      currentAnchors(clip),
    );

    const heading = documentRef.createElement('h2');
    heading.textContent = 'Contacts';

    const note = documentRef.createElement('p');
    note.className = 'panel__note';
    note.textContent =
      `Live production-solver inspection at ${time.toFixed(2)}s. These readouts do not add hidden corrections or change the animation.`;

    const children: HTMLElement[] = [heading, note];

    if (diagnostics.length === 0) {
      const empty = documentRef.createElement('p');
      empty.className = 'panel__empty';
      empty.textContent = 'This exercise defines no contact locks.';
      children.push(empty);
    }

    for (const diagnostic of diagnostics) {
      const card = documentRef.createElement('article');
      card.className = `contact-card contact-card--${diagnostic.status}`;

      const head = documentRef.createElement('div');
      head.className = 'contact-card__head';
      const label = documentRef.createElement('label');
      label.className = 'field field--check';
      const input = documentRef.createElement('input');
      input.type = 'checkbox';
      input.checked = diagnostic.enabled;
      input.addEventListener('change', () => {
        store.getState().setLockEnabled(diagnostic.id, input.checked);
      });
      const chain = documentRef.createElement('span');
      chain.textContent = IK_CHAINS[diagnostic.chain].label;
      label.append(input, chain);
      const status = documentRef.createElement('strong');
      status.textContent = statusLabel(diagnostic);
      head.append(label, status);

      const metrics = documentRef.createElement('dl');
      metrics.className = 'contact-metrics';
      appendMetric(documentRef, metrics, 'Lock', diagnostic.mode);
      if (diagnostic.mode === 'equipment') {
        appendMetric(
          documentRef,
          metrics,
          'Socket',
          `${diagnostic.equipmentId ?? '?'}:${diagnostic.socket ?? '?'}`,
          true,
        );
      }
      appendMetric(documentRef, metrics, 'Target', point(diagnostic.target), true);
      appendMetric(documentRef, metrics, 'Effector', point(diagnostic.actual), true);
      appendMetric(
        documentRef,
        metrics,
        'Error',
        diagnostic.error === null ? '—' : `${(diagnostic.error * 1000).toFixed(2)} mm`,
      );
      appendMetric(documentRef, metrics, 'Reachability', reachability(diagnostic));

      card.append(head, metrics);
      children.push(card);
    }

    const hint = documentRef.createElement('p');
    hint.className = 'panel__hint';
    hint.textContent =
      'Error is the final world-space distance from the resolved hand/foot effector to its lock target. Reachability is reported by the existing analytical IK solver.';
    children.push(hint);

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
