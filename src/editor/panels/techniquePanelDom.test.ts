import { beforeEach, describe, expect, it } from 'vitest';
import { EXERCISES } from '../../exercises/library';
import { studioStore } from '../storeCore';
import {
  createTechniquePanelDom,
  describeTechniqueRule,
  type TechniqueValidationScheduler,
} from './techniquePanelDom';

class FakeClassList {
  private values = new Set<string>();
  replace(value: string): void { this.values = new Set(value.split(/\s+/).filter(Boolean)); }
  contains(name: string): boolean { return this.values.has(name); }
  toString(): string { return [...this.values].join(' '); }
}

class FakeElement {
  readonly classList = new FakeClassList();
  readonly dataset: Record<string, string> = {};
  readonly children: FakeElement[] = [];
  textContent: string | null = null;
  hidden = false;
  get className(): string { return this.classList.toString(); }
  set className(value: string) { this.classList.replace(value); }
  append(...nodes: FakeElement[]): void { this.children.push(...nodes); }
  replaceChildren(...nodes: FakeElement[]): void { this.children.splice(0, this.children.length, ...nodes); }
}

const fakeDocument = (): Pick<Document, 'createElement'> => ({
  createElement: (() => new FakeElement()) as unknown as Document['createElement'],
});
const fake = (element: Element): FakeElement => element as unknown as FakeElement;

class FakeScheduler implements TechniqueValidationScheduler {
  next = 1;
  readonly scheduled = new Map<number, { callback: () => void; delay: number }>();
  readonly cancelled: number[] = [];

  schedule(callback: () => void, delayMs: number): unknown {
    const id = this.next++;
    this.scheduled.set(id, { callback, delay: delayMs });
    return id;
  }

  cancel(handle: unknown): void {
    const id = Number(handle);
    this.cancelled.push(id);
    this.scheduled.delete(id);
  }
}

beforeEach(() => {
  studioStore.getState().loadExercise(EXERCISES[0].id);
  studioStore.setState({ validation: null });
});

describe('first-party Technique panel DOM', () => {
  it('preserves the 120 ms validation scheduling and cancellation lifecycle', () => {
    const scheduler = new FakeScheduler();
    const panel = createTechniquePanelDom(fakeDocument(), studioStore, scheduler);

    expect([...scheduler.scheduled.values()][0]?.delay).toBe(120);
    const firstHandle = [...scheduler.scheduled.keys()][0];

    studioStore.getState().loadExercise(EXERCISES[1].id);
    expect(scheduler.cancelled).toContain(firstHandle);
    expect([...scheduler.scheduled.values()].at(-1)?.delay).toBe(120);

    const latestHandle = [...scheduler.scheduled.keys()].at(-1);
    panel.dispose();
    expect(scheduler.cancelled).toContain(latestHandle);
  });

  it('renders validation status, rule state and common errors from studioStore', () => {
    const scheduler = new FakeScheduler();
    const panel = createTechniquePanelDom(fakeDocument(), studioStore, scheduler);
    const exercise = studioStore.getState().document.exercise;
    const firstRule = exercise.technique[0];

    studioStore.setState({
      validation: {
        violations: [],
        perFrame: [],
        loopClosed: true,
        unreachable: [],
        frames: 42,
      },
    });

    expect(panel.elements.status.hidden).toBe(false);
    expect(fake(panel.elements.status).classList.contains('is-ok')).toBe(true);
    expect(panel.elements.status.textContent).toContain(
      `All ${exercise.technique.length} rules pass across 42 sampled frames.`,
    );
    expect(fake(panel.elements.ruleList).children).toHaveLength(exercise.technique.length);
    expect(fake(panel.elements.errorList).children).toHaveLength(exercise.commonErrors.length);

    if (firstRule) {
      studioStore.setState({
        validation: {
          violations: [{
            ruleId: firstRule.id,
            message: 'Probe violation',
            severity: 'warning',
            time: 0.5,
          }],
          perFrame: [],
          loopClosed: false,
          unreachable: [{ time: 0.5, chain: 'arm_l', error: 0.01 }],
          frames: 42,
        },
      });
      const firstItem = fake(panel.elements.ruleList).children[0];
      expect(firstItem?.classList.contains('is-failing')).toBe(true);
      expect(panel.elements.status.textContent).toContain(
        `1 of ${exercise.technique.length} rules break.`,
      );
    }

    panel.dispose();
  });

  it('keeps the existing human-readable rule descriptions', () => {
    expect(describeTechniqueRule({
      kind: 'stationary',
      tolerance: 0.012,
    })).toBe('stays within 1.2 cm of its start');
    expect(describeTechniqueRule({
      kind: 'jointAngle',
      bone: 'forearm_l',
      axis: 'x',
      min: 0,
      max: 120,
    })).toBe('forearm_l X between 0° and 120°');
  });
});
