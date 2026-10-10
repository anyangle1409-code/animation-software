#!/usr/bin/env python3
"""Fail-closed metadata-only independent anatomical source eligibility audit.

Only reviews manually recorded, cited third-party SOURCE METADATA; does not
download human CT, meshes, software weights, or infer canonical 182cm anatomy.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT / "ORIGINAL_V1_WORK/anatomy/independent_source_rights_cohort_candidates_20261010.json"
REQUIRED_IDS = {
    "bonehub_visible_human_male",
    "totalsegmentator_ct_original",
    "totalsegmentator_ribs_medotter_mirror",
    "totalsegmentator_appendicular_tool",
    "utah_subtalar_arthrodesis_fluoroscopy",
    "ultrabones100k",
    "vsd_lower_extremity_30_subjects",
}
EXPECTED_COHORT_GROUPS = {
    "NLM_VISIBLE_HUMAN_MALE_1994": {"bonehub_visible_human_male"},
    "BASEL_TOTAL_SEGMENTATOR_1204_CT": {
        "totalsegmentator_ct_original",
        "totalsegmentator_ribs_medotter_mirror",
    },
    "VSD_30_CADAVER_SUBJECTS": {"vsd_lower_extremity_30_subjects"},
    "MODEL_NOT_A_COHORT": {"totalsegmentator_appendicular_tool"},
    "UTAH_ANKLE_ARTHRODESIS_CLINICAL": {"utah_subtalar_arthrodesis_fluoroscopy"},
    "ULTRABONES_14_SPECIMENS": {"ultrabones100k"},
}


def validate(data: dict) -> dict:
    if data.get("kind") != "HGPT_EXTERNAL_ANATOMICAL_REFERENCE_RIGHTS_AND_COHORT_GATE":
        raise ValueError("Unexpected evidence manifest")
    if (data.get("commercial_product_release_allowed") is not False or
            data.get("canonical_target_selection_allowed") is not False):
        raise ValueError("No blanket commercial or anatomy approval permitted")
    if data.get("explicit_rulings") != {
        "may_download_raw_subject_imaging_in_this_branch": False,
        "may_import_noncommercial_data_in_app": False,
        "may_adopt_any_population_target": False,
        "may_install_models_as_app_dependencies": False,
        "may_increment_region_readiness": False,
    }:
        raise ValueError("Explicit non-promotion guard changed")
    ids = set()
    urls = set()
    cohorts = defaultdict(set)
    for item in data.get("datasets", []):
        ident = item.get("id")
        if not isinstance(ident, str) or ident in ids:
            raise ValueError("Duplicate or invalid source identifier")
        ids.add(ident)
        url = item.get("source_url")
        if not isinstance(url, str) or not url.startswith("https://") or url in urls:
            raise ValueError("Missing, duplicate or unsafe source URL")
        urls.add(url)
        cohort = item.get("cohort_key")
        if not isinstance(cohort, str) or not re.fullmatch("[A-Z0-9_]+", cohort):
            raise ValueError("Unrecognized or missing donor grouping")
        cohorts[cohort].add(ident)
        for k in ("normal_adult_canonical_targets_approved", "commercial_import_approved",
                  "raw_data_inspected_in_this_review"):
            if item.get(k) is not False:
                raise ValueError("Unsupported claim: " + k)
        status = str(item.get("rights_status"))
        label = str(item.get("license_label"))
        if not status or not label:
            raise ValueError("Licensing must be explicit")
        if "NON_COMMERCIAL" in status or "-NC" in label or "COMMERCIAL_LICENSE_REQUIRED" in status:
            if "commercial" in str(item.get("recommended_use", "")).lower() and "do_not" not in str(item.get("recommended_use")):
                raise ValueError("Restricted source improperly recommended for commercial use")
    if ids != REQUIRED_IDS or dict(cohorts) != EXPECTED_COHORT_GROUPS:
        raise ValueError("Unapproved source IDs or donor deduplication change")
    if len(data.get("cohort_overlap_caveats", [])) < 3:
        raise ValueError("Donor overlap caveats missing")
    for phrase in ("rights_and_attribution", "subject_suitability",
                   "physical_unit_coordinate_registration", "articular_contact", "full_joint_ROM"):
        if phrase not in data.get("evidence_chain_not_complete", []):
            raise ValueError("Missing required anatomical source verification: " + phrase)
    group_size = {key: len(ids) for key, ids in cohorts.items()}
    return {
        "schema_version": 1,
        "kind": "HGPT_NONCANONICAL_REFERENCE_RIGHTS_AUDIT",
        "source_entries": len(ids),
        "independent_nonsoftware_donor_cohorts_at_most": sum(
            key != "MODEL_NOT_A_COHORT" for key in cohorts
        ),
        "one_cohort_not_two": {
            "BASEL_TOTAL_SEGMENTATOR_1204_CT": group_size["BASEL_TOTAL_SEGMENTATOR_1204_CT"],
        },
        "noncommercial_or_model_license_restricted_entries": sorted(
            item["id"] for item in data["datasets"]
            if "-NC" in item["license_label"] or
               "COMMERCIAL_LICENSE_REQUIRED" in item["rights_status"]
        ),
        "source_pixels_or_meshes_downloaded": False,
        "commercial_import_approved": False,
        "canonical_geometry_approved": False,
        "anatomical_readiness_changed": False,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", type=Path, default=DEFAULT)
    args = p.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    print(json.dumps(validate(data), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
