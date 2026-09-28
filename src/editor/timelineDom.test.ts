import { beforeEach, describe, expect, it } from 'vitest';
import { EXERCISES } from '../exercises/library';
import { studioStore } from './storeCore';
import { createStudioTimelineDom } from './timelineDom';

class FakeClassList {
  private values = new Set<string>();
  replace(value: string): void { this.values = new Set(value.split(/\s+/).filter(Boolean)); }
  add(...names: string[]): void { for (const name of names) this.values.add(name); }
  toggle(name: string, force?: boolean): boolean {
    const enabled = force ?? !this.values.has(name);
    if (enabled) this.values.add(name); else this.values.delete(name);
    return enabled;
  }
  contains(name: string): boolean { return this.values.has(name); }
  toString(): string { return [...this.values].join(' '); }
}

class FakeElement {
  readonly classList = new FakeClassList();
  readonly dataset: Record<string, string> = {};
  readonly children: FakeElement[] = [];
  readonly style: Record<string, string> = {};
  readonly attributes = new Map<string, string>();
  textContent: string | null = null;
  type = ''; value = ''; title = ''; disabled = false; checked = false; hidden = false;
  min = ''; max = ''; step = '';
  private readonly listeners = new Map<string, Set<EventListenerOrEventListenerObject>>();
  get className(): string { return this.classList.toString(); }
  set className(value: string) { this.classList.replace(value); }
  append(...nodes: FakeElement[]): void { this.children.push(...nodes); }
  replaceChildren(...nodes: FakeElement[]): void { this.children.splice(0, this.children.length, ...nodes); }
  setAttribute(name: string, value: string): void { this.attributes.set(name, value); }
  addEventListener(type: string, listener: EventListenerOrEventListenerObject): void {
    const listeners = this.listeners.get(type) ?? new Set<EventListenerOrEventListenerObject>();
    listeners.add(listener); this.listeners.set(type, listeners);
  }
  removeEventListener(type: string, listener: EventListenerOrEventListenerObject): void {
    this.listeners.get(type)?.delete(listener);
  }
  getBoundingClientRect(): DOMRect { return { left: 0, width: 100 } as DOMRect; }
  setPointerCapture(): void {}
  dispatch(type: string, patch: Partial<PointerEvent> = {}): void {
    const event = { type, clientX: 0, pointerId: 1, buttons: 0, stopPropagation() {}, ...patch } as PointerEvent;
    for (const listener of this.listeners.get(type) ?? []) {
      if (typeof listener === 'function') listener(event); else listener.handleEvent(event);
    }
  }
  click(): void { this.dispatch('click'); }
}

const fakeDocument = (): Pick<Document, 'createElement'> => ({
  createElement: (() => new FakeElement()) as unknown as Document['createElement'],
});
const fake = (element: Element): FakeElement => element as unknown as FakeElement;

beforeEach(() => {
  const state = studioStore.getState();
  state.loadExercise(EXERCISES[0].id);
  state.pause(); state.setTime(0); state.setLoop(true); state.setSpeed(1); state.setLoopRange(null);
});

describe('first-party Studio Timeline DOM', () => {
  it('mirrors playback state and live indicators without React', () => {
    const timeline = createStudioTimelineDom(fakeDocument(), studioStore);
    const clip = studioStore.getState().document.clip;
    expect(timeline.element.dataset.hgptTimeline).toBe('first-party');
    expect(fake(timeline.element).classList.contains('timeline')).toBe(true);
    expect(timeline.controls.play.textContent).toBe('Play');
    expect(timeline.controls.timeReadout.textContent).toBe(`0.00s / ${clip.duration.toFixed(2)}s`);
    expect(timeline.controls.frameReadout.textContent).toBe(`0f / ${Math.round(clip.duration * clip.fps)}f`);
    expect(timeline.controls.previousFrame.disabled).toBe(true);
    expect(timeline.controls.loop.checked).toBe(true);
    expect(timeline.controls.speed.value).toBe('1');
    expect(timeline.controls.clearRange.disabled).toBe(true);
    expect(fake(timeline.controls.track).children.length).toBeGreaterThan(3);

    studioStore.getState().setTime(clip.duration / 2);
    expect(timeline.controls.playhead.style.left).toBe('50%');
    studioStore.getState().setLoopRange({ start: 0, end: clip.duration / 2 });
    expect(timeline.controls.clearRange.disabled).toBe(false);
    expect(timeline.controls.rangeReadout.textContent).toBe(`0.00–${(clip.duration / 2).toFixed(2)}s`);
    timeline.dispose();
  });

  it('routes playback, range, keyframe and scrub controls through studioStore', () => {
    const timeline = createStudioTimelineDom(fakeDocument(), studioStore);
    const initial = studioStore.getState().document.clip;
    fake(timeline.controls.play).click();
    expect(studioStore.getState().playing).toBe(true);
    fake(timeline.controls.nextFrame).click();
    expect(studioStore.getState().playing).toBe(false);
    expect(studioStore.getState().time).toBeCloseTo(1 / initial.fps, 6);

    timeline.controls.speed.value = '1.5';
    fake(timeline.controls.speed).dispatch('change');
    expect(studioStore.getState().speed).toBe(1.5);
    timeline.controls.loop.checked = false;
    fake(timeline.controls.loop).dispatch('change');
    expect(studioStore.getState().loop).toBe(false);

    studioStore.getState().setTime(initial.duration / 2);
    fake(timeline.controls.setIn).click();
    expect(studioStore.getState().loop).toBe(true);
    expect(studioStore.getState().loopRange?.start).toBeCloseTo(initial.duration / 2, 6);
    fake(timeline.controls.clearRange).click();
    expect(studioStore.getState().loopRange).toBeNull();

    fake(timeline.controls.track).dispatch('pointerdown', { clientX: 75, pointerId: 4, buttons: 1 });
    expect(studioStore.getState().time).toBeCloseTo(initial.duration * 0.75, 6);

    const beforeKeys = studioStore.getState().document.clip.keyframes.length;
    fake(timeline.controls.setKeyframe).click();
    expect(studioStore.getState().document.clip.keyframes.length).toBeGreaterThanOrEqual(beforeKeys);

    timeline.dispose();
    const before = studioStore.getState().playing;
    fake(timeline.controls.play).click();
    expect(studioStore.getState().playing).toBe(before);
  });
});
