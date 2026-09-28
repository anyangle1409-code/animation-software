import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { characterStore } from '../characterStoreCore';
import { studioStore } from '../storeCore';
import { createReviewPanelDom } from './reviewPanelDom';

class FakeElement {
  readonly dataset: Record<string, string> = {};
  readonly children: FakeElement[] = [];
  className = '';
  textContent: string | null = null;
  type = '';
  disabled = false;
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
  click(): void {
    const event = { type: 'click' } as Event;
    for (const listener of this.listeners.get('click') ?? []) {
      if (typeof listener === 'function') listener(event);
      else listener.handleEvent(event);
    }
  }
}

const fakeDocument = (): Pick<Document, 'createElement'> => ({
  createElement: (() => new FakeElement()) as unknown as Document['createElement'],
});
const fake = (element: Element): FakeElement => element as unknown as FakeElement;
const all = (element: FakeElement): FakeElement[] => [
  element,
  ...element.children.flatMap((child) => all(child)),
];

beforeEach(() => {
  studioStore.getState().loadExercise('dumbbell_bicep_curl');
  studioStore.getState().selectBone(null);
  studioStore.getState().clearVisualReview();
  studioStore.getState().setCamera('recommended');
  characterStore.setState({
    sourceStatus: { kind: 'idle' },
    correctivesPreview: true,
  });
});

afterEach(() => {
  studioStore.getState().clearVisualReview();
  characterStore.setState({
    sourceStatus: { kind: 'idle' },
    correctivesPreview: true,
  });
});

describe('first-party Review panel DOM', () => {
  it('renders the automated gates and default curl movement diagnostics', () => {
    const panel = createReviewPanelDom(fakeDocument(), studioStore, characterStore);
    const nodes = all(fake(panel.element));
    expect(fake(panel.element).dataset.hgptPanel).toBe('review-first-party');
    expect(nodes.find((node) => node.className.includes('review-status'))?.textContent).toBeNull();
    expect(nodes.filter((node) => node.className === 'is-pass').length).toBeGreaterThan(0);
    expect(nodes.some((node) => node.textContent === 'Highest angular speed')).toBe(true);
    expect(nodes.some((node) => node.textContent === 'Bilateral mirror mismatch')).toBe(true);
    expect(nodes.some((node) => node.textContent === 'Return error')).toBe(true);
    panel.dispose();
  });

  it('routes movement locators and exact visual sign-off identity through existing stores', () => {
    const panel = createReviewPanelDom(fakeDocument(), studioStore, characterStore);
    let nodes = all(fake(panel.element));

    nodes.find((node) => node.dataset.hgptReviewControl === 'focus')!.click();
    expect(studioStore.getState().selection.bone).toBe('forearm_l');
    expect(studioStore.getState().camera).toBe('focus');

    nodes = all(fake(panel.element));
    const signoff = nodes.find((node) => node.dataset.hgptReviewControl === 'visual-signoff');
    expect(signoff?.disabled).toBe(false);
    signoff!.click();

    const state = studioStore.getState();
    const character = characterStore.getState();
    expect(state.visualReview?.document).toBe(state.document);
    expect(state.visualReview?.characterSourceId).toBe(character.sourceId);
    expect(state.visualReview?.deformationRevision).toBe(character.deformationRevision);

    studioStore.getState().regenerate();
    nodes = all(fake(panel.element));
    expect(nodes.find((node) => node.dataset.hgptReviewControl === 'visual-signoff')?.textContent)
      .toBe('Mark visual review passed');
    panel.dispose();
  });

  it('blocks production sign-off while raw skinning is active and detaches on disposal', () => {
    characterStore.getState().setCorrectivesPreview(false);
    const panel = createReviewPanelDom(fakeDocument(), studioStore, characterStore);
    const root = fake(panel.element);
    let nodes = all(root);
    expect(nodes.find((node) => node.dataset.hgptReviewControl === 'visual-signoff')?.disabled)
      .toBe(true);
    expect(nodes.some((node) => node.textContent === 'Enable Correctives on before production visual sign-off.'))
      .toBe(true);

    const before = [...root.children];
    panel.dispose();
    characterStore.getState().setCorrectivesPreview(true);
    nodes = all(root);
    expect(root.children).toEqual(before);
    expect(nodes.find((node) => node.dataset.hgptReviewControl === 'visual-signoff')?.disabled)
      .toBe(true);
  });
});
