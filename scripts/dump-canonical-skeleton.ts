import { canonicalSkeleton } from '../src/rig/skeleton';

console.log(JSON.stringify(canonicalSkeleton.bones.map((bone) => ({
  name: bone.name,
  head: bone.definition.head,
  tail: bone.definition.tail,
}))));
