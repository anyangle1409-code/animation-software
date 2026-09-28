import { beforeEach, describe, expect, it } from 'vitest';
import { studioStore } from '../storeCore';
import { createContactPanelDom } from './contactPanelDom';

class FakeElement {
  readonly dataset: Record<string, string> = {};
  readonly children: FakeElement[] = [];
  className = '';
  textContent: string | null = null;
  type = '';
  checked = false;
  private readonly listeners = new Map<string, Set<EventListenerOrEventListenerObject>>();

  append(...nodes: FakeElement[]): void { this.children.push(...nodes); }
  replaceChildren(...nodes: FakeElement[]): void { this.children.splice(0, this.children.length, ...nodes); }
  addEventListener(type: string, listener: EventListenerOrEventListenerObject): void {
    const listeners = this.listeners.get(type) ?? new Set<EventListenerOrEventListenerObject>();
    listeners.add(listener);
    this.listeners.set(type, listeners);
  }
  removeEventListener(type: string, listener: EventListenerOrEventListenerObject): void {
    this.listeners.get(type)?.delete(listener);
  }
  dispatchEvent(event: Event): boolean {
    for (const listener of this.listeners.get(event.type) ?? []) {
      if (typeof listener === 'function') listener(event);
      else listener.handleEvent(event);
    }
    return true;
  }
}

const fakeDocument = (): Pick<Document, 'createElement'> => ({
  createElement: (() => new FakeElement()) as unknown as Document['createElement'],
});

const fake = (element: Element): FakeElement => element as unknown as FakeElement;

const all = (root: FakeElement): FakeElement[] => [
  root,
  ...root.children.flatMap((child) => all(child)),
];

beforeEach(() => {
  studioStore.getState().loadExercise('dumbbell_bicep_curl');
  studioStore.getState().setTime(0);
});

describe('first-party Contact panel DOM', () => {
  it('renders the production contact diagnostics and follows the playhead', () => {
    const panel = createContactPanelDom(fakeDocument(), studioStore);
    const nodes = all(fake(panel.element));
    expect(fake(panel.element).dataset.hgptPanel).toBe('contacts-first-party');
    expect(nodes.filter((node) => node.className.startsWith('contact-card '))).toHaveLength(2);
    const note = nodes.find((node) => node.className === 'panel__note');
    expect(note?.textContent).toContain('0.00s');

    studioStore.getState().setTime(0.5);
    const updated = all(fake(panel.element)).find((node) => node.className === 'panel__note');
    expect(updated?.textContent).toContain('0.50s');
    panel.dispose();
  });

  it('routes lock toggles through the existing edit/history path and detaches on dispose', () => {
    const panel = createContactPanelDom(fakeDocument(), studioStore);
    const before = studioStore.getState();
    const lock = before.document.clip.locks[0];
    expect(lock).toBeDefined();
    const input = all(fake(panel.element)).find((node) => node.type === 'checkbox');
    expect(input).toBeDefined();
    input!.checked = !lock!.enabled;
    input!.dispatchEvent({ type: 'change' } as Event);

    const after = studioStore.getState();
    expect(after.document.clip.locks.find((candidate) => candidate.id === lock!.id)?.enabled).toBe(!lock!.enabled);
    expect(after.history.past).toHaveLength(before.history.past.length + 1);

    const note = all(fake(panel.element)).find((node) => node.className === 'panel__note');
    const textBeforeDispose = note?.textContent;
    panel.dispose();
    studioStore.getState().setTime(0.75);
    expect(note?.textContent).toBe(textBeforeDispose);
  });
});
