"""Validate future exercise muscle coverage without creating Blender bindings.

The 60-stem / 120-bilateral-record foundation lives in experimental PR124,
outside this working branch. It must be retrieved from an immutable commit and
verified as a Git blob BEFORE comparing proposed IDs. New entries are planning
names, not approved muscles, origin/insertion geometry, or app highlights.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
from pathlib import Path

EXPECTED_BLOB_SHA1 = "16885571e16ca380da5ad85981570c3625a8d7a3"
SOURCE_COMMIT = "7c820d68de69dcdef7d567e836302123df953446"
STEM = re.compile(r"^[a-z][a-z0-9_]*$")
GROUP_ID = re.compile(r"^hgpt\.musclegroup\.[a-z][a-z0-9_]*$")
DEPTH = frozenset({"superficial", "intermediate", "deep"})
PROPOSAL_FIELDS_NULL = ("binding", "skin_mask", "layer_neighbour_proof")


def verify_source_blob(raw: bytes) -> dict:
    digest = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if digest != EXPECTED_BLOB_SHA1:
        raise ValueError("Pinned PR124 muscle source Git blob hash mismatch")
    return json.loads(raw)


def validate(catalogue: dict, registry: dict) -> dict:
    def require(condition, message):
        if not condition:
            raise ValueError(message)

    require(catalogue.get("schema_version") == 1, "Unknown catalogue schema")
    require(catalogue.get("experimental_only") is True and
            catalogue.get("production_ready") is False and
            catalogue.get("anatomical_accuracy_approved") is False,
            "Incorrect experiment/approval declarations")
    require(catalogue.get("PT_MODEL_VERSION") == registry.get("PT_MODEL_VERSION") == "1.0",
            "Production model version drift")
    require(catalogue.get("existing_source", {}).get("content_blob_sha") == EXPECTED_BLOB_SHA1 and
            catalogue["existing_source"].get("commit") == SOURCE_COMMIT,
            "Wrong pinned registry reference")
    require(catalogue.get("scope", {}).get("claims_complete_human_musculature") is False and
            catalogue["scope"].get("custom_visual_highlights_implemented") is False,
            "Catalogue incorrectly claims completion or a highlighting feature")
    existing = registry.get("muscles")
    require(isinstance(existing, list) and len(existing) == 120,
            "Expected 120 original bilateral seed records")
    old_ids = set()
    old_stems = set()
    for item in existing:
        muscle_id = item.get("id")
        stem = item.get("seed_id")
        side = item.get("side")
        require(isinstance(stem, str) and STEM.fullmatch(stem) is not None and
                side in {"L", "R"} and
                muscle_id == f"hgpt.muscle.{stem}.{side}" and
                muscle_id not in old_ids, f"Malformed/duplicated existing ID {muscle_id}")
        old_ids.add(muscle_id)
        old_stems.add(stem)
        require(item.get("binding") is None, f"Unexpected old native binding {muscle_id}")
        require(item.get("status") == "semantic_seed_only", "Old experimental status changed")
    require(len(old_stems) == 60, "Original seed must contain exactly 60 stems")
    for stem in old_stems:
        require(all(f"hgpt.muscle.{stem}.{side}" in old_ids for side in ("L", "R")),
                f"Unpaired existing stem: {stem}")

    groups = catalogue.get("groups")
    proposed = catalogue.get("proposed_members")
    require(isinstance(groups, list) and len(groups) >= 10 and
            isinstance(proposed, list) and len(proposed) >= 50,
            "Future groups/proposals missing")
    group_ids = set()
    for item in groups:
        gid = item.get("id")
        require(isinstance(gid, str) and GROUP_ID.fullmatch(gid) is not None and
                gid not in group_ids, f"Invalid or duplicate group ID: {gid}")
        group_ids.add(gid)
        require(item.get("status") == "COVERAGE_PLAN_ONLY" and
                item.get("source_url", "").startswith("https://") and
                item.get("label") and item.get("future_exercise_family"),
                f"Unreviewed or uncited group: {gid}")
    new_stems = set()
    regions = collections.Counter()
    group_counts = collections.Counter()
    for item in proposed:
        stem = item.get("proposed_stem")
        require(isinstance(stem, str) and STEM.fullmatch(stem) is not None and
                stem not in old_stems and stem not in new_stems,
                f"Proposed stem collision / invalid stem: {stem}")
        new_stems.add(stem)
        ids = [f"hgpt.muscle.{stem}.{side}" for side in ("L", "R")]
        require(item.get("proposed_ids") == ids and all(x not in old_ids for x in ids),
                f"Proposed bilateral ID collision: {stem}")
        require(item.get("group_id") in group_ids, f"Unknown group for {stem}")
        require(item.get("depth_category_for_research") in DEPTH, f"Unknown depth for {stem}")
        require(item.get("status") == "PROPOSED_SEMANTIC_NAME_ONLY",
                f"Unreviewed proposal misrepresented as accepted: {stem}")
        require(item.get("high_level_function_tag") and
                item.get("source_url", "").startswith("https://"),
                f"Uncited high-level anatomical function: {stem}")
        for name in PROPOSAL_FIELDS_NULL:
            require(item.get(name, "__MISSING__") is None,
                    f"Unreviewed {name} supplied: {stem}")
        for end in ("origin", "insertion"):
            attachment = item.get(end, {})
            require(attachment.get("anatomical_landmark_id", "__MISSING__") is None and
                    attachment.get("bone_local_m", "__MISSING__") is None and
                    attachment.get("status") == "unreviewed",
                    f"Invented or missing attachment information: {stem}/{end}")
        regions[item["region"]] += 1
        group_counts[item["group_id"]] += 1
    for group in groups:
        gid = group["id"]
        actual = sorted(p["proposed_stem"] for p in proposed if p["group_id"] == gid)
        declared = group.get("proposed_stems")
        require(isinstance(declared, list) and len(declared) == len(set(declared)) and
                sorted(declared) == actual and actual,
                f"Group incomplete or duplicates declared: {gid}")
    existing_regions = catalogue.get("existing_groups")
    require(isinstance(existing_regions, list) and len(existing_regions) >= 8,
            "Existing body region family taxonomy missing")
    region_ids = set()
    covered_old = []
    for family in existing_regions:
        gid = family.get("id")
        require(isinstance(gid, str) and GROUP_ID.fullmatch(gid) is not None and
                gid not in group_ids and gid not in region_ids,
                f"Existing region ID invalid/collides: {gid}")
        region_ids.add(gid)
        require(family.get("status") == "FOUNDATION_SEMANTICS_NOT_ANATOMICAL_BINDINGS",
                f"Existing group claims anatomical binding: {gid}")
        require(family.get("semantic_registry_source_sha") == EXPECTED_BLOB_SHA1,
                f"Unpinned existing group {gid}")
        stems = family.get("established_stems")
        require(isinstance(stems, list) and stems and len(stems) == len(set(stems)),
                f"Missing/duplicated existing group members: {gid}")
        require(all(stem in old_stems for stem in stems),
                f"Unknown existing group member: {gid}")
        region = gid.removeprefix("hgpt.musclegroup.existing_")
        expected = sorted(m["seed_id"] for m in existing if m["region"] == region and m["side"] == "L")
        require(sorted(stems) == expected, f"Existing region composition mismatch: {gid}")
        covered_old.extend(stems)
    require(len(covered_old) == len(set(covered_old)) == len(old_stems)
            and set(covered_old) == old_stems,
            "Existing group taxonomy does not cover each original stem exactly once")

    functional_groups = catalogue.get("functional_groups")
    require(isinstance(functional_groups, list) and len(functional_groups) >= 15,
            "Future functional exercise groups missing")
    function_ids = set()
    total_stems = old_stems | new_stems
    for function in functional_groups:
        fid = function.get("id")
        require(isinstance(fid, str) and fid.startswith("hgpt.musclefunction.")
                and STEM.fullmatch(fid.removeprefix("hgpt.musclefunction."))
                and fid not in function_ids, f"Invalid/duplicated functional ID {fid}")
        function_ids.add(fid)
        members = function.get("muscle_stems")
        require(isinstance(members, list) and members and len(members) == len(set(members))
                and all(m in total_stems for m in members),
                f"Functional group references missing or duplicate stem: {fid}")
        require(function.get("status") == "FUTURE_EXERCISE_PLANNING"
                and function.get("activation_is_not_implied") is True
                and function.get("anatomical_attachment_approved") is False,
                f"Functional group falsely claims anatomical/activation proof: {fid}")
    require(catalogue["scope"].get("existing_anatomical_region_groups") == len(existing_regions)
            and catalogue["scope"].get("additional_future_groups") == len(groups)
            and catalogue["scope"].get("cross_region_functional_group_count") == len(function_ids),
            "Anatomical/functional taxonomy summary count mismatch")
    require(catalogue["scope"].get("existing_unique_stems") == len(old_stems) and
            catalogue["scope"].get("existing_bilateral_records") == len(old_ids) and
            catalogue["scope"].get("proposed_additional_unique_stems") == len(new_stems) and
            catalogue["scope"].get("proposed_additional_bilateral_records") == 2 * len(new_stems),
            "Catalogue coverage counts inconsistent")
    return {
        "status": "SEMANTIC_COVERAGE_VALIDATED_NOT_ANATOMICALLY_BOUND",
        "source_commit": SOURCE_COMMIT, "source_blob_sha1": EXPECTED_BLOB_SHA1,
        "original_stems": len(old_stems),
        "original_records": len(old_ids),
        "new_proposed_stems": len(new_stems),
        "new_proposed_bilateral_names": 2 * len(new_stems),
        "total_planned_bilateral_names": len(old_ids) + 2 * len(new_stems),
        "major_future_group_count": len(groups),
        "existing_region_group_count": len(existing_regions),
        "functional_exercise_group_count": len(function_ids),
        "proposed_by_region": dict(sorted(regions.items())),
        "proposed_by_group": dict(sorted(group_counts.items())),
        "explicit_not_approved": ["actual muscle origin/insertion coordinates",
                                  "physical tissue meshes and overlapping geometry",
                                  "anatomical laterality on the runtime rig",
                                  "individual physiological activation",
                                  "mobile highlighting appearance or implementation"],
        "original_registry_unchanged": True,
        "highlight_implementation": "DEFERRED_OWNER_DECISION",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalogue", type=Path, required=True)
    parser.add_argument("--pinned-registry", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    reg = verify_source_blob(args.pinned_registry.read_bytes())
    report = validate(json.loads(args.catalogue.read_text()), reg)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "future_muscle_coverage_audit.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
