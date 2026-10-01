import { beforeEach, describe, expect, it } from 'vitest';
import { getExercise } from '../../exercises/library';
import type { GenerationResult } from '../../generation/generate';
import { parsePrompt } from '../../generation/parse';
import { generatorFamily } from '../../generation/families';
import {
  generationStore,
  type Candidate,
} from '../generationStoreCore';
import { studioStore } from '../storeCore';
import { createGeneratePanelDom } from './generatePanelDom';

class FakeElement {
  readonly dataset: Record<string, string> = {};
  readonly children: FakeElement[] = [];
  readonly attributes = new Map<string, string>();
  className = '';
  textContent: string | null = null;
  type = '';
  disabled = false;
  value = '';
  rows = 0;
  private readonly listeners = new Map<string, Set<EventListenerOrEventListenerObject>>();

  append(...nodes: FakeElement[]): void { this.children.push(...nodes); }
  replaceChildren(...nodes: FakeElement[]): void {
    this.children.splice(0, this.children.length, ...nodes);
  }
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

const PROMPT = 'Create a standing hammer curl with 12 kg dumbbells and controlled tempo.';

const passedCandidate = (): Candidate => ({
  key: 'candidate_generate_panel',
  prompt: PROMPT,
  approved: false,
  result: {
    parsed: parsePrompt(PROMPT),
    status: 'passed',
    exercise: getExercise('dumbbell_hammer_curl'),
    attempts: [],
    corrections: [],
    validations: 1,
  } satisfies GenerationResult,
});

beforeEach(() => {
  studioStore.getState().loadExercise('air_squat');
  generationStore.setState({
    prompt: PROMPT,
    running: false,
    progress: [],
    candidates: [],
    selected: null,
    validationCharacter: null,
  });
});

describe('first-party Generate panel DOM', () => {
  it('keeps prompt controls stable and reflects running progress', () => {
    const panel = createGeneratePanelDom(fakeDocument(), generationStore);
    const root = fake(panel.element);
    expect(root.dataset.hgptPanel).toBe('generate-first-party');

    const prompt = all(root).find((item) => item.dataset.hgptGenerateControl === 'prompt');
    expect(prompt).toBeDefined();
    prompt!.value = 'Create a seated dumbbell shoulder press with 10 kg dumbbells.';
    prompt!.dispatchEvent({ type: 'input' } as Event);
    expect(generationStore.getState().prompt).toBe(prompt!.value);

    const simple = all(root).find((item) => item.dataset.hgptGenerateControl === 'example-0');
    expect(simple?.textContent).toBe('exercise: dumbbell shoulder press');
    expect(prompt!.attributes.get('placeholder')).toBe('exercise: dumbbell shoulder press');

    const example = all(root).find((item) => item.dataset.hgptGenerateControl === 'example-1');
    example!.click();
    expect(generationStore.getState().prompt).toContain('incline dumbbell curl');

    generationStore.setState({
      running: true,
      progress: ['one', 'two', 'three', 'four', 'five'],
    });
    const current = all(root);
    expect(current.find((item) => item.dataset.hgptGenerateControl === 'prompt')?.disabled).toBe(true);
    expect(current.find((item) => item.dataset.hgptGenerateControl === 'generate')?.textContent)
      .toBe('Generating…');
    const progress = current.find((item) => item.className === 'generate-progress');
    expect(progress?.children.map((item) => item.textContent)).toEqual(['two', 'three', 'four', 'five']);
    panel.dispose();
  });

  it('labels cable generation as cable equipment rather than bodyweight', () => {
    const prompt = 'exercise: cable triceps pushdown';
    const parsed = parsePrompt(prompt);
    const entry: Candidate = {
      key: 'candidate_cable_panel',
      prompt,
      approved: false,
      result: {
        parsed,
        intent: parsed.intent!,
        family: generatorFamily('extension'),
        reference: 'cable_triceps_pushdown',
        status: 'passed',
        exercise: getExercise('cable_triceps_pushdown'),
        attempts: [],
        corrections: [],
        validations: 1,
      } satisfies GenerationResult,
    };
    generationStore.setState({ candidates: [entry], selected: entry.key });
    const panel = createGeneratePanelDom(fakeDocument(), generationStore);
    const text = all(fake(panel.element)).map((item) => item.textContent).filter(Boolean);
    expect(text).toContain('Cable station');
    expect(text).not.toContain('Bodyweight');
    panel.dispose();
  });

  it('routes preview, approval and discard through the generation and Studio stores', () => {
    const entry = passedCandidate();
    generationStore.setState({ candidates: [entry], selected: entry.key });
    const panel = createGeneratePanelDom(fakeDocument(), generationStore);
    const root = fake(panel.element);

    all(root).find((item) => item.dataset.hgptGenerateControl === `preview-${entry.key}`)!.click();
    expect(studioStore.getState().document.exercise.id).toBe('dumbbell_hammer_curl');

    all(root).find((item) => item.dataset.hgptGenerateControl === `approve-${entry.key}`)!.click();
    expect(generationStore.getState().candidates[0]?.approved).toBe(true);

    all(root).find((item) => item.dataset.hgptGenerateControl === `discard-${entry.key}`)!.click();
    expect(generationStore.getState().candidates).toEqual([]);
    expect(generationStore.getState().selected).toBeNull();
    panel.dispose();
  });

  it('detaches from generation updates after disposal', () => {
    const panel = createGeneratePanelDom(fakeDocument(), generationStore);
    const root = fake(panel.element);
    const dynamic = all(root).find((item) => item.dataset.hgptGenerateRegion === 'dynamic');
    expect(dynamic).toBeDefined();
    const before = [...dynamic!.children];
    panel.dispose();
    generationStore.setState({ running: true, progress: ['detached'] });
    expect(dynamic!.children).toEqual(before);
  });
});
