import { beforeEach, describe, expect, it } from 'vitest';
import { studioStore } from '../storeCore';
import { createGripPanelDom } from './gripPanelDom';

class FakeElement {
  readonly dataset: Record<string, string> = {};
  readonly children: FakeElement[] = [];
  className = '';
  textContent: string | null = null;
  type = '';
  value = '';
  min = '';
  max = '';
  step = '';
  checked = false;
  disabled = false;
  private readonly listeners = new Map<string, Set<EventListenerOrEventListenerObject>>();
  append(...nodes: FakeElement[]): void { this.children.push(...nodes); }
  replaceChildren(...nodes: FakeElement[]): void { this.children.splice(0, this.children.length, ...nodes); }
  addEventListener(type: string, listener: EventListenerOrEventListenerObject): void {
    const set = this.listeners.get(type) ?? new Set<EventListenerOrEventListenerObject>();
    set.add(listener); this.listeners.set(type, set);
  }
  dispatchEvent(event: Event): boolean {
    for (const listener of this.listeners.get(event.type) ?? []) {
      if (typeof listener === 'function') listener(event); else listener.handleEvent(event);
    }
    return true;
  }
  click(): void { this.dispatchEvent({ type: 'click' } as Event); }
}
const fakeDocument = (): Pick<Document, 'createElement'> => ({
  createElement: (() => new FakeElement()) as unknown as Document['createElement'],
});
const fake = (element: Element): FakeElement => element as unknown as FakeElement;
const all = (node: FakeElement): FakeElement[] => [node, ...node.children.flatMap(all)];
const find = (root: FakeElement, id: string): FakeElement => all(root).find((node) => node.dataset.hgptGripControl === id)!;

beforeEach(() => {
  studioStore.getState().loadExercise('dumbbell_bicep_curl');
  studioStore.getState().setTime(0);
});

describe('first-party Grip panel DOM', () => {
  it('routes global/profile/digit closure through existing Studio actions', () => {
    const panel = createGripPanelDom(fakeDocument(), studioStore);
    const root = fake(panel.element);
    expect(root.dataset.hgptPanel).toBe('grip-first-party');
    const closure = find(root, 'closure');
    closure.value = '0.7'; closure.dispatchEvent({ type: 'change' } as Event);
    expect(studioStore.getState().document.exercise.hands.closure).toBeCloseTo(0.7);
    const digit = find(root, 'digit-thumb');
    digit.value = '0.8'; digit.dispatchEvent({ type: 'change' } as Event);
    expect(studioStore.getState().document.exercise.hands.digitClosure?.thumb).toBeCloseTo(0.8);
    find(root, 'reset-digits').click();
    expect(studioStore.getState().document.exercise.hands.digitClosure).toBeUndefined();
    panel.dispose();
  });

  it('exposes measured one-hand fit and routes handle calibration edits', () => {
    const panel = createGripPanelDom(fakeDocument(), studioStore);
    const root = fake(panel.element);
    expect(all(root).some((node) => node.className === 'grip-fit')).toBe(true);
    const x = all(root).find((node) => node.dataset.hgptGripControl?.endsWith('-offset-x'));
    expect(x).toBeDefined();
    const id = x!.dataset.hgptGripControl!.slice(0, -'-offset-x'.length);
    x!.value = '3'; x!.dispatchEvent({ type: 'change' } as Event);
    const instance = studioStore.getState().document.exercise.equipment.instances.find((item) => item.id === id);
    expect(instance?.attachment.mode).toBe('hand');
    if (instance?.attachment.mode === 'hand') expect(instance.attachment.gripOffset?.x).toBeCloseTo(0.003);
    panel.dispose();
  });
});
