import { Matrix4, Vector3 } from 'three';
import type { PoseEvaluation, Skeleton } from '../rig/skeleton';
import { canonicalSkeleton } from '../rig/skeleton';
import type { Ring } from './profiles';
import { BODY_CHAINS } from './profiles';

/**
 * How far a point is from the skin, using the body profiles rather than the
 * built mesh.
 *
 * The profiles are authored in each bone's own frame, so the same test works in
 * any pose: transform the point into the bone's frame, find the cross-section at
 * that height, and measure it against the ellipse. Negative is inside.
 *
 * This is what lets the muscle overlay be checked automatically — a belly that
 * pokes out through the skin is a number, not an opinion.
 */
export interface SkinSample {
  /** Signed distance to the surface in metres; negative inside. */
  depth: number;
  /** Bone whose section the point was measured against. */
  bone: string | null;
}

interface Section {
  bone: string;
  length: number;
  rings: Ring[];
}

let sections: Section[] | null = null;

function buildSections(rig: Skeleton): Section[] {
  const out: Section[] = [];
  for (const chain of BODY_CHAINS) {
    for (const part of chain.parts) {
      if (!rig.has(part.bone)) continue;
      out.push({
        bone: part.bone,
        length: rig.bone(part.bone).length,
        rings: [...part.rings].sort((a, b) => a.t - b.t),
      });
    }
  }
  return out;
}

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

/**
 * The cross-section at `t`, interpolated between the two rings around it. A `t`
 * beyond either end clamps to the end ring, and the overshoot is returned so the
 * caller can add it — which turns the section into a capped tube rather than an
 * infinite one, and means a point beyond a bone's last ring is measured against
 * something real instead of nothing at all.
 */
function sectionAt(section: Section, t: number): { ring: Ring; overshoot: number } {
  const rings = section.rings;
  const first = rings[0];
  const last = rings[rings.length - 1];
  // A bone owns its whole span even where its profile stops short of it: the
  // next bone starts exactly where this one ends, so counting the shortfall as
  // "outside the body" would open a false gap at every joint.
  const low = Math.min(first.t, 0);
  const high = Math.max(last.t, 1);
  if (t <= first.t) return { ring: first, overshoot: Math.max(0, low - t) * section.length };
  if (t >= last.t) return { ring: last, overshoot: Math.max(0, t - high) * section.length };

  for (let index = 0; index < rings.length - 1; index += 1) {
    const a = rings[index];
    const b = rings[index + 1];
    if (t > b.t) continue;
    const span = b.t - a.t;
    const k = span <= 1e-9 ? 0 : (t - a.t) / span;
    return {
      ring: {
        t,
        rx: lerp(a.rx, b.rx, k),
        rz: lerp(a.rz, b.rz, k),
        ox: lerp(a.ox ?? 0, b.ox ?? 0, k),
        oz: lerp(a.oz ?? 0, b.oz ?? 0, k),
      },
      overshoot: 0,
    };
  }
  return { ring: last, overshoot: 0 };
}

/**
 * A set of sections with their world-to-bone matrices already inverted, so a
 * caller that probes the same few bones many times — fitting a muscle belly, for
 * instance — pays for the inversion once instead of once per sample.
 */
export interface SkinProbe {
  sections: { section: Section; inverse: Matrix4 }[];
}

export function skinProbe(
  evaluation: PoseEvaluation,
  bones: ReadonlySet<string>,
  rig: Skeleton = canonicalSkeleton,
  reuse?: SkinProbe,
): SkinProbe {
  if (!sections) sections = buildSections(rig);
  const probe = reuse ?? { sections: [] };
  let index = 0;
  for (const section of sections) {
    if (!bones.has(section.bone)) continue;
    const slot = probe.sections[index];
    if (slot) {
      slot.section = section;
      slot.inverse.copy(evaluation.matrix(section.bone as never)).invert();
    } else {
      probe.sections.push({
        section,
        inverse: new Matrix4().copy(evaluation.matrix(section.bone as never)).invert(),
      });
    }
    index += 1;
  }
  probe.sections.length = index;
  return probe;
}

/** Signed distance from a world point to the sections a probe holds. */
export function probeDepth(probe: SkinProbe, world: Vector3): SkinSample {
  let best: SkinSample = { depth: Number.POSITIVE_INFINITY, bone: null };
  for (const entry of probe.sections) {
    local.copy(world).applyMatrix4(entry.inverse);
    const sample = measureSection(entry.section, local);
    if (sample < best.depth) best = { depth: sample, bone: entry.section.bone };
  }
  return best;
}

function measureSection(section: Section, point: Vector3): number {
  const t = section.length <= 1e-6 ? 0 : point.y / section.length;
  const { ring, overshoot } = sectionAt(section, t);
  const dx = (point.x - (ring.ox ?? 0)) / Math.max(1e-6, ring.rx);
  const dz = (point.z - (ring.oz ?? 0)) / Math.max(1e-6, ring.rz);
  const scale = (ring.rx + ring.rz) / 2;
  const across = (Math.hypot(dx, dz) - 1) * scale;
  // Distance to the capped tube: outside along the bone and outside across it
  // combine, inside is whichever constraint is least slack.
  return overshoot > 0 ? Math.hypot(Math.max(0, across), overshoot) : across;
}

const local = new Vector3();

/**
 * Signed distance from a world point to the character's surface, negative when
 * the point is inside the body. A point inside more than one chain reports the
 * deepest of them, because the body is their union.
 */
export function skinDepth(
  evaluation: PoseEvaluation,
  world: Vector3,
  rig: Skeleton = canonicalSkeleton,
  /** Limit the search to these bones' sections, which is much cheaper. */
  bones?: ReadonlySet<string>,
): SkinSample {
  if (!sections) sections = buildSections(rig);
  let best: SkinSample = { depth: Number.POSITIVE_INFINITY, bone: null };

  for (const section of sections) {
    if (bones && !bones.has(section.bone)) continue;
    evaluation.worldToLocal(section.bone as never, world, local);
    const depth = measureSection(section, local);
    if (depth < best.depth) best = { depth, bone: section.bone };
  }

  return Number.isFinite(best.depth) ? best : { depth: Number.POSITIVE_INFINITY, bone: null };
}

/** True when the point sits inside the character's surface. */
export const insideSkin = (
  evaluation: PoseEvaluation,
  world: Vector3,
  rig: Skeleton = canonicalSkeleton,
): boolean => skinDepth(evaluation, world, rig).depth <= 0;
