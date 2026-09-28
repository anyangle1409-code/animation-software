import { describe, expect, it, vi } from 'vitest';
import {
  handleStudioKeyboardEvent,
  type KeyboardStudioState,
  type StudioKeyboardEvent,
  type StudioKeyboardStore,
} from './keyboardController';

function fixture() {
  const state: KeyboardStudioState = {
    undo: vi.fn(),
    redo: vi.fn(),
    togglePlay: vi.fn(),
    setKeyframe: vi.fn(),
    pause: vi.fn(),
    setTime: vi.fn(),
    time: 1,
    document: { clip: { fps: 30 } },
  };
  const store: StudioKeyboardStore = { getState: () => state };
  return { state, store };
}

function event(overrides: Partial<StudioKeyboardEvent> = {}): StudioKeyboardEvent {
  return {
    key: '',
    code: '',
    ctrlKey: false,
    metaKey: false,
    shiftKey: false,
    targetTagName: null,
    preventDefault: vi.fn(),
    ...overrides,
  };
}

describe('framework-neutral Studio keyboard controller', () => {
  it('ignores editing fields', () => {
    const { state, store } = fixture();
    const input = event({ key: 'z', ctrlKey: true, targetTagName: 'INPUT' });

    expect(handleStudioKeyboardEvent(input, store)).toBe(false);
    expect(state.undo).not.toHaveBeenCalled();
    expect(input.preventDefault).not.toHaveBeenCalled();
  });

  it('preserves undo/redo shortcuts', () => {
    const { state, store } = fixture();
    const undo = event({ key: 'z', ctrlKey: true });
    const redo = event({ key: 'z', metaKey: true, shiftKey: true });
    const redoY = event({ key: 'y', ctrlKey: true });

    expect(handleStudioKeyboardEvent(undo, store)).toBe(true);
    expect(handleStudioKeyboardEvent(redo, store)).toBe(true);
    expect(handleStudioKeyboardEvent(redoY, store)).toBe(true);
    expect(state.undo).toHaveBeenCalledTimes(1);
    expect(state.redo).toHaveBeenCalledTimes(2);
  });

  it('preserves playback and keyframe shortcuts', () => {
    const { state, store } = fixture();

    expect(handleStudioKeyboardEvent(event({ code: 'Space' }), store)).toBe(true);
    expect(handleStudioKeyboardEvent(event({ key: 'k' }), store)).toBe(true);
    expect(state.togglePlay).toHaveBeenCalledTimes(1);
    expect(state.setKeyframe).toHaveBeenCalledTimes(1);
  });

  it('steps one or five frames and pauses first', () => {
    const { state, store } = fixture();

    handleStudioKeyboardEvent(event({ key: 'ArrowRight' }), store);
    handleStudioKeyboardEvent(event({ key: 'ArrowLeft', shiftKey: true }), store);

    expect(state.pause).toHaveBeenCalledTimes(2);
    expect(state.setTime).toHaveBeenNthCalledWith(1, 1 + 1 / 30);
    expect(state.setTime).toHaveBeenNthCalledWith(2, 1 - 5 / 30);
  });
});
