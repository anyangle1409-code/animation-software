export interface HgPrimitiveGeometryData {
  positions: number[];
  normals: number[];
  uvs: number[];
  indices: number[];
}

type Point3 = [number, number, number];

const pushVertex = (
  mesh: HgPrimitiveGeometryData,
  point: Point3,
  normal: Point3,
  uv: [number, number],
): number => {
  const index = mesh.positions.length / 3;
  mesh.positions.push(point[0], point[1], point[2]);
  mesh.normals.push(normal[0], normal[1], normal[2]);
  mesh.uvs.push(uv[0], uv[1]);
  return index;
};

const emptyPrimitive = (): HgPrimitiveGeometryData => ({
  positions: [],
  normals: [],
  uvs: [],
  indices: [],
});

const add3 = (a: Point3, b: Point3): Point3 => [
  a[0] + b[0],
  a[1] + b[1],
  a[2] + b[2],
];

const scale3 = (a: Point3, scale: number): Point3 => [
  a[0] * scale,
  a[1] * scale,
  a[2] * scale,
];

export function boxPrimitiveData(
  size: readonly [number, number, number],
): HgPrimitiveGeometryData {
  const mesh = emptyPrimitive();
  const half: Point3 = [size[0] / 2, size[1] / 2, size[2] / 2];

  const face = (center: Point3, u: Point3, v: Point3, normal: Point3) => {
    const start = mesh.positions.length / 3;
    const corners: Point3[] = [
      add3(add3(center, scale3(u, -1)), scale3(v, -1)),
      add3(add3(center, u), scale3(v, -1)),
      add3(add3(center, u), v),
      add3(add3(center, scale3(u, -1)), v),
    ];
    const uvs: [number, number][] = [[0, 0], [1, 0], [1, 1], [0, 1]];
    corners.forEach((corner, index) => pushVertex(mesh, corner, normal, uvs[index]));
    mesh.indices.push(
      start, start + 1, start + 2,
      start, start + 2, start + 3,
    );
  };

  face([half[0], 0, 0], [0, half[1], 0], [0, 0, half[2]], [1, 0, 0]);
  face([-half[0], 0, 0], [0, half[1], 0], [0, 0, -half[2]], [-1, 0, 0]);
  face([0, half[1], 0], [0, 0, half[2]], [half[0], 0, 0], [0, 1, 0]);
  face([0, -half[1], 0], [0, 0, half[2]], [-half[0], 0, 0], [0, -1, 0]);
  face([0, 0, half[2]], [half[0], 0, 0], [0, half[1], 0], [0, 0, 1]);
  face([0, 0, -half[2]], [half[0], 0, 0], [0, -half[1], 0], [0, 0, -1]);
  return mesh;
}

export function cylinderPrimitiveData(
  radiusBottom: number,
  radiusTop: number,
  length: number,
  segments: number,
): HgPrimitiveGeometryData {
  const mesh = emptyPrimitive();
  const radialSegments = Math.max(3, Math.floor(segments));
  const half = length / 2;
  const slope = length === 0 ? 0 : (radiusBottom - radiusTop) / length;
  const normalScale = 1 / Math.hypot(1, slope);

  for (let segment = 0; segment <= radialSegments; segment += 1) {
    const u = segment / radialSegments;
    const angle = u * Math.PI * 2;
    const cosine = Math.cos(angle);
    const sine = Math.sin(angle);
    const normal: Point3 = [
      cosine * normalScale,
      slope * normalScale,
      sine * normalScale,
    ];
    pushVertex(mesh, [radiusBottom * cosine, -half, radiusBottom * sine], normal, [u, 0]);
    pushVertex(mesh, [radiusTop * cosine, half, radiusTop * sine], normal, [u, 1]);
  }

  for (let segment = 0; segment < radialSegments; segment += 1) {
    const bottom = segment * 2;
    const top = bottom + 1;
    const nextBottom = bottom + 2;
    const nextTop = bottom + 3;
    mesh.indices.push(bottom, top, nextBottom, top, nextTop, nextBottom);
  }

  const cap = (y: number, radius: number, normalY: number) => {
    const center = pushVertex(mesh, [0, y, 0], [0, normalY, 0], [0.5, 0.5]);
    const ringStart = mesh.positions.length / 3;
    for (let segment = 0; segment <= radialSegments; segment += 1) {
      const angle = (segment / radialSegments) * Math.PI * 2;
      const cosine = Math.cos(angle);
      const sine = Math.sin(angle);
      pushVertex(
        mesh,
        [radius * cosine, y, radius * sine],
        [0, normalY, 0],
        [0.5 + cosine * 0.5, 0.5 + sine * 0.5],
      );
    }
    for (let segment = 0; segment < radialSegments; segment += 1) {
      const current = ringStart + segment;
      const next = current + 1;
      if (normalY > 0) mesh.indices.push(center, next, current);
      else mesh.indices.push(center, current, next);
    }
  };

  cap(half, radiusTop, 1);
  cap(-half, radiusBottom, -1);
  return mesh;
}

export function spherePrimitiveData(
  radius: number,
  widthSegments = 16,
  heightSegments = 12,
): HgPrimitiveGeometryData {
  const mesh = emptyPrimitive();
  const width = Math.max(3, Math.floor(widthSegments));
  const height = Math.max(2, Math.floor(heightSegments));

  for (let row = 0; row <= height; row += 1) {
    const v = row / height;
    const theta = v * Math.PI;
    const sinTheta = Math.sin(theta);
    const cosTheta = Math.cos(theta);
    for (let column = 0; column <= width; column += 1) {
      const u = column / width;
      const phi = u * Math.PI * 2;
      const cosine = Math.cos(phi);
      const sine = Math.sin(phi);
      const normal: Point3 = [sinTheta * cosine, cosTheta, sinTheta * sine];
      pushVertex(
        mesh,
        [radius * normal[0], radius * normal[1], radius * normal[2]],
        normal,
        [u, 1 - v],
      );
    }
  }

  const stride = width + 1;
  for (let row = 0; row < height; row += 1) {
    for (let column = 0; column < width; column += 1) {
      const a = row * stride + column;
      const b = (row + 1) * stride + column;
      const c = (row + 1) * stride + column + 1;
      const d = row * stride + column + 1;
      if (row !== 0) mesh.indices.push(a, d, b);
      if (row !== height - 1) mesh.indices.push(d, c, b);
    }
  }
  return mesh;
}

export function torusPrimitiveData(
  radius: number,
  tube: number,
  arc: number,
  radialSegments = 10,
  tubularSegments = 24,
): HgPrimitiveGeometryData {
  const mesh = emptyPrimitive();
  const radial = Math.max(3, Math.floor(radialSegments));
  const tubular = Math.max(3, Math.floor(tubularSegments));

  for (let row = 0; row <= radial; row += 1) {
    const v = (row / radial) * Math.PI * 2;
    const cosV = Math.cos(v);
    const sinV = Math.sin(v);
    for (let column = 0; column <= tubular; column += 1) {
      const u = (column / tubular) * arc;
      const cosU = Math.cos(u);
      const sinU = Math.sin(u);
      const ring = radius + tube * cosV;
      pushVertex(
        mesh,
        [ring * cosU, ring * sinU, tube * sinV],
        [cosV * cosU, cosV * sinU, sinV],
        [column / tubular, row / radial],
      );
    }
  }

  const stride = tubular + 1;
  for (let row = 0; row < radial; row += 1) {
    for (let column = 0; column < tubular; column += 1) {
      const a = row * stride + column;
      const b = (row + 1) * stride + column;
      const c = (row + 1) * stride + column + 1;
      const d = row * stride + column + 1;
      mesh.indices.push(a, d, b, d, c, b);
    }
  }
  return mesh;
}
