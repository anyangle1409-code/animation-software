import { beforeEach, describe, expect, it } from 'vitest';
import { EXERCISES } from '../../exercises/library';
import { studioStore } from '../storeCore';
import { createComparisonPanelDom } from './comparisonPanelDom';

class FakeClassList {
  private values = new Set<string>();
  replace(value: string): void { this.values = new Set(value.split(/\s+/).filter(Boolean)); }
  contains(name: string): boolean { return this.values.has(name); }
  toString(): string { return [...this.values].join(' '); }
}

class FakeElement {
  readonly classList = new FakeClassList();
  readonly dataset: Record<string, string> = {};
  readonly children: FakeElement[] = [];
  readonly attributes = new Map<string, string>();
  namespaceURI: string | null = null;
  textContent: string | null = null;
  type = '';
  disabled = false;
  private readonly listeners = new Map<string, Set<EventListenerOrEventListenerObject>>();

  get className(): string { return this.classList.toString(); }
  set className(value: string) { this.classList.replace(value); }
  append(...nodes: FakeElement[]): void { this.children.push(...nodes); }
  replaceChildren(...nodes: FakeElement[]): void { this.children.splice(0, this.children.length, ...nodes); }
  setAttribute(name: string, value: string): void { this.attributes.set(name, value); }
  addEventListener(type: string, listener: EventListenerOrEventListenerObject): void {
    const listeners = this.listeners.get(type) ?? new Set<EventListenerOrEventListenerObject>();
    listeners.add(listener);
    this.listeners.set(type, listeners);
  }
  removeEventListener(type: string, listener: EventListenerOrEventListenerObject): void {
    this.listeners.get(type)?.delete(listener);
  }
  click(): void {
    const event = { type: 'click' } as Event;
    for (const listener of this.listeners.get('click') ?? []) {
      if (typeof listener === 'function') listener(event);
      else listener.handleEvent(event);
    }
  }
}

const fakeDocument = (): Pick<Document, 'createElement' | 'createElementNS'> => ({
  createElement: (() => new FakeElement()) as unknown as Document['createElement'],
  createElementNS: ((namespace: string) => {
    const element = new FakeElement();
    element.namespaceURI = namespace;
    return element;
  }) as unknown as Document['createElementNS'],
});

const fake = (element: Element): FakeElement => element as unknown as FakeElement;

beforeEach(() => {
  studioStore.getState().loadExercise(EXERCISES[0].id);
  studioStore.getState().clearComparison();
  studioStore.getState().selectBone(null);
  studioStore.getState().setTime(0);
});

describe('first-party Pose A/B Comparison panel DOM', () => {
  it('captures review-only snapshots without editing document/history and renders SVG diagrams', () => {
    const panel = createComparisonPanelDom(fakeDocument(), studioStore);
    const before = studioStore.getState();
    const documentBefore = before.document;
    const historyBefore = before.history;

    expect(panel.controls.clear.disabled).toBe(true);
    panel.controls.captureA.click();

    const afterA = studioStore.getState();
    expect(afterA.comparison.a).not.toBeNull();
    expect(afterA.document).toBe(documentBefore);
    expect(afterA.history).toBe(historyBefore);
    expect(panel.controls.clear.disabled).toBe(false);

    const aChildren = fake(panel.elements.aCard).children;
    const svg = aChildren[1];
    expect(svg?.namespaceURI).toBe('http://www.w3.org/2000/svg');
    expect(svg?.attributes.get('role')).toBe('img');
    expect(svg?.children.length).toBeGreaterThan(0);

    panel.dispose();
  });

  it('renders selected-joint deltas, clear behavior and detaches on dispose', () => {
    const panel = createComparisonPanelDom(fakeDocument(), studioStore);

    panel.controls.captureA.click();
    studioStore.getState().setTime(0.5);
    panel.controls.captureB.click();
    studioStore.getState().selectBone('forearm_l');

    expect(fake(panel.elements.detail).children).toHaveLength(1);
    expect(fake(panel.elements.detail).children[0]?.classList.contains('comparison-delta')).toBe(true);

    panel.controls.clear.click();
    expect(studioStore.getState().comparison).toEqual({ a: null, b: null });
    expect(panel.controls.clear.disabled).toBe(true);

    panel.dispose();
    studioStore.getState().captureComparison('a');
    expect(panel.controls.clear.disabled).toBe(true);
  });
});
