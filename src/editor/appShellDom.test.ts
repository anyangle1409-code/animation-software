import { beforeEach, describe, expect, it } from 'vitest';
import { createStudioAppShellDom } from './appShellDom';
import { studioLayoutStore } from './layoutState';

class FakeClassList {
  private values = new Set<string>();

  replace(value: string): void {
    this.values = new Set(value.split(/\s+/).filter(Boolean));
  }

  toggle(name: string, force?: boolean): boolean {
    const enabled = force ?? !this.values.has(name);
    if (enabled) this.values.add(name);
    else this.values.delete(name);
    return enabled;
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
  textContent: string | null = null;
  type = '';
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

const fakeDocument = (): Pick<Document, 'createElement'> => ({
  createElement: (() => new FakeElement()) as Document['createElement'],
});

const fake = (element: Element): FakeElement => element as unknown as FakeElement;

beforeEach(() => {
  studioLayoutStore.setState({
    leftTab: 'joint',
    rightTab: 'exercise',
    panelsOpen: true,
  });
});

describe('first-party Studio app shell DOM', () => {
  it('mirrors layout state using the existing classes and labels', () => {
    const shell = createStudioAppShellDom(fakeDocument(), studioLayoutStore);

    expect(fake(shell.element).classList.contains('studio')).toBe(true);
    expect(fake(shell.element).classList.contains('studio--focus')).toBe(false);
    expect(fake(shell.controls.leftTabs.joint).classList.contains('is-active')).toBe(true);
    expect(fake(shell.controls.rightTabs.exercise).classList.contains('is-active')).toBe(true);
    expect(shell.controls.panelToggle.textContent).toBe('Hide panels');

    expect(shell.slots.leftPanel.dataset.hgptEditorSlot).toBe('left-panel');
    expect(shell.slots.viewport.dataset.hgptEditorSlot).toBe('viewport');
    expect(shell.slots.rightPanel.dataset.hgptEditorSlot).toBe('right-panel');

    studioLayoutStore.getState().setLeftTab('equipment');
    studioLayoutStore.getState().setRightTab('review');
    studioLayoutStore.getState().setPanelsOpen(false);

    expect(fake(shell.controls.leftTabs.equipment).classList.contains('is-active')).toBe(true);
    expect(fake(shell.controls.leftTabs.joint).classList.contains('is-active')).toBe(false);
    expect(fake(shell.controls.rightTabs.review).classList.contains('is-active')).toBe(true);
    expect(fake(shell.element).classList.contains('studio--focus')).toBe(true);
    expect(shell.controls.panelToggle.textContent).toBe('Show panels');

    shell.dispose();
  });

  it('routes tab/toggle clicks through studioLayoutStore and detaches on dispose', () => {
    const shell = createStudioAppShellDom(fakeDocument(), studioLayoutStore);

    fake(shell.controls.leftTabs.character).click();
    fake(shell.controls.rightTabs.export).click();
    fake(shell.controls.panelToggle).click();

    expect(studioLayoutStore.getState().leftTab).toBe('character');
    expect(studioLayoutStore.getState().rightTab).toBe('export');
    expect(studioLayoutStore.getState().panelsOpen).toBe(false);

    shell.dispose();

    fake(shell.controls.leftTabs.grip).click();
    fake(shell.controls.panelToggle).click();

    expect(studioLayoutStore.getState().leftTab).toBe('character');
    expect(studioLayoutStore.getState().panelsOpen).toBe(false);

    studioLayoutStore.getState().setLeftTab('joint');
    expect(fake(shell.controls.leftTabs.character).classList.contains('is-active')).toBe(true);
  });
});
