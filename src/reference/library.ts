import type { ExerciseDefinition } from '../exercises/types';
import { curlReferenceFor } from './specs/curl';
import { overheadPressReferenceFor } from './specs/overheadPress';
import { squatReferenceFor } from './specs/squat';
import { lungeReferenceFor } from './specs/lunge';
import { hingeReferenceFor } from './specs/hinge';
import { rowReferenceFor } from './specs/row';
import { verticalPullReferenceFor } from './specs/verticalPull';
import { horizontalPressReferenceFor } from './specs/horizontalPress';
import { raiseReferenceFor } from './specs/raise';
import type { ReferenceFamilyId, ReferenceSpec } from './types';

export function referenceForFamily(
  family: ReferenceFamilyId,
  exercise: ExerciseDefinition,
): ReferenceSpec {
  switch (family) {
    case 'curl':
      return curlReferenceFor(exercise);
    case 'overhead_press':
      return overheadPressReferenceFor(exercise);
    case 'squat':
      return squatReferenceFor(exercise);
    case 'lunge':
      return lungeReferenceFor(exercise);
    case 'hinge':
      return hingeReferenceFor(exercise);
    case 'row':
      return rowReferenceFor(exercise);
    case 'vertical_pull':
      return verticalPullReferenceFor(exercise);
    case 'horizontal_press':
      return horizontalPressReferenceFor(exercise);
    case 'raise':
      return raiseReferenceFor(exercise);
  }
}
