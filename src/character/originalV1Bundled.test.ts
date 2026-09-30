import { afterEach, describe, expect, it, vi } from 'vitest';
import { canonicalSkeleton } from '../rig/skeleton';
import { hgRigifyFixture } from '../test/rigifyGlbFixture';
import {
  ORIGINAL_V1_BUNDLED_PATHS,
  bundledOriginalV1Source,
  loadBundledOriginalV1Bytes,
} from './originalV1Bundled';

const originalFetch = globalThis.fetch;

function response(data: ArrayBuffer, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    arrayBuffer: async () => data.slice(0),
  } as Response;
}

afterEach(() => {
  globalThis.fetch = originalFetch;
  vi.restoreAllMocks();
});

describe('dormant ORIGINAL v1 packaged loader', () => {
  it('pins only the final production paths', () => {
    expect(ORIGINAL_V1_BUNDLED_PATHS).toEqual({
      bare: 'characters/HomeGymPT_Male_ORIGINAL_v1.glb',
      dressed: 'characters/HomeGymPT_Male_ORIGINAL_v1_DRESSED.glb',
    });
    for (const path of Object.values(ORIGINAL_V1_BUNDLED_PATHS)) {
      expect(path).not.toMatch(/^(?:https?:)?\/\//i);
      expect(path).not.toMatch(/^\//);
      expect(path).not.toMatch(/candidate|baseline|corner_final|makehuman|meshy|v(?:9|10|11|12|13|14|15)/i);
    }
  });

  it('fetches only the exact packaged path selected by the variant', async () => {
    const fixture = hgRigifyFixture();
    const fetchMock = vi.fn(async (url: string | URL | Request) => {
      expect(url).toBe(ORIGINAL_V1_BUNDLED_PATHS.bare);
      return response(fixture.data);
    });
    globalThis.fetch = fetchMock as typeof fetch;

    const data = await loadBundledOriginalV1Bytes('bare');

    expect(data.byteLength).toBe(fixture.data.byteLength);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('rejects an unsupported/candidate variant before any fetch can occur', async () => {
    const fetchMock = vi.fn();
    globalThis.fetch = fetchMock as typeof fetch;

    await expect(
      loadBundledOriginalV1Bytes('candidate' as never),
    ).rejects.toThrow(/Unsupported ORIGINAL v1 bundled variant/);

    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('rejects HTTP failures and malformed local bytes', async () => {
    globalThis.fetch = vi.fn(async () => response(new ArrayBuffer(0), 404)) as typeof fetch;
    await expect(loadBundledOriginalV1Bytes('dressed')).rejects.toThrow(/HTTP 404/);

    globalThis.fetch = vi.fn(async () =>
      response(new TextEncoder().encode('not a glb container at all').buffer),
    ) as typeof fetch;
    await expect(loadBundledOriginalV1Bytes('dressed')).rejects.toThrow(/GLB magic/);
  });

  it('preserves authored GLB bytes and weights through the existing preserved source path', async () => {
    const fixture = hgRigifyFixture();
    globalThis.fetch = vi.fn(async () => response(fixture.data)) as typeof fetch;

    const source = bundledOriginalV1Source('bare');
    const character = await source.build(canonicalSkeleton);
    try {
      expect(character.source).toBe('original-v1');
      expect(character.preservedGlb?.byteLength).toBe(fixture.data.byteLength);
      expect(character.meshes.length).toBeGreaterThan(0);
      expect(source.lastReport).not.toBeNull();
      expect(source.lastReport?.vertices).toBeGreaterThan(0);
      expect(source.lastReport?.mapping.missingRequired).toEqual([]);
    } finally {
      character.dispose();
    }
  }, 30_000);
});
