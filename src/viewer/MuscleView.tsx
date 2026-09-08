import { useFrame } from '@react-three/fiber';
import { useMemo, useRef } from 'react';
import { Mesh } from 'three';
import { MUSCLES, createMuscleTransform, resolveMuscle } from '../muscles/model';
import { ACTIVATION_STYLES, activationMap, activationOf } from '../muscles/activation';
import { MUSCLE_GROUPS } from '../muscles/groups';
import { useStudio } from '../editor/store';
import { useSceneState } from './sceneState';

/**
 * The muscle overlay. Every belly follows its own two attachment points, and is
 * coloured by how hard the selected exercise works it.
 */
export function MuscleView() {
  const scene = useSceneState();
  const involvement = useStudio((state) => state.document.exercise.muscles);
  const activation = useMemo(() => activationMap(involvement), [involvement]);
  const meshes = useRef(new Map<string, Mesh>());
  const transform = useMemo(createMuscleTransform, []);

  useFrame(() => {
    for (const muscle of MUSCLES) {
      const mesh = meshes.current.get(muscle.id);
      if (!mesh) continue;
      resolveMuscle(scene.evaluation, muscle, transform);
      mesh.position.copy(transform.position);
      mesh.quaternion.copy(transform.quaternion);
      mesh.scale.copy(transform.scale);
    }
  });

  return (
    <>
      {MUSCLES.map((muscle) => {
        const level = activationOf(activation, muscle.group);
        const style = ACTIVATION_STYLES[level];
        return (
          <mesh
            key={muscle.id}
            name={MUSCLE_GROUPS[muscle.group].label}
            castShadow
            ref={(mesh) => {
              if (mesh) meshes.current.set(muscle.id, mesh);
              else meshes.current.delete(muscle.id);
            }}
          >
            {/* A unit sphere, scaled per frame into the muscle's own belly. */}
            <sphereGeometry args={[1, 14, 10]} />
            <meshStandardMaterial
              color={style.colour}
              emissive={style.colour}
              emissiveIntensity={style.emissive}
              transparent={style.opacity < 1}
              opacity={style.opacity}
              roughness={0.62}
              metalness={0.03}
            />
          </mesh>
        );
      })}
    </>
  );
}
