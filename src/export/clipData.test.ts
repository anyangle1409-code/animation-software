import { describe, expect, it } from 'vitest';
import { canonicalSkeleton } from '../rig/skeleton';
import { generateClip } from '../animation/generate';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { bakeClip } from './test/clipBuilderCompat';
import { bakeClipData } from './clipData';
import type { DeformationSampler } from '../character/types';

describe('first-party baked clip data', () => {
  it('matches the retained Three compatibility clip for canonical bone tracks', () => {
    const studioClip = generateClip(canonicalSkeleton, bicepCurl);
    const firstParty = bakeClipData(studioClip, canonicalSkeleton, { fps: 20 });
    const compatibility = bakeClip(studioClip, canonicalSkeleton, { fps: 20 });

    expect(firstParty.fps).toBe(compatibility.fps);
    expect(firstParty.times).toEqual(compatibility.times);
    expect(firstParty.tracks).toHaveLength(compatibility.clip.tracks.length);

    for (const track of firstParty.tracks) {
      const expected = compatibility.clip.tracks.find(
        (candidate) => candidate.name === `${track.bone}.${track.property}`,
      );
      expect(expected, `${track.bone}.${track.property}`).toBeDefined();
      expect(track.times).toEqual(Array.from(expected!.times));
      const values = Array.from(expected!.values);
      expect(track.values).toHaveLength(values.length);
      track.values.forEach((value, index) => {
        expect(value).toBeCloseTo(values[index], 10);
      });
    }

    for (const [id, track] of firstParty.equipmentTracks) {
      expect(track).toEqual(compatibility.equipmentTracks.get(id));
    }
  });
  it('carries imported-character deformation samples as first-party data', () => {
    const studioClip = generateClip(canonicalSkeleton, bicepCurl);
    const sampler = (): DeformationSampler => {
      const values: number[] = [];
      return {
        sample(pose) {
          values.push(pose.rotations.forearm_l?.x ?? 0);
        },
        tracks(times) {
          return [{
            target: 'fixture_body',
            property: 'morphTargetInfluence',
            morphTarget: 'fixture_bend',
            times,
            values,
          }];
        },
      };
    };

    const firstParty = bakeClipData(studioClip, canonicalSkeleton, {
      fps: 20,
      boneTracks: false,
      deformation: sampler(),
    });
    const compatibility = bakeClip(studioClip, canonicalSkeleton, {
      fps: 20,
      boneTracks: false,
      deformation: sampler(),
    });

    expect(firstParty.tracks).toHaveLength(0);
    expect(firstParty.deformationTracks).toHaveLength(1);
    const actual = firstParty.deformationTracks[0];
    expect(actual).toMatchObject({
      target: 'fixture_body',
      property: 'morphTargetInfluence',
      morphTarget: 'fixture_bend',
    });

    const expected = compatibility.clip.tracks.find(
      (track) => track.name === 'fixture_body.morphTargetInfluences[fixture_bend]',
    );
    expect(expected).toBeDefined();
    expect(actual.times).toEqual(Array.from(expected!.times));
    expect(actual.values).toEqual(Array.from(expected!.values));
  });

});
