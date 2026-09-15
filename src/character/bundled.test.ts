import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  BASELINE_CHARACTER_URL,
  DRESSED_CHARACTER_URL,
  registerBundledCharacters,
} from './bundled';
import { characterSources, defaultCharacterId, unregisterCharacterSource } from './registry';

/**
 * The production character files are not in the repository, so the studio has
 * to behave for someone who clones it without them — and it has to notice them
 * when they are there, through a probe that a static file server will actually
 * answer.
 */

const before = defaultCharacterId();

afterEach(() => {
  unregisterCharacterSource('baseline');
  unregisterCharacterSource('baseline-dressed');
  vi.unstubAllGlobals();
});

const answer = (available: string[]) =>
  vi.fn(async (url: string, init?: RequestInit) => {
    void init;
    return available.includes(url)
      ? { ok: true, status: 206, headers: new Headers({ 'content-type': 'model/gltf-binary' }) }
      : { ok: true, status: 200, headers: new Headers({ 'content-type': 'text/html' }) };
  });

describe('bundled characters', () => {
  it('registers nothing and keeps the built-in default when no asset is there', async () => {
    vi.stubGlobal('fetch', answer([]));
    expect(await registerBundledCharacters()).toEqual([]);
    expect(defaultCharacterId()).toBe(before);
  });

  it('treats a dev server answering with index.html as a missing file', async () => {
    const fetcher = answer([]);
    vi.stubGlobal('fetch', fetcher);
    await registerBundledCharacters();
    // A 200 is not enough; it is the content type that distinguishes a real
    // asset from the single-page fallback.
    expect(fetcher).toHaveBeenCalled();
    expect(characterSources().some((source) => source.id === 'baseline')).toBe(false);
  });

  it('asks for one byte rather than issuing a HEAD, which public assets may refuse', async () => {
    const fetcher = answer([BASELINE_CHARACTER_URL, DRESSED_CHARACTER_URL]);
    vi.stubGlobal('fetch', fetcher);
    await registerBundledCharacters();
    for (const call of fetcher.mock.calls) {
      const init = call[1];
      expect(init?.method ?? 'GET').toBe('GET');
      expect((init?.headers as Record<string, string>)?.Range).toBe('bytes=0-0');
    }
  });

  it('registers both characters and dresses the default when both are there', async () => {
    vi.stubGlobal('fetch', answer([BASELINE_CHARACTER_URL, DRESSED_CHARACTER_URL]));
    expect(await registerBundledCharacters()).toEqual(['baseline', 'baseline-dressed']);
    expect(defaultCharacterId()).toBe('baseline-dressed');
    const ids = characterSources().map((source) => source.id);
    expect(ids).toContain('baseline');
    expect(ids).toContain('baseline-dressed');
  });

  it('falls back to the undressed body when only that is there', async () => {
    vi.stubGlobal('fetch', answer([BASELINE_CHARACTER_URL]));
    expect(await registerBundledCharacters()).toEqual(['baseline']);
    expect(defaultCharacterId()).toBe('baseline');
  });

  it('survives a probe that throws', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new Error('offline');
      }),
    );
    expect(await registerBundledCharacters()).toEqual([]);
  });
});
