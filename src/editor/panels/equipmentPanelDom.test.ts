import { beforeEach, describe, expect, it } from 'vitest';
import { studioStore } from '../storeCore';
import { createEquipmentPanelDom } from './equipmentPanelDom';

class FakeElement {
  readonly dataset: Record<string, string> = {};
  readonly children: FakeElement[] = [];
  className = '';
  textContent: string | null = null;
  type = '';
  value = '';
  step = '';
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
  click(): void { this.dispatchEvent({ type: 'click' } as Event); }
}

const fakeDocument = (): Pick<Document, 'createElement'> => ({
  createElement: (() => new FakeElement()) as unknown as Document['createElement'],
});
const fake = (element: Element): FakeElement => element as unknown as FakeElement;
const all = (root: FakeElement): FakeElement[] => [root, ...root.children.flatMap((child) => all(child))];

beforeEach(() => {
  studioStore.getState().loadExercise('pull_up');
  studioStore.getState().selectEquipment(null);
});

describe('first-party Equipment panel DOM', () => {
  it('renders/selects static equipment and exposes its object/socket editors', () => {
    const panel = createEquipmentPanelDom(fakeDocument(), studioStore);
    let nodes = all(fake(panel.element));
    expect(fake(panel.element).dataset.hgptPanel).toBe('equipment-first-party');

    const rack = nodes.find((node) => node.dataset.hgptEquipmentId === 'rack');
    expect(rack).toBeDefined();
    rack!.click();
    expect(studioStore.getState().selection.equipmentId).toBe('rack');

    nodes = all(fake(panel.element));
    expect(nodes.filter((node) => node.dataset.hgptEquipmentField?.startsWith('position-'))).toHaveLength(3);
    expect(nodes.filter((node) => node.dataset.hgptEquipmentField?.startsWith('rotation-'))).toHaveLength(3);

    const socket = nodes.find((node) => Boolean(node.dataset.hgptSocketId));
    expect(socket?.dataset.hgptSocketId).toBeDefined();
    socket!.click();
    expect(studioStore.getState().selection.socketId).toBe(socket!.dataset.hgptSocketId);

    nodes = all(fake(panel.element));
    expect(nodes.filter((node) => node.dataset.hgptEquipmentField?.startsWith('socket-position-'))).toHaveLength(3);
    expect(nodes.filter((node) => node.dataset.hgptEquipmentField?.startsWith('socket-rotation-'))).toHaveLength(3);
    panel.dispose();
  });

  it('routes static object/socket edits and reset through existing history actions', () => {
    studioStore.getState().selectEquipment('rack');
    const panel = createEquipmentPanelDom(fakeDocument(), studioStore);
    let nodes = all(fake(panel.element));
    const x = nodes.find((node) => node.dataset.hgptEquipmentField === 'position-x');
    expect(x).toBeDefined();
    const historyBefore = studioStore.getState().history.past.length;
    x!.value = '12.5';
    x!.dispatchEvent({ type: 'input' } as Event);
    const afterObject = studioStore.getState();
    expect(afterObject.document.exercise.equipment.instances.find((item) => item.id === 'rack')?.position.x)
      .toBeCloseTo(0.125, 9);
    expect(afterObject.history.past).toHaveLength(historyBefore + 1);

    nodes = all(fake(panel.element));
    const socketButton = nodes.find((node) => Boolean(node.dataset.hgptSocketId));
    expect(socketButton?.dataset.hgptSocketId).toBeDefined();
    socketButton!.click();

    nodes = all(fake(panel.element));
    const socketX = nodes.find((node) => node.dataset.hgptEquipmentField === 'socket-position-x');
    expect(socketX).toBeDefined();
    const historyAfterSelect = studioStore.getState().history.past.length;
    socketX!.value = String(Number(socketX!.value) + 1);
    socketX!.dispatchEvent({ type: 'input' } as Event);
    expect(studioStore.getState().history.past).toHaveLength(historyAfterSelect + 1);

    nodes = all(fake(panel.element));
    const reset = nodes.find((node) => Boolean(node.dataset.hgptSocketReset));
    expect(reset).toBeDefined();
    const socketId = reset!.dataset.hgptSocketReset!;
    reset!.click();
    const instance = studioStore.getState().document.exercise.equipment.instances.find((item) => item.id === 'rack');
    expect(instance?.socketOverrides?.[socketId]).toBeUndefined();
    expect(studioStore.getState().history.past).toHaveLength(historyAfterSelect + 2);
    panel.dispose();
  });

  it('keeps hand-driven equipment transform/socket ownership in Grip', () => {
    studioStore.getState().loadExercise('dumbbell_bicep_curl');
    const panel = createEquipmentPanelDom(fakeDocument(), studioStore);
    let nodes = all(fake(panel.element));
    const first = nodes.find((node) => Boolean(node.dataset.hgptEquipmentId));
    expect(first?.dataset.hgptEquipmentId).toBeDefined();
    first!.click();

    nodes = all(fake(panel.element));
    expect(nodes.filter((node) => Boolean(node.dataset.hgptEquipmentField))).toHaveLength(0);
    const socket = nodes.find((node) => Boolean(node.dataset.hgptSocketId));
    expect(socket).toBeDefined();
    socket!.click();
    expect(studioStore.getState().selection.socketId).toBeNull();
    panel.dispose();
  });
});
