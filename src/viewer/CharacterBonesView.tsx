import { useFrame } from '@react-three/fiber';
import { useMemo, useRef } from 'react';
import { BufferAttribute, BufferGeometry, Vector3 } from 'three';
import type { Bone, Mesh } from 'three';
import type { ThreeEvent } from '@react-three/fiber';
import { useCharacter } from '../editor/characterStore';
import { useAlignment } from '../editor/alignmentStore';

const scratch = new Vector3();

/**
 * The character's own bones, drawn over the body (never hidden by it), so a
 * joint that sits off the surface it should be inside is visible. Tapping a
 * joint selects that bone for alignment.
 */
export function CharacterBonesView() {
  const build = useCharacter((state) => state.active);
  const selected = useAlignment((state) => state.selected);
  const select = useAlignment((state) => state.select);
  const markers = useRef<(Mesh | null)[]>([]);

  const bones = useMemo<Bone[]>(() => build?.bones ?? [], [build]);
  const pairs = useMemo(() => bones.filter((bone) => bone.parent && (bone.parent as Bone).isBone), [bones]);
  const geometry = useMemo(() => {
    const g = new BufferGeometry();
    g.setAttribute('position', new BufferAttribute(new Float32Array(pairs.length * 6), 3));
    return g;
  }, [pairs]);

  useFrame(() => {
    const position = geometry.getAttribute('position') as BufferAttribute;
    pairs.forEach((bone, i) => {
      bone.getWorldPosition(scratch);
      position.setXYZ(i * 2, scratch.x, scratch.y, scratch.z);
      (bone.parent as Bone).getWorldPosition(scratch);
      position.setXYZ(i * 2 + 1, scratch.x, scratch.y, scratch.z);
    });
    position.needsUpdate = true;
    geometry.computeBoundingSphere();
    bones.forEach((bone, i) => {
      const marker = markers.current[i];
      if (marker) bone.getWorldPosition(marker.position);
    });
  });

  if (!build) return null;
  const pick = (name: string) => (event: ThreeEvent<MouseEvent>) => {
    event.stopPropagation();
    select(name);
  };

  return (
    <group renderOrder={10}>
      <lineSegments geometry={geometry} renderOrder={10}>
        <lineBasicMaterial color="#5fd4ff" depthTest={false} transparent opacity={0.9} />
      </lineSegments>
      {bones.map((bone, i) => (
        <mesh
          key={bone.uuid}
          ref={(mesh) => {
            markers.current[i] = mesh;
          }}
          renderOrder={11}
          onClick={pick(bone.name)}
        >
          <sphereGeometry args={[bone.name === selected ? 0.016 : 0.008, 10, 8]} />
          <meshBasicMaterial color={bone.name === selected ? '#ff9a3c' : '#5fd4ff'} depthTest={false} transparent />
        </mesh>
      ))}
    </group>
  );
}
