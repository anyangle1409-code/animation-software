"""Fixed rest tessellation for read-only measurements; source polygons stay untouched."""
import hashlib
import json


def freeze_evaluated(original_evaluated,native_rest_triangles):
    """Wrap a snapshot reader, freezing native triangle indices on its first rest read.

    Pose samples retain their evaluated coordinates and use the same triangle split.
    Existing triangle meshes pass through in their original order. Any vertex count
    or polygon-index change is an error rather than an implicit correspondence guess.
    """
    frozen=None;original_faces=None;vertex_count=None
    report={}
    def evaluated(body):
        nonlocal frozen,original_faces,vertex_count
        vertices,polygons=original_evaluated(body)
        current=tuple(tuple(face) for face in polygons)
        if frozen is None:
            vertex_count=len(vertices);original_faces=current
            derived=any(len(face)!=3 for face in current)
            faces=native_rest_triangles(body) if derived else current
            if vertex_count<=0 or not faces:raise ValueError('No measurement geometry')
            frozen=[]
            for face in faces:
                face=tuple(face)
                if (len(face)!=3 or len(set(face))!=3 or
                    any(not isinstance(i,int) or isinstance(i,bool) or not 0<=i<vertex_count for i in face)):
                    raise ValueError('Invalid native triangle indices')
                frozen.append(face)
            report.update(source_polygon_count=len(current),measurement_triangle_count=len(frozen),
                          vertices=vertex_count,derived_tessellation=derived,
                          fixed_triangle_indices_sha256=hashlib.sha256(json.dumps(frozen,separators=(',',':')).encode()).hexdigest(),
                          scope='native rest loop-triangle indices frozen for measurement; source mesh never edited')
        if len(vertices)!=vertex_count or current!=original_faces:
            raise ValueError('Evaluated topology changed; correspondence is not stable')
        return vertices,frozen
    return evaluated,report
