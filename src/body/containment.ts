import { Matrix4, Vector3 } from 'three';
import type { PoseEvaluation, Skeleton } from '../rig/skeleton';
import { canonicalSkeleton } from '../rig/skeleton';
import type { BoneName } from '../rig/boneNames';
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

/**
 * Containment-only coverage across the lateral chest → armpit → deltoid gap.
 *
 * Stage 2 moved the arm chain 33.7 mm outboard. The chest correctly did not
 * follow, and the deltoid/upper-arm sections correctly went with the humerus,
 * which leaves a band between them that no profile section covers. The
 * pectoral and latissimus bellies cross that band: measured on the widened rig
 * they reach 9.86 mm and 19.93 mm outside the surface — in the press and the
 * pull-up respectively — against a 7 mm allowance, where before the widening
 * they sat at 4.43 mm and under 4 mm.
 *
 * These sections exist ONLY here. `BODY_CHAINS` feeds
 * `buildProfileBodyGeometry`, which is a rendered surface, so putting the
 * bridge there would widen the visible chest. This is a proxy correction: it
 * changes where a belly is allowed to be, and nothing about what is drawn or
 * how much mass the character has.
 *
 * Sized from the measured points rather than guessed. Both worst points land
 * near the clavicle's lateral end — the latissimus at t 0.848, x −61.8,
 * z −10.0 mm, the pectoral at t 0.800, x −34.7, z +26.2 mm in clavicle-local
 * millimetres — so the ring is offset to sit over them instead of being
 * enlarged concentrically, which would add volume on the far side for nothing.
 * It spans only the outer half of the clavicle; `sectionAt` caps the tube
 * beyond its end rings, so the medial chest is unaffected.
 */
const bridgeRing = (t: number, rx: number, rz: number, ox: number, oz: number): Ring =>
  ({ t, rx, rz, ox, oz });

const ARMPIT_BRIDGE: { bone: BoneName; rings: Ring[] }[] = (['clavicle_l', 'clavicle_r'] as BoneName[]).map(
  (bone) => {
    // The two clavicle frames are NOT reflections of one another here: applying
    // the same negative ox to both moved the left ring into the armpit and the
    // right one inboard, which fixed one side and left the other untouched.
    // Measured, so the offset is flipped explicitly.
    const sign = bone.endsWith('_l') ? 1 : -1;
    return {
      bone,
      rings: [
        bridgeRing(0.5, 0.03, 0.03, sign * -0.026, 0.004),
        bridgeRing(0.8, 0.05, 0.046, sign * -0.05, 0.006),
        // The far station reaches the deltoid. The latissimus passes behind the
        // shoulder here — its worst point measures 85 mm posterior to the upper
        // arm's axis, at the clavicle's very end — so this ring carries both the
        // outboard offset and the front-to-back depth to meet it.
        bridgeRing(1.0, 0.055, 0.052, sign * -0.06, -0.006),
      ],
    };
  },
);

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
  for (const part of ARMPIT_BRIDGE) {
    if (!rig.has(part.bone)) continue;
    out.push({
      bone: part.bone,
      length: rig.bone(part.bone).length,
      rings: [...part.rings].sort((a, b) => a.t - b.t),
    });
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
