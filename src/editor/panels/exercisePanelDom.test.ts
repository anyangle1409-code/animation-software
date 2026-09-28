import { beforeEach, describe, expect, it } from 'vitest';
import { studioStore } from '../storeCore';
import { createExercisePanelDom } from './exercisePanelDom';

class FakeStyle { background = ''; }

class FakeElement {
  readonly dataset: Record<string, string> = {};
  readonly children: FakeElement[] = [];
  readonly attributes = new Map<string, string>();
  readonly style = new FakeStyle();
  className = '';
  textContent: string | null = null;
  type = '';
  value = '';
  min = '';
  max = '';
  step = '';
  private readonly listeners = new Map<string, Set<EventListenerOrEventListenerObject>>();

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
const all = (root: FakeElement): FakeElement[] => [root, ...root.children.flatMap((child) => all(child))];

beforeEach(() => {
  studioStore.getState().loadExercise('dumbbell_bicep_curl');
});

describe('first-party Exercise panel DOM', () => {
  it('renders all tempo controls, muscle metadata and grip closure', () => {
    const panel = createExercisePanelDom(fakeDocument(), studioStore);
    const nodes = all(fake(panel.element));
    expect(fake(panel.element).dataset.hgptPanel).toBe('exercise-first-party');
    expect(nodes.filter((node) => node.type === 'number')).toHaveLength(4);
    const closure = nodes.find((node) => node.type === 'range');
    expect(closure).toBeDefined();
    expect(closure?.attributes.get('aria-label')).toBe('Grip closure');
    expect(nodes.filter((node) => node.className === 'muscle-list__name').length).toBeGreaterThan(0);
    panel.dispose();
  });

  it('routes tempo and grip edits through the existing regeneration/history actions', () => {
    const panel = createExercisePanelDom(fakeDocument(), studioStore);
    const nodes = all(fake(panel.element));
    const number = nodes.find((node) => node.type === 'number');
    const closure = nodes.find((node) => node.type === 'range');
    expect(number).toBeDefined();
    expect(closure).toBeDefined();

    const beforeTempo = studioStore.getState();
    const originalEccentric = beforeTempo.document.exercise.tempo.eccentric;
    number!.value = String(originalEccentric + 0.1);
    number!.dispatchEvent({ type: 'input' } as Event);
    const afterTempo = studioStore.getState();
    expect(afterTempo.document.exercise.tempo.eccentric).toBeCloseTo(originalEccentric + 0.1);
    expect(afterTempo.history.past).toHaveLength(beforeTempo.history.past.length + 1);

    const beforeClosure = studioStore.getState();
    const nextClosure = Math.max(0, beforeClosure.document.exercise.hands.closure - 0.05);
    const liveClosure = all(fake(panel.element)).find((node) => node.type === 'range');
    expect(liveClosure).toBeDefined();
    liveClosure!.value = String(nextClosure);
    liveClosure!.dispatchEvent({ type: 'input' } as Event);
    const afterClosure = studioStore.getState();
    expect(afterClosure.document.exercise.hands.closure).toBeCloseTo(nextClosure);
    expect(afterClosure.history.past).toHaveLength(beforeClosure.history.past.length + 1);
    panel.dispose();
  });

  it('detaches from the Studio store on dispose', () => {
    const panel = createExercisePanelDom(fakeDocument(), studioStore);
    const title = fake(panel.element).children[0];
    const textBefore = title?.textContent;
    panel.dispose();
    studioStore.getState().loadExercise('air_squat');
    expect(title?.textContent).toBe(textBefore);
  });
});
