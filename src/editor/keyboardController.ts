import type { StudioState } from './store';
import { studioStore } from './store';

export type KeyboardStudioState = Pick<
  StudioState,
  'undo' | 'redo' | 'togglePlay' | 'setKeyframe' | 'pause' | 'setTime' | 'time'
> & {
  document: { clip: { fps: number } };
};

export interface StudioKeyboardStore {
  getState(): KeyboardStudioState;
}

export interface StudioKeyboardEvent {
  key: string;
  code: string;
  ctrlKey: boolean;
  metaKey: boolean;
  shiftKey: boolean;
  targetTagName?: string | null;
  preventDefault(): void;
}

/** Apply one framework-neutral Studio keyboard shortcut. */
export function handleStudioKeyboardEvent(
  event: StudioKeyboardEvent,
  store: StudioKeyboardStore = studioStore,
): boolean {
  if (event.targetTagName && /^(INPUT|SELECT|TEXTAREA)$/.test(event.targetTagName)) return false;

  const state = store.getState();
  const meta = event.ctrlKey || event.metaKey;
  const key = event.key.toLowerCase();

  if (meta && key === 'z') {
    event.preventDefault();
    if (event.shiftKey) state.redo();
    else state.undo();
    return true;
  }

  if (meta && key === 'y') {
    event.preventDefault();
    state.redo();
    return true;
  }

  if (event.code === 'Space') {
    event.preventDefault();
    state.togglePlay();
    return true;
  }

  if (key === 'k') {
    state.setKeyframe();
    return true;
  }

  if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
    event.preventDefault();
    const direction = event.key === 'ArrowLeft' ? -1 : 1;
    const frames = event.shiftKey ? 5 : 1;
    state.pause();
    state.setTime(state.time + (direction * frames) / state.document.clip.fps);
    return true;
  }

  return false;
}

/**
 * Temporary browser binding. The shortcut logic itself is UI-framework neutral.
 */
export function bindStudioKeyboard(
  target: Pick<Window, 'addEventListener' | 'removeEventListener'>,
  store: StudioKeyboardStore = studioStore,
): () => void {
  const onKey = (event: KeyboardEvent) => {
    const targetElement = event.target as HTMLElement | null;
    handleStudioKeyboardEvent(
      {
        key: event.key,
        code: event.code,
        ctrlKey: event.ctrlKey,
        metaKey: event.metaKey,
        shiftKey: event.shiftKey,
        targetTagName: targetElement?.tagName ?? null,
        preventDefault: () => event.preventDefault(),
      },
      store,
    );
  };

  target.addEventListener('keydown', onKey);
  return () => target.removeEventListener('keydown', onKey);
}
