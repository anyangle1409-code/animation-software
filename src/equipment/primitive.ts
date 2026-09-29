import type { Part } from './geometry';
import {
  boxPrimitiveData,
  cylinderPrimitiveData,
  spherePrimitiveData,
  torusPrimitiveData,
  type HgPrimitiveGeometryData,
} from '../core/primitiveGeometry';

/** One shared geometry translation from authored equipment parts to project mesh data. */
export function equipmentPartPrimitiveData(part: Part): HgPrimitiveGeometryData {
  switch (part.shape) {
    case 'box':
      return boxPrimitiveData(part.size);
    case 'cylinder':
      return cylinderPrimitiveData(
        part.radius,
        part.radiusTop ?? part.radius,
        part.length,
        part.segments ?? 16,
      );
    case 'sphere':
      return spherePrimitiveData(part.radius);
    case 'torus':
      return torusPrimitiveData(
        part.radius,
        part.tube,
        part.arc ?? Math.PI * 2,
      );
  }
}
