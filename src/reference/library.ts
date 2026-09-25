import type { ExerciseDefinition } from '../exercises/types';
import { curlReferenceFor } from './specs/curl';
import type { ReferenceFamilyId, ReferenceSpec } from './types';

export function referenceForFamily(
  family: ReferenceFamilyId,
  exercise: ExerciseDefinition,
): ReferenceSpec {
  switch (family) {
    case 'curl':
      return curlReferenceFor(exercise);
  }
}
