import { afterEach, describe, expect, it } from 'vitest';
import { characterStore } from '../characterStoreCore';
import { studioStore } from '../storeCore';
import { createCorrectivePanelDom } from './correctivePanelDom';
import type { CharacterBuild, DeformationControl } from '../../character';

class FakeElement {
  readonly dataset: Record<string, string> = {};
  readonly children: FakeElement[] = [];
  className = '';
  textContent: string | null = null;
  type = '';
  disabled = false;
  value = '';
  min = '';
  max = '';
  step = '';
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
const all = (node: FakeElement): FakeElement[] => [node, ...node.children.flatMap(all)];
const fake = (node: Element): FakeElement => node as unknown as FakeElement;

afterEach(() => {
  characterStore.getState().setActive(null);
  characterStore.getState().setCorrectivesPreview(true);
});

describe('first-party Correctives panel DOM', () => {
  it('preserves raw/production preview routing and the no-character state', () => {
    const panel = createCorrectivePanelDom(fakeDocument(), characterStore, studioStore);
    const root = fake(panel.element);
    expect(root.dataset.hgptPanel).toBe('correctives-first-party');
    expect(all(root).some((node) => node.textContent === 'No active character is mounted.')).toBe(true);
    expect(all(root).find((node) => node.dataset.hgptCorrectiveControl === 'scan')?.disabled).toBe(true);
    all(root).find((node) => node.dataset.hgptCorrectiveControl === 'raw')!.click();
    expect(characterStore.getState().correctivesPreview).toBe(false);
    expect(all(root).find((node) => node.dataset.hgptCorrectiveControl === 'raw')?.className).toBe('is-active');
    all(root).find((node) => node.dataset.hgptCorrectiveControl === 'on')!.click();
    expect(characterStore.getState().correctivesPreview).toBe(true);
    panel.dispose();
  });

  it('stops reacting to character changes after disposal', () => {
    const panel = createCorrectivePanelDom(fakeDocument(), characterStore, studioStore);
    const before = fake(panel.element).children[3];
    panel.dispose();
    characterStore.getState().setCorrectivesPreview(false);
    expect(fake(panel.element).children[3]).toBe(before);
  });

  it('routes authored corrective presets and reset through the character revision', () => {
    let value = 0.5;
    const control: DeformationControl = {
      id: 'shoulder', label: 'Shoulder', min: 0, max: 1, step: 0.01,
      defaultValue: 0.5, get value() { return value; }, set(next) { value = next; },
    };
    characterStore.getState().setActive({ meshes: [], deformation: { update() {}, controls: [control] } } as unknown as CharacterBuild);
    const panel = createCorrectivePanelDom(fakeDocument(), characterStore, studioStore);
    const root = fake(panel.element);
    const before = characterStore.getState().deformationRevision;
    all(root).find((node) => node.dataset.hgptCorrectiveControl === 'preset-shoulder-1')!.click();
    expect(value).toBe(1);
    expect(characterStore.getState().deformationRevision).toBe(before + 1);
    all(root).find((node) => node.dataset.hgptCorrectiveControl === 'reset-shoulder')!.click();
    expect(value).toBe(0.5);
    expect(characterStore.getState().deformationRevision).toBe(before + 2);
    panel.dispose();
  });
});
