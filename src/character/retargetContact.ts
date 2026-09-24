import { Matrix4, Quaternion, Vector3 } from 'three';
import type { Bone, Object3D, SkinnedMesh } from 'three';
import type { ResolvedContact } from '../constraints/types';
import { IK_CHAINS } from '../ik/chains';
import type { IKChainId } from '../ik/types';
import type { BoneName } from '../rig/boneNames';
import { boneFrame } from '../rig/skeleton';
import type { RetargetBinding } from '../retargeting/retarget';
import type { Side } from './types';

type HandMatrix = (side: Side, target: Matrix4) => Matrix4 | null;

interface ContactRegion {
  mesh: SkinnedMesh;
  vertices: number[];
}

/**
 * Correct locked contacts on a preserved imported skeleton.
 *
 * Absolute retargeting transfers anatomical frames, but a source character's
 * limb lengths need not match the canonical rig. Small source-space IK
 * corrections put its actual distal surface on the floor or equipment without
 * changing the shared exercise pose or replacing the authored skeleton.
 */
export class RetargetContactResolver {
  private readonly regions: Map<IKChainId, ContactRegion[]>;
  private readonly point = new Vector3();
  private readonly implicitFootAnchors = new Map<IKChainId, Vector3>();

  constructor(
    private readonly binding: RetargetBinding,
    private readonly boneByName: Map<BoneName, Bone>,
    private readonly handMatrix: HandMatrix,
  ) {
    this.regions = contactRegions(binding);
  }

  /** Apply distal IK and return any residual equipment error shared by the body. */
  apply(contacts: ResolvedContact[]): Vector3 | null {
    const active = this.withImplicitFeet(contacts);
    for (const contact of active) this.orient(contact);
    for (let pass = 0; pass < 3; pass += 1) {
      for (const contact of active) this.solve(contact);
    }

    const residual = new Vector3();
    let count = 0;
    for (const contact of active) {
      residual.add(this.delta(contact));
      count += 1;
    }
    return count ? residual.multiplyScalar(1 / count) : null;
  }

  private withImplicitFeet(contacts: ResolvedContact[]): ResolvedContact[] {
    const floorHands = contacts.filter((contact) => contact.chain.startsWith('arm')
      && contact.mode === 'world' && contact.target.y <= 0.12);
    if (floorHands.length < 2) {
      this.implicitFootAnchors.clear();
      return contacts;
    }

    const result = [...contacts];
    for (const chain of ['leg_l', 'leg_r'] as const) {
      if (contacts.some((contact) => contact.chain === chain)) continue;
      const end = this.boneByName.get(IK_CHAINS[chain].end);
      if (!end) continue;
      let anchor = this.implicitFootAnchors.get(chain);
      if (!anchor) {
        anchor = end.getWorldPosition(new Vector3());
        this.implicitFootAnchors.set(chain, anchor);
      }
      result.push({ chain, mode: 'floor', target: this.sourceToCanonical(anchor) });
    }
    return result;
  }

  private sourceToCanonical(source: Vector3): { x: number; y: number; z: number } {
    const target = source.clone().applyQuaternion(this.binding.worldAlignment.clone().invert());
    if (this.binding.mirrorSides) target.x *= -1;
    return { x: target.x, y: target.y, z: target.z };
  }

  private orient(contact: ResolvedContact): void {
    if (!contact.aim || !contact.chain.startsWith('arm')) return;
    const side: Side = contact.chain.endsWith('_l') ? 'l' : 'r';
    const hand = this.boneByName.get(`hand_${side}` as BoneName);
    const index = this.boneByName.get(`index_01_${side}` as BoneName);
    const middle = this.boneByName.get(`middle_01_${side}` as BoneName);
    const ring = this.boneByName.get(`ring_01_${side}` as BoneName);
    const pinky = this.boneByName.get(`pinky_01_${side}` as BoneName);
    if (!hand || !index || !middle || !ring || !pinky) return;

    const head = hand.getWorldPosition(new Vector3());
    const tail = new Vector3();
    for (const bone of [index, middle, ring, pinky]) tail.add(bone.getWorldPosition(new Vector3()));
    tail.multiplyScalar(0.25);
    const width = index.getWorldPosition(new Vector3()).sub(pinky.getWorldPosition(new Vector3()));
    if (tail.distanceToSquared(head) < 1e-8 || width.lengthSq() < 1e-8) return;

    const direction = transformedDirection(contact.aim.direction, this.binding);
    const forward = contact.aim.forward
      ? transformedDirection(contact.aim.forward, this.binding)
      : width.clone();
    if (direction.lengthSq() < 1e-8 || forward.lengthSq() < 1e-8) return;
    const currentFrame = boneFrame(head, tail, width);
    const desiredFrame = boneFrame(head, head.clone().add(direction), forward);
    const delta = desiredFrame.multiply(currentFrame.invert());
    setWorldRotation(hand, delta.multiply(hand.getWorldQuaternion(new Quaternion())));
    this.binding.character.root.updateMatrixWorld(true);
  }

  /** Convert a world displacement back into the canonical root-motion frame. */
  rootOffset(world: Vector3): Vector3 {
    const offset = world.clone().applyQuaternion(this.binding.worldAlignment.clone().invert());
    if (this.binding.mirrorSides) offset.x *= -1;
    return offset;
  }

  private solve(contact: ResolvedContact): void {
    const chain = IK_CHAINS[contact.chain];
    const root = this.boneByName.get(chain.root);
    const mid = this.boneByName.get(chain.mid);
    const end = this.boneByName.get(chain.end);
    if (!root || !mid || !end) return;

    const delta = this.delta(contact);
    if (!Number.isFinite(delta.lengthSq()) || delta.lengthSq() < 1e-12) return;
    // A malformed asset must not drag a limb arbitrarily far across the scene.
    if (delta.length() > 0.25) delta.setLength(0.25);
    const target = end.getWorldPosition(new Vector3()).add(delta);
    ccd(this.binding.character.root, root, mid, end, target);
  }

  private delta(contact: ResolvedContact): Vector3 {
    const chain = IK_CHAINS[contact.chain];
    const side: Side = contact.chain.endsWith('_l') ? 'l' : 'r';
    const arm = contact.chain.startsWith('arm');
    const end = this.boneByName.get(chain.end);
    if (!end) return new Vector3();

    const current = arm
      ? this.handMatrix(side, new Matrix4())
      : null;
    const currentPoint = current
      ? this.point.setFromMatrixPosition(current).clone()
      : end.getWorldPosition(new Vector3());
    const target = new Vector3(contact.target.x, contact.target.y, contact.target.z);
    if (this.binding.mirrorSides) target.x *= -1;
    target.applyQuaternion(this.binding.worldAlignment);

    const floor = contact.mode === 'floor'
      || (contact.mode === 'world' && arm && contact.target.y <= 0.12);
    const delta = target.sub(currentPoint);
    if (floor) {
      const minimum = this.minimumY(contact.chain);
      delta.y = Number.isFinite(minimum) ? (contact.lift ?? 0) - minimum : delta.y;
    }
    return delta;
  }

  private minimumY(chain: IKChainId): number {
    let minimum = Infinity;
    for (const { mesh, vertices } of this.regions.get(chain) ?? []) {
      mesh.skeleton.update();
      mesh.updateWorldMatrix(true, false);
      const position = mesh.geometry.getAttribute('position');
      for (const vertex of vertices) {
        this.point.fromBufferAttribute(position, vertex);
        mesh.applyBoneTransform(vertex, this.point).applyMatrix4(mesh.matrixWorld);
        minimum = Math.min(minimum, this.point.y);
      }
    }
    return minimum;
  }
}

function transformedDirection(
  value: { x: number; y: number; z: number },
  binding: RetargetBinding,
): Vector3 {
  const result = new Vector3(value.x, value.y, value.z);
  if (binding.mirrorSides) result.x *= -1;
  return result.applyQuaternion(binding.worldAlignment).normalize();
}

function ccd(rootObject: Object3D, root: Bone, mid: Bone, end: Bone, target: Vector3): void {
  const endWorld = end.getWorldQuaternion(new Quaternion());
  for (let iteration = 0; iteration < 5; iteration += 1) {
    for (const joint of [mid, root]) {
      const jointPosition = joint.getWorldPosition(new Vector3());
      const current = end.getWorldPosition(new Vector3()).sub(jointPosition);
      const desired = target.clone().sub(jointPosition);
      if (current.lengthSq() < 1e-10 || desired.lengthSq() < 1e-10) continue;
      const delta = new Quaternion().setFromUnitVectors(current.normalize(), desired.normalize());
      const world = joint.getWorldQuaternion(new Quaternion());
      setWorldRotation(joint, delta.multiply(world));
      rootObject.updateMatrixWorld(true);
    }
  }
  // Contact IK moves the limb, not the authored palm/sole orientation.
  setWorldRotation(end, endWorld);
  rootObject.updateMatrixWorld(true);
}

function setWorldRotation(bone: Bone, world: Quaternion): void {
  const parent = bone.parent?.getWorldQuaternion(new Quaternion()) ?? new Quaternion();
  bone.quaternion.copy(parent.invert().multiply(world));
  bone.updateMatrixWorld(true);
}

function contactRegions(binding: RetargetBinding): Map<IKChainId, ContactRegion[]> {
  const result = new Map<IKChainId, ContactRegion[]>();
  for (const chainId of Object.keys(IK_CHAINS) as IKChainId[]) {
    const side = chainId.endsWith('_l') ? 'l' : 'r';
    const canonical = chainId.startsWith('arm')
      ? handBones(side)
      : ([`foot_${side}`, `toe_${side}`] as BoneName[]);
    const sourceNames = new Set(canonical
      .map((name) => binding.mapping.bones[name])
      .filter((name): name is string => Boolean(name)));
    const regions: ContactRegion[] = [];

    for (const mesh of binding.character.meshes) {
      const indices = mesh.geometry.getAttribute('skinIndex');
      const weights = mesh.geometry.getAttribute('skinWeight');
      if (!indices || !weights) continue;
      const vertices: number[] = [];
      for (let vertex = 0; vertex < indices.count; vertex += 1) {
        let strongest = 0;
        for (let slot = 1; slot < 4; slot += 1) {
          if (weights.getComponent(vertex, slot) > weights.getComponent(vertex, strongest)) strongest = slot;
        }
        const bone = mesh.skeleton.bones[indices.getComponent(vertex, strongest)];
        if (bone && sourceNames.has(bone.name)) vertices.push(vertex);
      }
      if (vertices.length) regions.push({ mesh, vertices });
    }
    result.set(chainId, regions);
  }
  return result;
}

function handBones(side: Side): BoneName[] {
  const names: BoneName[] = [`hand_${side}` as BoneName];
  names.push(...digitBones(side));
  return names;
}

function digitBones(side: Side): BoneName[] {
  const names: BoneName[] = [];
  for (const digit of ['thumb', 'index', 'middle', 'ring', 'pinky'] as const) {
    for (const segment of ['01', '02', '03'] as const) {
      names.push(`${digit}_${segment}_${side}` as BoneName);
    }
  }
  return names;
}
