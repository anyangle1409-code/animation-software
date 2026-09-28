import { beforeEach, describe, expect, it } from 'vitest';
import { EXERCISES } from '../../exercises/library';
import { studioStore } from '../storeCore';
import { createMusclePanelDom } from './musclePanelDom';

class FakeClassList {
  private values = new Set<string>();
  replace(value: string): void {
    this.values = new Set(value.split(/\s+/).filter(Boolean));
  }
  contains(name: string): boolean {
    return this.values.has(name);
  }
  toString(): string {
    return [...this.values].join(' ');
  }
}

class FakeElement {
  readonly classList = new FakeClassList();
  readonly dataset: Record<string, string> = {};
  readonly children: FakeElement[] = [];
  readonly style: { background?: string } = {};
  textContent: string | null = null;
  type = '';
  value = '';
  checked = false;
  hidden = false;
  title = '';
  private readonly listeners = new Map<string, Set<EventListenerOrEventListenerObject>>();

  get className(): string {
    return this.classList.toString();
  }
  set className(value: string) {
    this.classList.replace(value);
  }
  append(...nodes: FakeElement[]): void {
    this.children.push(...nodes);
  }
  replaceChildren(...nodes: FakeElement[]): void {
    this.children.splice(0, this.children.length, ...nodes);
  }
  addEventListener(type: string, listener: EventListenerOrEventListenerObject): void {
    const listeners = this.listeners.get(type) ?? new Set<EventListenerOrEventListenerObject>();
    listeners.add(listener);
    this.listeners.set(type, listeners);
  }
  removeEventListener(type: string, listener: EventListenerOrEventListenerObject): void {
    this.listeners.get(type)?.delete(listener);
  }
  dispatch(type: string): void {
    const event = { type } as Event;
    for (const listener of this.listeners.get(type) ?? []) {
      if (typeof listener === 'function') listener(event);
      else listener.handleEvent(event);
    }
  }
}

const fakeDocument = (): Pick<Document, 'createElement'> => ({
  createElement: (() => new FakeElement()) as unknown as Document['createElement'],
});

const fake = (element: Element): FakeElement => element as unknown as FakeElement;

beforeEach(() => {
  studioStore.getState().loadExercise(EXERCISES[0].id);
  studioStore.getState().setTime(0);
});

describe('first-party Muscle diagnostics panel DOM', () => {
  it('renders live diagnostics and preserves local filter semantics', () => {
    const panel = createMusclePanelDom(fakeDocument(), studioStore);

    expect(panel.element.dataset.hgptPanel).toBe('muscles-first-party');
    expect(panel.controls.activeOnly.checked).toBe(false);
    expect(panel.controls.region.value).toBe('all');
    expect(panel.elements.hint.textContent).toContain('0.00s');
    expect(fake(panel.elements.list).children.length).toBeGreaterThan(0);
    expect(panel.elements.empty.hidden).toBe(true);

    const initialCount = fake(panel.elements.list).children.length;
    panel.controls.activeOnly.checked = true;
    fake(panel.controls.activeOnly).dispatch('change');
    const activeCount = fake(panel.elements.list).children.length;
    expect(activeCount).toBeLessThan(initialCount);

    panel.controls.activeOnly.checked = false;
    fake(panel.controls.activeOnly).dispatch('change');
    panel.controls.region.value = 'arms';
    fake(panel.controls.region).dispatch('change');
    const armCount = fake(panel.elements.list).children.length;
    expect(armCount).toBeGreaterThan(0);
    expect(armCount).toBeLessThan(initialCount);

    panel.dispose();
  });

  it('tracks playhead changes and detaches from the Studio store on dispose', () => {
    const panel = createMusclePanelDom(fakeDocument(), studioStore);

    studioStore.getState().setTime(0.5);
    expect(panel.elements.hint.textContent).toContain('0.50s');

    panel.dispose();
    studioStore.getState().setTime(0.75);
    expect(panel.elements.hint.textContent).toContain('0.50s');
  });
});
