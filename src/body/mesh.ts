import { BufferAttribute, BufferGeometry, Color, Quaternion, Vector3 } from 'three';
import type { RigBone, Skeleton } from '../rig/skeleton';
import { canonicalSkeleton } from '../rig/skeleton';
import type { BodyBlob, BodyChain, Ring } from './profiles';
import { BODY_BLOBS, BODY_CHAINS, BODY_COLOURS } from './profiles';

/**
 * Build the body as one skinned mesh.
 *
 * Each chain becomes a single tube of elliptical rings running along several
 * bones, built in the rig's rest pose so the bind matrix stays identity. Rings
 * near a joint share their weight between the two bones either side of it, which
 * is what lets an elbow crease and a shoulder round over instead of two rigid
 * parts scissoring past one another.
 *
 * The result is one indexed geometry shared by the viewport and GLB exporter.
 */
export interface BodyGeometry {
  geometry: BufferGeometry;
  vertices: number;
  triangles: number;
}

/** glTF skinning carries four slots; the profile mesh uses at most two. */
const INFLUENCES = 4;

/** One ring, resolved onto the bone it belongs to. */
interface PlacedRing {
  ring: Ring;
  bone: RigBone;
  /** Bone index and weight for this ring's vertices. */
  own: number;
  other: number | null;
  ownWeight: number;
}

/**
 * Surface colour is a vertex attribute rather than a second material, so skin,
 * shorts, eyes and lips all ship in one mesh with one draw call — which is what
 * keeps the character cheap enough for the phone app.
 */
const colourCache = new Map<string, Color>();
const colourOf = (hex: string | undefined): Color => {
  const key = hex ?? BODY_COLOURS.skin;
  let colour = colourCache.get(key);
  if (!colour) {
    colour = new Color(key);
    colourCache.set(key, colour);
  }
  return colour;
};

export function buildBodyGeometry(rig: Skeleton = canonicalSkeleton): BodyGeometry {
  return buildProfileBodyGeometry(rig);
}

/** Build the profile-based surface used by the character and exporter. */
export function buildProfileBodyGeometry(rig: Skeleton = canonicalSkeleton): BodyGeometry {
  const positions: number[] = [];
  const indices: number[] = [];
  const skinIndices: number[] = [];
  const skinWeights: number[] = [];
  const colours: number[] = [];

  const boneIndex = new Map<string, number>();
  rig.bones.forEach((bone, index) => boneIndex.set(bone.name, index));

  const scratch = new Vector3();
  const rotation = new Quaternion();

  function pushVertex(placed: PlacedRing, local: Vector3, colour?: string): number {
    const index = positions.length / 3;
    scratch
      .copy(local)
      .applyQuaternion(rotation.copy(placed.bone.restWorldQuaternion))
      .add(placed.bone.restHead);
    positions.push(scratch.x, scratch.y, scratch.z);

    const tint = colourOf(colour ?? placed.ring.colour);
    colours.push(tint.r, tint.g, tint.b);

    const blended = placed.other !== null && placed.ownWeight < 1;
    const bones = [placed.own, blended ? (placed.other as number) : placed.own, 0, 0];
    const weights = [blended ? placed.ownWeight : 1, blended ? 1 - placed.ownWeight : 0, 0, 0];
    for (let i = 0; i < INFLUENCES; i += 1) {
      skinIndices.push(bones[i]);
      skinWeights.push(weights[i]);
    }
    return index;
  }

  const ringVertex = (placed: PlacedRing, angle: number): Vector3 =>
    new Vector3(
      (placed.ring.ox ?? 0) + placed.ring.rx * Math.cos(angle),
      placed.ring.t * placed.bone.length,
      (placed.ring.oz ?? 0) + placed.ring.rz * Math.sin(angle),
    );

  const ringCentre = (placed: PlacedRing): Vector3 =>
    new Vector3(placed.ring.ox ?? 0, placed.ring.t * placed.bone.length, placed.ring.oz ?? 0);

  for (const chain of BODY_CHAINS) {
    const rings = placeChain(rig, boneIndex, chain);
    if (rings.length < 2) continue;
    const sides = chain.sides ?? 16;

    const ringStart: number[] = [];
    for (const placed of rings) {
      ringStart.push(positions.length / 3);
      for (let side = 0; side < sides; side += 1) {
        pushVertex(placed, ringVertex(placed, (side / sides) * Math.PI * 2));
      }
    }

    for (let r = 0; r < rings.length - 1; r += 1) {
      const a = ringStart[r];
      const b = ringStart[r + 1];
      for (let side = 0; side < sides; side += 1) {
        const next = (side + 1) % sides;
        indices.push(a + side, b + side, b + next);
        indices.push(a + side, b + next, a + next);
      }
    }

    cap(rings[0], ringStart[0], sides, true);
    cap(rings[rings.length - 1], ringStart[rings.length - 1], sides, false);
  }

  /** Close an open end. A domed end is already a point, so nothing is drawn. */
  function cap(placed: PlacedRing, start: number, sides: number, front: boolean) {
    if (Math.max(placed.ring.rx, placed.ring.rz) < 0.0015) return;
    const centre = pushVertex(placed, ringCentre(placed));
    for (let side = 0; side < sides; side += 1) {
      const next = (side + 1) % sides;
      // The start cap faces back down the bone, the end cap faces along it.
      if (front) indices.push(centre, start + side, start + next);
      else indices.push(centre, start + next, start + side);
    }
  }

  for (const blob of BODY_BLOBS) {
    if (!rig.has(blob.bone)) continue;
    addBlob(rig.bone(blob.bone), blob);
  }

  function addBlob(bone: RigBone, blob: BodyBlob) {
    const stacks = Math.max(4, Math.round((blob.detail ?? 8) * 0.75));
    const slices = blob.detail ?? 12;
    const start = positions.length / 3;
    const placed: PlacedRing = {
      ring: { t: 0, rx: 0, rz: 0 },
      bone,
      own: boneIndex.get(bone.name) ?? 0,
      other: null,
      ownWeight: 1,
    };
    for (let stack = 0; stack <= stacks; stack += 1) {
      const phi = (stack / stacks) * Math.PI;
      for (let slice = 0; slice < slices; slice += 1) {
        const theta = (slice / slices) * Math.PI * 2;
        pushVertex(
          placed,
          new Vector3(
            blob.centre[0] + blob.radii[0] * Math.sin(phi) * Math.cos(theta),
            blob.centre[1] + blob.radii[1] * Math.cos(phi),
            blob.centre[2] + blob.radii[2] * Math.sin(phi) * Math.sin(theta),
          ),
          blob.colour,
        );
      }
    }
    for (let stack = 0; stack < stacks; stack += 1) {
      for (let slice = 0; slice < slices; slice += 1) {
        const next = (slice + 1) % slices;
        const a = start + stack * slices + slice;
        const b = start + (stack + 1) * slices + slice;
        const c = start + (stack + 1) * slices + next;
        const d = start + stack * slices + next;
        // Wound so the outside faces out: a sphere wound the other way renders
        // as its own inside, which reads as a dark hole in the skin.
        indices.push(a, c, b);
        indices.push(a, d, c);
      }
    }
  }

  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new BufferAttribute(new Float32Array(positions), 3));
  geometry.setAttribute('skinIndex', new BufferAttribute(new Uint16Array(skinIndices), 4));
  geometry.setAttribute('skinWeight', new BufferAttribute(new Float32Array(skinWeights), 4));
  geometry.setAttribute('color', new BufferAttribute(new Float32Array(colours), 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();

  return { geometry, vertices: positions.length / 3, triangles: indices.length / 3 };
}

/**
 * Resolve a chain into a flat list of rings, each carrying the bone it rides and
 * how much of it belongs to the neighbouring bone.
 *
 * A ring within a blend width of a joint is shared with the bone on the far side
 * of that joint — evenly at the joint itself, entirely to one bone a blend width
 * away. That single rule covers every joint in the body.
 */
function placeChain(
  rig: Skeleton,
  boneIndex: Map<string, number>,
  chain: BodyChain,
): PlacedRing[] {
  const parts = chain.parts.filter((part) => rig.has(part.bone));
  const placed: PlacedRing[] = [];

  parts.forEach((part, partIndex) => {
    const bone = rig.bone(part.bone);
    const own = boneIndex.get(bone.name) ?? 0;
    const previous = partIndex > 0 ? parts[partIndex - 1] : null;
    const next = partIndex < parts.length - 1 ? parts[partIndex + 1] : null;

    // Before the first part, the chain hands over to whatever the bone actually
    // hangs off — the deltoid to the collarbone, the glute to the pelvis.
    const parentName = previous?.bone ?? (bone.parent && bone.parent !== 'root' ? bone.parent : null);
    const parentIndex = parentName ? boneIndex.get(parentName) ?? null : null;
    const headBlend = part.blend ?? 0;
    const tailBlend = next?.blend ?? 0;
    const nextIndex = next ? boneIndex.get(next.bone) ?? null : null;

    for (const entry of ringsWithDomes(chain, part.rings, bone.length, partIndex, parts.length)) {
      const distance = entry.t * bone.length;
      let other: number | null = null;
      let ownWeight = 1;

      if (parentIndex !== null && headBlend > 0 && distance < headBlend) {
        other = parentIndex;
        ownWeight = Math.min(1, Math.max(0, 0.5 + (0.5 * distance) / headBlend));
      } else if (nextIndex !== null && tailBlend > 0 && bone.length - distance < tailBlend) {
        other = nextIndex;
        ownWeight = Math.min(1, Math.max(0, 0.5 + (0.5 * (bone.length - distance)) / tailBlend));
      }

      placed.push({ ring: entry, bone, own, other, ownWeight });
    }
  });

  return placed;
}

/** Add the rings that round off the two ends of a chain. */
function ringsWithDomes(
  chain: BodyChain,
  rings: Ring[],
  boneLength: number,
  partIndex: number,
  partCount: number,
): Ring[] {
  const sorted = [...rings].sort((a, b) => a.t - b.t);
  const steps = 3;
  const length = Math.max(1e-4, boneLength);

  const dome = (source: Ring, height: number, direction: -1 | 1): Ring[] => {
    const radius = (source.rx + source.rz) / 2;
    const added: Ring[] = [];
    for (let step = steps; step >= 1; step -= 1) {
      const angle = (step / steps) * (Math.PI / 2);
      added.push({
        t: source.t + (direction * height * radius * Math.sin(angle)) / length,
        rx: source.rx * Math.cos(angle),
        rz: source.rz * Math.cos(angle),
        ox: source.ox,
        oz: source.oz,
      });
    }
    return added;
  };

  const out: Ring[] = [];
  if (chain.domeStart && partIndex === 0) out.push(...dome(sorted[0], chain.domeStart, -1));
  out.push(...sorted);
  if (chain.domeEnd && partIndex === partCount - 1) {
    out.push(...dome(sorted[sorted.length - 1], chain.domeEnd, 1).reverse());
  }
  return out;
}

/**
 * The character's surface, shared by the viewport and the exporter. Colour comes
 * from the vertex attribute, so the material itself stays white and the skin,
 * shorts and eyes all come out of one draw call.
 */
export const BODY_MATERIAL = {
  color: '#ffffff',
  vertexColors: true,
  roughness: 0.68,
  metalness: 0.02,
} as const;
