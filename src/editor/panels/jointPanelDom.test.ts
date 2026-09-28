import { beforeEach, describe, expect, it } from 'vitest';
import { studioStore } from '../storeCore';
import { createJointPanelDom } from './jointPanelDom';

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
const find = (root: FakeElement, id: string): FakeElement => all(root).find((node) => node.dataset.hgptJointControl === id)!;

beforeEach(() => {
  studioStore.getState().loadExercise('dumbbell_bicep_curl');
  studioStore.getState().selectBone(null);
  studioStore.getState().setTime(0);
});

describe('first-party Joint panel DOM', () => {
  it('selects a bone and edits limit-aware axes through existing history actions', () => {
    const panel = createJointPanelDom(fakeDocument(), studioStore);
    const root = fake(panel.element);
    expect(root.dataset.hgptPanel).toBe('joint-first-party');
    const select = find(root, 'bone');
    select.value = 'forearm_l'; select.dispatchEvent({ type: 'change' } as Event);
    expect(studioStore.getState().selection.bone).toBe('forearm_l');
    const axis = find(root, 'axis-x-number');
    expect(axis.type).toBe('number');
    const history = studioStore.getState().history.past.length;
    axis.value = '35'; axis.dispatchEvent({ type: 'change' } as Event);
    expect(studioStore.getState().history.past.length).toBe(history + 1);
    expect(find(root, 'axis-x-number').value).toBe('35');
    panel.dispose();
  });

  it('keeps finger visibility local and routes pose and timing actions through the store', () => {
    studioStore.getState().selectBone('forearm_l');
    const panel = createJointPanelDom(fakeDocument(), studioStore);
    const root = fake(panel.element);
    const count = find(root, 'bone').children.length;
    const fingers = find(root, 'fingers');
    fingers.checked = true; fingers.dispatchEvent({ type: 'change' } as Event);
    expect(find(root, 'bone').children.length).toBeGreaterThan(count);
    find(root, 'copy-pose').click();
    expect(studioStore.getState().clipboard).not.toBeNull();
    const timing = find(root, 'custom-timing');
    timing.checked = true; timing.dispatchEvent({ type: 'change' } as Event);
    const key = studioStore.getState().document.clip.keyframes[0];
    expect(key.jointTiming?.forearm_l).toEqual({ delay: 0, finish: 1 });
    panel.dispose();
  });
});
