import { describe, expect, it } from 'vitest';
import { captureReviewBatch } from './captureController';
import type { ReviewCaptureRequest } from './evidence';

const request = (captureId: string, time: number): ReviewCaptureRequest => ({
  referenceId: 'curl.standing.supinated.v1',
  exerciseId: 'generated_test',
  captureId,
  momentId: captureId.startsWith('peak') ? 'peak' : 'start',
  time,
  normalizedTime: time / 5.5,
  viewId: captureId.split('__')[1] ?? 'front',
  camera: { preset: 'front', target: 'full_body' },
  viewport: {
    width: 960,
    height: 960,
    dpr: 1,
    backdrop: 'review_neutral',
    showGrid: false,
    showGizmos: false,
    showIkHandles: false,
    viewMode: 'character',
  },
});

describe('local review capture controller', () => {
  it('captures requests in order and restores the previous state', async () => {
    const log: string[] = [];
    const requests = [request('start__front', 0), request('peak__front', 2.5)];

    const evidence = await captureReviewBatch(requests, {
      snapshot() {
        log.push('snapshot');
        return { camera: 'free' };
      },
      apply(next) {
        log.push(`apply:${next.captureId}`);
      },
      settle(next) {
        log.push(`settle:${next.captureId}`);
      },
      capturePng(next) {
        log.push(`capture:${next.captureId}`);
        return { bytes: new Uint8Array([1, 2, 3]), width: 960, height: 960 };
      },
      restore(state) {
        log.push(`restore:${state.camera}`);
      },
    });

    expect(evidence.map((item) => item.captureId)).toEqual(['start__front', 'peak__front']);
    expect(evidence.every((item) => item.mimeType === 'image/png')).toBe(true);
    expect(log).toEqual([
      'snapshot',
      'apply:start__front',
      'settle:start__front',
      'capture:start__front',
      'apply:peak__front',
      'settle:peak__front',
      'capture:peak__front',
      'restore:free',
    ]);
  });

  it('restores state even if image capture fails', async () => {
    let restored = false;
    await expect(
      captureReviewBatch([request('start__front', 0)], {
        snapshot: () => ({ ok: true }),
        apply: () => undefined,
        settle: () => undefined,
        capturePng: () => {
          throw new Error('canvas unavailable');
        },
        restore: () => {
          restored = true;
        },
      }),
    ).rejects.toThrow(/canvas unavailable/);
    expect(restored).toBe(true);
  });
});
