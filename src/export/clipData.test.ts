import { describe, expect, it } from 'vitest';
import { canonicalSkeleton } from '../rig/skeleton';
import { generateClip } from '../animation/generate';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { bakeClipData } from './clipData';
import type { DeformationSampler } from '../character/types';

const mapEntries = <T>(map: ReadonlyMap<string, T>) =>
  [...map.entries()].sort(([a], [b]) => a.localeCompare(b));

describe('first-party baked clip data', () => {
  it('samples deterministic canonical bone and equipment data with valid track shapes', () => {
    const studioClip = generateClip(canonicalSkeleton, bicepCurl);
    const first = bakeClipData(studioClip, canonicalSkeleton, { fps: 20 });
    const second = bakeClipData(studioClip, canonicalSkeleton, { fps: 20 });

    expect(first.fps).toBe(20);
    expect(first.name).toBe(studioClip.name);
    expect(first.duration).toBe(studioClip.duration);
    expect(first.times[0]).toBe(0);
    expect(first.times.at(-1)).toBe(studioClip.duration);
    expect(first.times).toHaveLength(Math.max(2, Math.round(studioClip.duration * 20)) + 1);
    for (let index = 1; index < first.times.length; index += 1) {
      expect(first.times[index]).toBeGreaterThan(first.times[index - 1]);
    }

    expect(first.tracks).toEqual(second.tracks);
    expect(mapEntries(first.equipmentTracks)).toEqual(mapEntries(second.equipmentTracks));

    const names = first.tracks.map((track) => `${track.bone}.${track.property}`);
    expect(names).toContain('forearm_l.quaternion');
    expect(names).toContain('thigh_l.quaternion');
    expect(names).not.toContain('toe_l.quaternion');

    for (const track of first.tracks) {
      const valueSize = track.property === 'quaternion' ? 4 : 3;
      expect(track.values).toHaveLength(track.times.length * valueSize);
      expect(track.times.every(Number.isFinite)).toBe(true);
      expect(track.values.every(Number.isFinite)).toBe(true);
      expect(track.times).toEqual(Array.from(new Float32Array(track.times)));
      expect(track.values).toEqual(Array.from(new Float32Array(track.values)));
    }

    expect([...first.equipmentTracks.keys()].sort())
      .toEqual(studioClip.equipment.map((item) => item.id).sort());
    for (const [id, track] of first.equipmentTracks) {
      expect(track.position, `${id}/position`).toHaveLength(first.times.length * 3);
      expect(track.quaternion, `${id}/quaternion`).toHaveLength(first.times.length * 4);
      if (track.scale) expect(track.scale, `${id}/scale`).toHaveLength(first.times.length * 3);
      expect(track.position.every(Number.isFinite)).toBe(true);
      expect(track.quaternion.every(Number.isFinite)).toBe(true);
    }
  });

  it('carries imported-character deformation samples as first-party float data', () => {
    const studioClip = generateClip(canonicalSkeleton, bicepCurl);
    const sampled: number[] = [];
    const sampler: DeformationSampler = {
      sample(pose) {
        sampled.push(pose.rotations.forearm_l?.x ?? 0);
      },
      tracks(times) {
        return [{
          target: 'fixture_body',
          property: 'morphTargetInfluence',
          morphTarget: 'fixture_bend',
          times,
          values: sampled,
        }];
      },
    };

    const baked = bakeClipData(studioClip, canonicalSkeleton, {
      fps: 20,
      boneTracks: false,
      deformation: sampler,
    });

    expect(baked.tracks).toHaveLength(0);
    expect(sampled).toHaveLength(baked.times.length);
    expect(baked.deformationTracks).toHaveLength(1);
    const actual = baked.deformationTracks[0];
    expect(actual).toMatchObject({
      target: 'fixture_body',
      property: 'morphTargetInfluence',
      morphTarget: 'fixture_bend',
    });
    expect(actual.times).toEqual(Array.from(new Float32Array(baked.times)));
    expect(actual.values).toEqual(Array.from(new Float32Array(sampled)));
  });
});
