import { beforeEach, describe, expect, it } from 'vitest';
import { sampleClip } from '../../animation/clip';
import { IK_CHAIN_IDS } from '../../ik/chains';
import { studioStore } from '../storeCore';
import { createIKPanelDom } from './ikPanelDom';

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
const all = (root: FakeElement): FakeElement[] => [root, ...root.children.flatMap((child) => all(child))];

beforeEach(() => {
  studioStore.getState().loadExercise('dumbbell_bicep_curl');
  studioStore.getState().setTime(0);
  studioStore.getState().selectHandle(null);
});

describe('first-party IK panel DOM', () => {
  it('renders all chains, viewport-handle state and live handle buttons', () => {
    const panel = createIKPanelDom(fakeDocument(), studioStore);
    const nodes = all(fake(panel.element));
    expect(fake(panel.element).dataset.hgptPanel).toBe('ik-first-party');
    expect(nodes.filter((node) => node.dataset.hgptIkChain)).toHaveLength(IK_CHAIN_IDS.length);
    expect(nodes.find((node) => node.dataset.hgptIkControl === 'show-handles')?.checked)
      .toBe(studioStore.getState().showIkHandles);

    const sample = sampleClip(studioStore.getState().document.clip, studioStore.getState().time);
    const active = IK_CHAIN_IDS.find((id) => sample.ik[id]?.enabled);
    if (active) {
      expect(nodes.find((node) => node.dataset.hgptIkHandle === `${active}-target`)).toBeDefined();
      expect(nodes.find((node) => node.dataset.hgptIkHandle === `${active}-pole`)).toBeDefined();
    }
    panel.dispose();
  });

  it('routes viewport visibility, handle selection and lock edits through existing actions', () => {
    const panel = createIKPanelDom(fakeDocument(), studioStore);
    let nodes = all(fake(panel.element));

    const showHandles = nodes.find((node) => node.dataset.hgptIkControl === 'show-handles');
    expect(showHandles).toBeDefined();
    const beforeVisibility = studioStore.getState().showIkHandles;
    showHandles!.dispatchEvent({ type: 'change' } as Event);
    expect(studioStore.getState().showIkHandles).toBe(!beforeVisibility);

    nodes = all(fake(panel.element));
    const sample = sampleClip(studioStore.getState().document.clip, studioStore.getState().time);
    const active = IK_CHAIN_IDS.find((id) => sample.ik[id]?.enabled);
    if (active) {
      const target = nodes.find((node) => node.dataset.hgptIkHandle === `${active}-target`);
      expect(target).toBeDefined();
      target!.dispatchEvent({ type: 'click' } as Event);
      expect(studioStore.getState().selection.handle).toEqual({ chain: active, kind: 'target' });
    }

    nodes = all(fake(panel.element));
    const firstLock = studioStore.getState().document.clip.locks[0];
    expect(firstLock).toBeDefined();
    const lockInput = nodes.find((node) => node.dataset.hgptLockId === firstLock!.id);
    expect(lockInput).toBeDefined();
    const historyBefore = studioStore.getState().history.past.length;
    lockInput!.checked = !firstLock!.enabled;
    lockInput!.dispatchEvent({ type: 'change' } as Event);
    const after = studioStore.getState();
    expect(after.document.clip.locks.find((lock) => lock.id === firstLock!.id)?.enabled).toBe(!firstLock!.enabled);
    expect(after.history.past).toHaveLength(historyBefore + 1);
    panel.dispose();
  });

  it('detaches from the Studio store on dispose', () => {
    const panel = createIKPanelDom(fakeDocument(), studioStore);
    const heading = fake(panel.element).children[0];
    panel.dispose();
    studioStore.getState().loadExercise('air_squat');
    expect(heading?.textContent).toBe('Inverse kinematics');
  });
});
