import type { EquipmentKind } from '../equipment/types';
import { EQUIPMENT_PARTS, MATERIALS } from '../equipment/geometry';
import type { Part } from '../equipment/geometry';

function PartMesh({ part }: { part: Part }) {
  const material = MATERIALS[part.material];
  const position = part.position ?? [0, 0, 0];
  const rotation = 'rotation' in part ? part.rotation ?? [0, 0, 0] : [0, 0, 0];

  return (
    <mesh position={position} rotation={rotation as [number, number, number]} castShadow>
      {part.shape === 'cylinder' && (
        <cylinderGeometry
          args={[part.radiusTop ?? part.radius, part.radius, part.length, part.segments ?? 16]}
        />
      )}
      {part.shape === 'box' && <boxGeometry args={part.size} />}
      {part.shape === 'sphere' && <sphereGeometry args={[part.radius, 16, 12]} />}
      {part.shape === 'torus' && (
        <torusGeometry args={[part.radius, part.tube, 10, 24, part.arc ?? Math.PI * 2]} />
      )}
      <meshStandardMaterial {...material} />
    </mesh>
  );
}

/** Renders a piece of equipment from the shared geometry data. */
export function EquipmentMesh({ kind }: { kind: EquipmentKind }) {
  return (
    <>
      {EQUIPMENT_PARTS[kind].map((part, index) => (
        <PartMesh key={index} part={part} />
      ))}
    </>
  );
}
