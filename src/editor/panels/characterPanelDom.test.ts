import { beforeEach, describe, expect, it, vi } from 'vitest';
import { characterStore } from '../characterStoreCore';
import { studioStore } from '../storeCore';
import { createCharacterPanelDom } from './characterPanelDom';
import { createMapping, reportMapping } from '../../retargeting/boneMap';

class FakeElement {
  readonly dataset: Record<string, string> = {};
  readonly children: FakeElement[] = [];
  className = '';
  textContent: string | null = null;
  type = '';
  value = '';
  accept = '';
  style: Record<string, string> = {};
  files: File[] | null = null;
  private readonly listeners = new Map<string, Set<EventListenerOrEventListenerObject>>();
  append(...nodes: FakeElement[]): void { this.children.push(...nodes); }
  replaceChildren(...nodes: FakeElement[]): void { this.children.splice(0, this.children.length, ...nodes); }
  addEventListener(type: string, listener: EventListenerOrEventListenerObject): void {
    const listeners = this.listeners.get(type) ?? new Set<EventListenerOrEventListenerObject>();
    listeners.add(listener); this.listeners.set(type, listeners);
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
const all = (root: FakeElement): FakeElement[] => [root, ...root.children.flatMap(all)];
const control = (root: FakeElement, id: string) => all(root).find((node) => node.dataset.hgptCharacterControl === id)!;

beforeEach(() => { characterStore.getState().clear(); characterStore.getState().setBindMode('preserve'); });

describe('first-party Character panel DOM', () => {
  it('routes source and bind selection through the character store and disposes its subscription', () => {
    const panel = createCharacterPanelDom(fakeDocument(), characterStore, studioStore);
    const root = fake(panel.element);
    expect(root.dataset.hgptPanel).toBe('character-first-party');
    const bind = control(root, 'bind-mode');
    bind.value = 'rebind'; bind.dispatchEvent({ type: 'change' } as Event);
    expect(characterStore.getState().bindMode).toBe('rebind');
    expect(control(root, 'bind-mode').value).toBe('rebind');
    panel.dispose();
    characterStore.getState().setBindMode('preserve');
    expect(control(root, 'bind-mode').value).toBe('rebind');
  });

  it('keeps import input and button wired, clears input and switches view after load', async () => {
    const panel = createCharacterPanelDom(fakeDocument(), characterStore, studioStore);
    const root = fake(panel.element);
    const input = control(root, 'file');
    const click = vi.spyOn(input, 'click');
    control(root, 'import').click();
    expect(click).toHaveBeenCalledOnce();
    const load = vi.spyOn(characterStore.getState(), 'load').mockResolvedValue();
    const setViewMode = vi.spyOn(studioStore.getState(), 'setViewMode');
    const file = { name: 'candidate.glb' } as File;
    input.files = [file]; input.value = 'candidate.glb';
    input.dispatchEvent({ type: 'change' } as Event);
    await vi.waitFor(() => expect(setViewMode).toHaveBeenCalledWith('character'));
    expect(load).toHaveBeenCalledWith(file);
    expect(input.value).toBe('');
    load.mockRestore(); setViewMode.mockRestore(); panel.dispose();
  });

  it('renders the required bone mapping and routes edits, save and removal', () => {
    const mapping = createMapping('Candidate', 'source');
    mapping.bones.pelvis = 'Hips';
    characterStore.setState({ name: 'Candidate', mapping, report: reportMapping(mapping) });
    const panel = createCharacterPanelDom(fakeDocument(), characterStore, studioStore);
    const root = fake(panel.element);
    const pelvis = all(root).find((node) => node.dataset.hgptCharacterBone === 'pelvis');
    expect(pelvis?.value).toBe('Hips');
    const setBone = vi.spyOn(characterStore.getState(), 'setBone').mockImplementation(() => {});
    pelvis!.value = ''; pelvis!.dispatchEvent({ type: 'change' } as Event);
    expect(setBone).toHaveBeenCalledWith('pelvis', null);
    const persist = vi.spyOn(characterStore.getState(), 'persist').mockImplementation(() => {});
    control(root, 'persist').click();
    expect(persist).toHaveBeenCalledOnce();
    setBone.mockRestore(); persist.mockRestore();
    control(root, 'remove').click();
    expect(characterStore.getState().name).toBeNull();
    panel.dispose();
  });
});
