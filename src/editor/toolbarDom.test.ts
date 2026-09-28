import { describe, expect, it } from 'vitest';
import { EXERCISES } from '../exercises/library';
import type { ViewMode } from './storeCore';
import {
  createStudioToolbarDom,
  type ToolbarStorePort,
  type ToolbarStoreState,
} from './toolbarDom';

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
  readonly attributes = new Map<string, string>();
  textContent: string | null = null;
  type = '';
  value = '';
  title = '';
  disabled = false;
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

  replaceChildren(...nodes: FakeElement[]): void {
    this.children.splice(0, this.children.length, ...nodes);
  }

  setAttribute(name: string, value: string): void {
    this.attributes.set(name, value);
  }

  addEventListener(type: string, listener: EventListenerOrEventListenerObject): void {
    const listeners = this.listeners.get(type) ?? new Set<EventListenerOrEventListenerObject>();
    listeners.add(listener);
    this.listeners.set(type, listeners);
  }

  removeEventListener(type: string, listener: EventListenerOrEventListenerObject): void {
    this.listeners.get(type)?.delete(listener);
  }

  dispatch(type: string): void {
    const event = { type } as Event;
    for (const listener of this.listeners.get(type) ?? []) {
      if (typeof listener === 'function') listener(event);
      else listener.handleEvent(event);
    }
  }

  click(): void {
    this.dispatch('click');
  }
}

const fakeDocument = (): Pick<Document, 'createElement'> => ({
  createElement: (() => new FakeElement()) as unknown as Document['createElement'],
});

const fake = (element: Element): FakeElement => element as unknown as FakeElement;

function createToolbarStore() {
  const calls = {
    loadExercise: [] as string[],
    viewMode: [] as ViewMode[],
    backdrop: [] as ToolbarStoreState['backdrop'][],
    camera: [] as ToolbarStoreState['camera'][],
    regenerate: 0,
    undo: 0,
    redo: 0,
  };
  const listeners = new Set<() => void>();
  const first = EXERCISES[0];
  let state: ToolbarStoreState = {
    document: { exercise: { id: first.id, name: first.name } },
    history: { past: [], future: [] },
    viewMode: 'combined',
    backdrop: 'studio',
    camera: 'recommended',
    loadExercise(id) {
      calls.loadExercise.push(id);
    },
    setViewMode(viewMode) {
      calls.viewMode.push(viewMode);
    },
    setBackdrop(backdrop) {
      calls.backdrop.push(backdrop);
    },
    setCamera(camera) {
      calls.camera.push(camera);
    },
    regenerate() {
      calls.regenerate += 1;
    },
    undo() {
      calls.undo += 1;
    },
    redo() {
      calls.redo += 1;
    },
  };
  const store: ToolbarStorePort = {
    getState: () => state,
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
  const setState = (patch: Partial<ToolbarStoreState>) => {
    state = { ...state, ...patch };
    for (const listener of [...listeners]) listener();
  };
  return { store, calls, setState };
}

describe('first-party Studio toolbar DOM', () => {
  it('mirrors the React toolbar labels, options and store state', () => {
    const { store, setState } = createToolbarStore();
    const toolbar = createStudioToolbarDom(fakeDocument(), store);

    expect(toolbar.element.dataset.hgptToolbar).toBe('first-party');
    expect(fake(toolbar.element).classList.contains('toolbar')).toBe(true);
    expect(fake(toolbar.controls.exerciseSelect).children).toHaveLength(EXERCISES.length);
    expect(fake(toolbar.controls.viewModes.combined).classList.contains('is-active')).toBe(true);
    expect(toolbar.controls.backdropSelect.value).toBe('studio');
    expect(toolbar.controls.cameraSelect.value).toBe('recommended');
    expect(toolbar.controls.undo.disabled).toBe(true);
    expect(toolbar.controls.redo.disabled).toBe(true);

    setState({
      document: { exercise: { id: 'candidate_probe', name: 'Candidate Probe' } },
      history: { past: [{}], future: [{}] },
      viewMode: 'anatomy',
      backdrop: 'void',
      camera: 'front',
    });

    const exerciseOptions = fake(toolbar.controls.exerciseSelect).children;
    expect(exerciseOptions).toHaveLength(EXERCISES.length + 1);
    expect(exerciseOptions[0]?.textContent).toBe('Candidate: Candidate Probe');
    expect(toolbar.controls.exerciseSelect.value).toBe('candidate_probe');
    expect(fake(toolbar.controls.viewModes.anatomy).classList.contains('is-active')).toBe(true);
    expect(fake(toolbar.controls.viewModes.combined).classList.contains('is-active')).toBe(false);
    expect(toolbar.controls.backdropSelect.value).toBe('void');
    expect(toolbar.controls.cameraSelect.value).toBe('front');
    expect(toolbar.controls.undo.disabled).toBe(false);
    expect(toolbar.controls.redo.disabled).toBe(false);

    toolbar.dispose();
  });

  it('routes controls through the supplied store and detaches on dispose', () => {
    const { store, calls } = createToolbarStore();
    const toolbar = createStudioToolbarDom(fakeDocument(), store);

    toolbar.controls.exerciseSelect.value = EXERCISES[1].id;
    fake(toolbar.controls.exerciseSelect).dispatch('change');
    fake(toolbar.controls.viewModes.skeleton).click();
    toolbar.controls.backdropSelect.value = 'light';
    fake(toolbar.controls.backdropSelect).dispatch('change');
    toolbar.controls.cameraSelect.value = 'left';
    fake(toolbar.controls.cameraSelect).dispatch('change');
    fake(toolbar.controls.regenerate).click();
    fake(toolbar.controls.undo).click();
    fake(toolbar.controls.redo).click();

    expect(calls.loadExercise).toEqual([EXERCISES[1].id]);
    expect(calls.viewMode).toEqual(['skeleton']);
    expect(calls.backdrop).toEqual(['light']);
    expect(calls.camera).toEqual(['left']);
    expect(calls.regenerate).toBe(1);
    expect(calls.undo).toBe(1);
    expect(calls.redo).toBe(1);

    toolbar.dispose();
    fake(toolbar.controls.regenerate).click();
    fake(toolbar.controls.viewModes.character).click();
    expect(calls.regenerate).toBe(1);
    expect(calls.viewMode).toEqual(['skeleton']);
  });
});
