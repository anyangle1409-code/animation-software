#!/usr/bin/env python3
"""Audit committed ORIGINAL v1 candidate GLBs without Blender or third-party Python.

This is a structural/provenance-boundary audit for review exports. Passing it
does NOT promote either GLB to production and does not replace deformation,
anatomy, garment or release approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "ORIGINAL_V1_WORK/candidates"
DEFAULT_MANIFEST = CANDIDATES / "CANDIDATE_GLB_EXPORT.json"
DEFAULT_RIG = ROOT / "ORIGINAL_V1_WORK/hgpt_canonical_v4_original.json"

GLB_MAGIC = b"glTF"
JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942

LEGACY_TOKENS = (
    "makehuman",
    "meshy",
    "corner_final",
    "baseline_v",
    "high_detail_mesh_work",
    "v15f",
    "v15_",
    "v14_",
    "v13_",
    "v12_",
    "v11_",
    "v10_",
    "v9_",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def parse_glb(path: Path) -> tuple[dict[str, Any], list[dict[str, int]]]:
    data = path.read_bytes()
    if len(data) < 20:
        raise ValueError("file too short for GLB header")
    magic, version, declared_length = struct.unpack_from("<4sII", data, 0)
    if magic != GLB_MAGIC:
        raise ValueError(f"bad GLB magic {magic!r}")
    if version != 2:
        raise ValueError(f"unsupported GLB version {version}")
    if declared_length != len(data):
        raise ValueError(f"declared GLB length {declared_length} != actual {len(data)}")

    offset = 12
    chunks: list[dict[str, int]] = []
    json_doc: dict[str, Any] | None = None
    chunk_index = 0
    while offset < len(data):
        if offset + 8 > len(data):
            raise ValueError("truncated GLB chunk header")
        length, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        end = offset + length
        if end > len(data):
            raise ValueError("GLB chunk exceeds declared file length")
        payload = data[offset:end]
        chunks.append({"index": chunk_index, "type": chunk_type, "length": length})
        if chunk_index == 0:
            if chunk_type != JSON_CHUNK:
                raise ValueError("first GLB chunk is not JSON")
            try:
                json_doc = json.loads(payload.rstrip(b" \t\r\n\x00").decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError(f"invalid GLB JSON chunk: {exc}") from exc
        elif chunk_type not in (BIN_CHUNK,):
            raise ValueError(f"unexpected GLB chunk type 0x{chunk_type:08x}")
        offset = end
        chunk_index += 1

    if offset != len(data):
        raise ValueError("GLB chunk walk did not end at file length")
    if json_doc is None:
        raise ValueError("missing GLB JSON chunk")
    return json_doc, chunks


def node_parent_map(nodes: list[dict[str, Any]]) -> dict[int, int]:
    parents: dict[int, int] = {}
    for parent_index, node in enumerate(nodes):
        for child in node.get("children", []):
            if child in parents:
                raise ValueError(f"node {child} has multiple parents")
            parents[int(child)] = parent_index
    return parents


def audit_variant(
    variant: str,
    path: Path,
    manifest_entry: dict[str, Any],
    rig: dict[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    if not path.is_file():
        return {"variant": variant, "path": str(path), "pass": False, "errors": ["file missing"], "warnings": []}

    actual_size = path.stat().st_size
    actual_sha = sha256(path)
    if actual_size != int(manifest_entry["bytes"]):
        errors.append(f"size mismatch: manifest {manifest_entry['bytes']} vs actual {actual_size}")
    if actual_sha != str(manifest_entry["sha256"]):
        errors.append(f"SHA-256 mismatch: manifest {manifest_entry['sha256']} vs actual {actual_sha}")

    try:
        gltf, chunks = parse_glb(path)
    except ValueError as exc:
        return {
            "variant": variant,
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "pass": False,
            "errors": errors + [str(exc)],
            "warnings": warnings,
            "sha256": actual_sha,
            "bytes": actual_size,
        }

    asset = gltf.get("asset", {})
    if asset.get("version") != "2.0":
        errors.append(f"glTF asset version must be 2.0, got {asset.get('version')!r}")

    buffers = gltf.get("buffers", [])
    if not buffers:
        errors.append("no buffers declared")
    for i, buffer in enumerate(buffers):
        if buffer.get("uri"):
            errors.append(f"buffer {i} has external URI {buffer['uri']!r}")

    images = gltf.get("images", [])
    textures = gltf.get("textures", [])
    if images:
        errors.append(f"candidate must use numeric materials only; found {len(images)} image(s)")
    if textures:
        errors.append(f"candidate must use numeric materials only; found {len(textures)} texture(s)")
    for i, image in enumerate(images):
        if image.get("uri"):
            errors.append(f"image {i} has external URI {image['uri']!r}")

    if gltf.get("animations"):
        errors.append(f"review rest-pose GLB must contain no animations; found {len(gltf['animations'])}")

    serialized = json.dumps(gltf, sort_keys=True).lower()
    legacy_hits = sorted(token for token in LEGACY_TOKENS if token in serialized)
    if legacy_hits:
        errors.append(f"legacy/reference token(s) present in GLB JSON: {legacy_hits}")

    nodes = gltf.get("nodes", [])
    names: dict[str, list[int]] = {}
    for i, node in enumerate(nodes):
        if node.get("name"):
            names.setdefault(str(node["name"]), []).append(i)

    expected_bones = rig.get("bones", [])
    expected_names = [str(b["name"]) for b in expected_bones]
    expected_set = set(expected_names)
    expected_count = int(rig.get("bone_count", len(expected_names)))
    if len(expected_names) != expected_count:
        errors.append(f"rig payload bone list/count disagree: declared {expected_count}, listed {len(expected_names)}")

    for bone_name in expected_names:
        count = len(names.get(bone_name, []))
        if count != 1:
            errors.append(f"bone node {bone_name!r} appears {count} times")

    try:
        parents = node_parent_map(nodes)
    except ValueError as exc:
        errors.append(str(exc))
        parents = {}

    if all(len(names.get(n, [])) == 1 for n in expected_names):
        for bone in expected_bones:
            name = str(bone["name"])
            expected_parent = bone.get("parent")
            idx = names[name][0]
            parent_idx = parents.get(idx)
            actual_parent_name = nodes[parent_idx].get("name") if parent_idx is not None else None
            if expected_parent is None:
                if actual_parent_name in expected_set:
                    errors.append(
                        f"root bone {name!r} unexpectedly has bone parent {actual_parent_name!r}"
                    )
            elif actual_parent_name != expected_parent:
                errors.append(
                    f"bone parent mismatch for {name!r}: expected {expected_parent!r}, got {actual_parent_name!r}"
                )

    skins = gltf.get("skins", [])
    if not skins:
        errors.append("no skins found")
    for i, skin in enumerate(skins):
        joint_names = [nodes[j].get("name") for j in skin.get("joints", []) if 0 <= int(j) < len(nodes)]
        if len(joint_names) != expected_count:
            errors.append(f"skin {i} has {len(joint_names)} joints, expected {expected_count}")
        if set(joint_names) != expected_set:
            missing = sorted(expected_set - set(joint_names))
            extra = sorted(set(joint_names) - expected_set)
            errors.append(f"skin {i} joint set mismatch; missing={missing}, extra={extra}")
        if skin.get("inverseBindMatrices") is None:
            errors.append(f"skin {i} has no inverseBindMatrices accessor")

    mesh_nodes = [
        (i, node)
        for i, node in enumerate(nodes)
        if node.get("mesh") is not None
    ]
    if not mesh_nodes:
        errors.append("no mesh nodes found")

    for i, node in mesh_nodes:
        if node.get("skin") is None:
            errors.append(f"mesh node {node.get('name', i)!r} is not skinned")
        mesh_index = int(node["mesh"])
        if not (0 <= mesh_index < len(gltf.get("meshes", []))):
            errors.append(f"mesh node {node.get('name', i)!r} references invalid mesh {mesh_index}")
            continue
        mesh = gltf["meshes"][mesh_index]
        for p_index, primitive in enumerate(mesh.get("primitives", [])):
            attrs = set(primitive.get("attributes", {}))
            required = {"POSITION", "NORMAL", "JOINTS_0", "WEIGHTS_0"}
            missing_attrs = sorted(required - attrs)
            if missing_attrs:
                errors.append(
                    f"mesh {mesh.get('name', mesh_index)!r} primitive {p_index} missing {missing_attrs}"
                )
            if "TEXCOORD_0" in attrs:
                errors.append(
                    f"mesh {mesh.get('name', mesh_index)!r} unexpectedly contains TEXCOORD_0"
                )

    materials = gltf.get("materials", [])
    material_names = {str(m.get("name")) for m in materials if m.get("name")}
    skin_material = "HGPT_ORIGINAL_V1_SKIN_CANDIDATE"
    shorts_material = "HGPT_ORIGINAL_V1_SHORTS_FABRIC_CANDIDATE"
    body_node = "HGPT_ORIGINAL_V1_BODY_O4_CANDIDATE"
    shorts_node = "HGPT_ORIGINAL_V1_SHORTS_CANDIDATE"

    if skin_material not in material_names:
        errors.append(f"missing expected skin material {skin_material!r}")
    if body_node not in names:
        errors.append(f"missing expected body node {body_node!r}")

    if variant == "bare":
        if shorts_material in material_names:
            errors.append("bare GLB contains shorts material")
        if shorts_node in names:
            errors.append("bare GLB contains shorts node")
        if len(mesh_nodes) != 1:
            errors.append(f"bare GLB expected exactly 1 mesh node, found {len(mesh_nodes)}")
    elif variant == "dressed":
        if shorts_material not in material_names:
            errors.append(f"dressed GLB missing shorts material {shorts_material!r}")
        if shorts_node not in names:
            errors.append(f"dressed GLB missing shorts node {shorts_node!r}")
        if len(mesh_nodes) != 2:
            errors.append(f"dressed GLB expected exactly 2 mesh nodes, found {len(mesh_nodes)}")
    else:
        errors.append(f"unknown manifest variant {variant!r}")

    return {
        "variant": variant,
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "pass": not errors,
        "errors": errors,
        "warnings": warnings,
        "sha256": actual_sha,
        "bytes": actual_size,
        "asset": asset,
        "chunk_count": len(chunks),
        "node_count": len(nodes),
        "mesh_node_count": len(mesh_nodes),
        "skin_count": len(skins),
        "material_names": sorted(material_names),
        "image_count": len(images),
        "texture_count": len(textures),
        "animation_count": len(gltf.get("animations", [])),
        "legacy_token_hits": legacy_hits,
        "expected_bone_count": len(expected_names),
    }


def audit_candidate_set(manifest_path: Path, rig_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    rig = json.loads(rig_path.read_text(encoding="utf-8-sig"))
    errors: list[str] = []

    if manifest.get("stage") != "candidate review export (not production)":
        errors.append(f"unexpected manifest stage {manifest.get('stage')!r}")
    if manifest.get("rig") != "hgpt_canonical_v4_original":
        errors.append(f"unexpected manifest rig {manifest.get('rig')!r}")
    if rig.get("identity") != "hgpt_canonical_v4_original":
        errors.append(f"unexpected rig identity {rig.get('identity')!r}")

    exports = manifest.get("exports", {})
    if set(exports) != {"bare", "dressed"}:
        errors.append(f"manifest exports must be bare+dressed, got {sorted(exports)}")

    variants: list[dict[str, Any]] = []
    for variant in ("bare", "dressed"):
        entry = exports.get(variant)
        if not isinstance(entry, dict):
            variants.append(
                {"variant": variant, "pass": False, "errors": ["missing manifest entry"], "warnings": []}
            )
            continue
        file_name = str(entry.get("file", ""))
        path = manifest_path.parent / file_name
        variants.append(audit_variant(variant, path, entry, rig))

    pass_all = not errors and all(v.get("pass") for v in variants)
    return {
        "schema_version": 1,
        "pass": pass_all,
        "stage": "candidate_structural_audit_not_production_approval",
        "manifest": str(manifest_path.relative_to(ROOT)).replace("\\", "/"),
        "rig_payload": str(rig_path.relative_to(ROOT)).replace("\\", "/"),
        "errors": errors,
        "variants": variants,
        "boundary": (
            "Passing proves structural/self-contained candidate GLB packaging only. "
            "It does not approve anatomy, deformation, garment quality, clean-room history or release promotion."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--rig", type=Path, help="explicit rig payload; otherwise use manifest rig_payload or historical default")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    try:
        rig_path = args.rig
        if rig_path is None:
            probe = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
            declared = probe.get("rig_payload")
            if isinstance(declared, dict) and declared.get("path"):
                rig_path = ROOT / declared["path"]
                if not rig_path.is_file() or sha256(rig_path) != declared.get("sha256"):
                    raise ValueError("manifest-declared rig payload bytes differ")
            else:
                rig_path = DEFAULT_RIG
        result = audit_candidate_set(args.manifest, rig_path)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
