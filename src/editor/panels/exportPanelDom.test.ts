import { beforeEach, describe, expect, it } from 'vitest';
import type { GlbExportOptions } from '../../export/glb';
import { characterStore } from '../characterStoreCore';
import { studioStore } from '../storeCore';
import {
  createExportPanelDom,
  type ExportActions,
} from './exportPanelDom';

class FakeElement {
  readonly dataset: Record<string, string> = {};
  readonly children: FakeElement[] = [];
  className = '';
  textContent: string | null = null;
  type = '';
  checked = false;
  disabled = false;
  value = '';
  private readonly listeners = new Map<string, Set<EventListenerOrEventListenerObject>>();

  append(...nodes: FakeElement[]): void { this.children.push(...nodes); }
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
const all = (element: FakeElement): FakeElement[] => [
  element,
  ...element.children.flatMap((child) => all(child)),
];
const flush = async () => {
  await Promise.resolve();
  await Promise.resolve();
};

beforeEach(() => {
  studioStore.getState().loadExercise('dumbbell_bicep_curl');
});

describe('first-party Export panel DOM', () => {
  it('starts with the React defaults and rerenders current clip metadata', () => {
    const actions = stubActions();
    const panel = createExportPanelDom(fakeDocument(), studioStore, characterStore, actions);
    const root = fake(panel.element);
    const nodes = all(root);
    expect(root.dataset.hgptPanel).toBe('export-first-party');
    expect(nodes.find((node) => node.dataset.hgptExportControl === 'sample-rate')?.value).toBe('30');
    expect(nodes.find((node) => node.dataset.hgptExportControl === 'include-equipment')?.checked).toBe(true);
    expect(nodes.find((node) => node.dataset.hgptExportControl === 'animated-glb')?.textContent)
      .toBe('Export bicep_curl.glb');
    expect(nodes.find((node) => node.dataset.hgptExportControl === 'metadata')?.textContent)
      .toBe('Export dumbbell_bicep_curl.json');
    panel.dispose();
  });

  it('preserves export options, filenames and done status for every action', async () => {
    const calls: {
      glb: { options: GlbExportOptions; filename?: string }[];
      json: string[];
    } = { glb: [], json: [] };
    const actions = stubActions(calls);
    const panel = createExportPanelDom(fakeDocument(), studioStore, characterStore, actions);
    const root = fake(panel.element);

    let nodes = all(root);
    const rate = nodes.find((node) => node.dataset.hgptExportControl === 'sample-rate')!;
    rate.value = '60';
    rate.dispatchEvent({ type: 'change' } as Event);
    nodes = all(root);
    const equipment = nodes.find((node) => node.dataset.hgptExportControl === 'include-equipment')!;
    equipment.checked = false;
    equipment.dispatchEvent({ type: 'change' } as Event);

    all(root).find((node) => node.dataset.hgptExportControl === 'animated-glb')!.click();
    await flush();
    expect(calls.glb[0]?.options).toMatchObject({
      fps: 60,
      includeEquipment: false,
      character: characterStore.getState().sourceId,
    });
    expect(calls.glb[0]?.filename).toBe('bicep_curl.glb');
    expect(all(root).find((node) => node.dataset.hgptExportStatus === 'done')?.textContent)
      .toBe('GLB downloaded.');

    all(root).find((node) => node.dataset.hgptExportControl === 'clip-glb')!.click();
    await flush();
    expect(calls.glb[1]?.options).toEqual({ fps: 60, clipOnly: true });
    expect(calls.glb[1]?.filename).toBe('bicep_curl.anim.glb');

    all(root).find((node) => node.dataset.hgptExportControl === 'clip-json')!.click();
    await flush();
    all(root).find((node) => node.dataset.hgptExportControl === 'metadata')!.click();
    await flush();
    expect(calls.json).toEqual([
      'bicep_curl.anim.json',
      'dumbbell_bicep_curl.json',
    ]);
    panel.dispose();
  });

  it('reports export errors and resets local options on a fresh mount', async () => {
    const actions = stubActions();
    actions.exportGlb = async () => { throw new Error('export failed'); };
    const first = createExportPanelDom(fakeDocument(), studioStore, characterStore, actions);
    const root = fake(first.element);
    all(root).find((node) => node.dataset.hgptExportControl === 'animated-glb')!.click();
    await flush();
    expect(all(root).find((node) => node.dataset.hgptExportStatus === 'error')?.textContent)
      .toBe('export failed');

    const rate = all(root).find((node) => node.dataset.hgptExportControl === 'sample-rate')!;
    rate.value = '24';
    rate.dispatchEvent({ type: 'change' } as Event);
    first.dispose();

    const second = createExportPanelDom(fakeDocument(), studioStore, characterStore, stubActions());
    expect(all(fake(second.element)).find((node) => node.dataset.hgptExportControl === 'sample-rate')?.value)
      .toBe('30');
    second.dispose();
  });
});

function stubActions(
  calls: {
    glb: { options: GlbExportOptions; filename?: string }[];
    json: string[];
  } = { glb: [], json: [] },
): ExportActions {
  let pendingGlbIndex = -1;
  return {
    exportGlb: (async (_clip, _exercise, options = {}) => {
      calls.glb.push({ options });
      pendingGlbIndex = calls.glb.length - 1;
      return new Blob(['glb']);
    }) as ExportActions['exportGlb'],
    exportAnimationJson: (() => ({ kind: 'animation' })) as unknown as ExportActions['exportAnimationJson'],
    exportMetadataJson: (() => ({ kind: 'metadata' })) as unknown as ExportActions['exportMetadataJson'],
    downloadBlob: ((_blob: Blob, filename: string) => {
      if (pendingGlbIndex >= 0) {
        calls.glb[pendingGlbIndex]!.filename = filename;
        pendingGlbIndex = -1;
      }
    }) as ExportActions['downloadBlob'],
    downloadJson: ((_value: unknown, filename: string) => {
      calls.json.push(filename);
    }) as ExportActions['downloadJson'],
  };
}
