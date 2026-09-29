import { describe, expect, it } from 'vitest';
import { canonicalSkeleton } from '../rig/skeleton';
import { generateClip } from '../animation/generate';
import { bicepCurl } from '../exercises/definitions/bicepCurl';
import { bakeClip } from './clipBuilder';
import { bakeClipData } from './clipData';

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
});
