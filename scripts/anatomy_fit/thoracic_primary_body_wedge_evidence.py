#!/usr/bin/env python3
"""Source-only thoracic radiographic vertebral body wedge evidence: NO 3D fit.

Transcribes primary Kunkel et al. J Anat (2011) Table 2 level body heights.
Never infer a wedge angle without matched sagittal AP depths, standing frame
and source-compatible endplate definitions. No geometry or skeleton changes.
"""
import argparse
import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ANATOMY = REPO / "ORIGINAL_V1_WORK" / "anatomy"
LEDGER = ANATOMY / "audit" / "thoracic_primary_body_wedge_kunkel2011_v1.json"
STACK = ANATOMY / "canonical_spine_level_stack_v1.json"
CONSTRAINTS = ANATOMY / "canonical_thoracic_qualitative_constraints_v1.json"
LEVELS = ["C7"] + ["T" + str(n) for n in range(1, 13)]
STATUS = "NONCANONICAL_PRIMARY_SOURCE_LEVEL_MEANS_NO_3D_ANGLE_OR_BODY_PROMOTION"


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def evaluate(ledger, stack, constraints):
    """Verify exact level identities and consistency, report source contrast.

    All values are cohort means from radiographs of detached mixed-sex
    specimen segments, not registered measurements of the HGPT character.
    """
    if not isinstance(ledger, dict) or ledger.get("schema_version") != 1:
        raise ValueError("primary thoracic source ledger/schema missing")
    if (ledger.get("kind") != "PRIMARY_THORACIC_VERTEBRAL_BODY_HEIGHT_WEDGE_EVIDENCE"
            or ledger.get("status") != STATUS):
        raise ValueError("thoracic source identity or noncanonical status changed")
    src = ledger.get("source")
    if not isinstance(src, dict) or (
        src.get("doi") != "10.1111/j.1469-7580.2011.01397.x"
        or src.get("pmcid") != "PMC3171774"
        or src.get("table") != "Table 2"
        or src.get("measurement_method") !=
            "lateral radiographic vertebral body corner heights; not direct anatomical vertebral body caliper"
        or src.get("segments_total") != 72
        or src.get("spines_total") != 30
        or src.get("donors_female") != 15
        or src.get("donors_male") != 15
        or src.get("segments_per_disc_level") != 6
    ):
        raise ValueError("primary publication/method or cohort evidence changed")
    interpretation = ledger.get("interpretation")
    if not isinstance(interpretation, dict) or (
        interpretation.get("anatomical_approval") is not False
        or interpretation.get("canonical_geometry_change_allowed") is not False
    ):
        raise ValueError("radiographic evidence must never approve bone geometry")
    if (not isinstance(interpretation.get("unavailable_from_table"), list)
            or len(interpretation["unavailable_from_table"]) < 4):
        raise ValueError("source limitations removed")
    if (stack.get("status") !=
            "LEVEL_HEIGHT_STACK_NUMERIC_BODY_DISC_EVIDENCE_COMPLETE_3D_ALIGNMENT_NOT_FROZEN"
            or constraints.get("status") !=
            "QUALITATIVE_CONSTRAINTS_ONLY_NO_PER_LEVEL_VALUES"):
        raise ValueError("source spine status changed; requires explicit re-review")
    rows = ledger.get("levels")
    if not isinstance(rows, list) or [row.get("level") for row in rows
                                        if isinstance(row, dict)] != LEVELS:
        raise ValueError("C7–T12 source level order/count or identity changed")
    details = []
    by_level = stack.get("vertebral_bodies_mm", {})
    if not isinstance(by_level, dict):
        raise ValueError("missing preserved canonical source-average ledger")
    for row in rows:
        if set(row) != {"level", "anterior_mean_mm", "anterior_sd_mm",
                        "posterior_mean_mm", "posterior_sd_mm",
                        "published_average_mm"}:
            raise ValueError("source table fields changed or unsourced coordinates added")
        vals = [row[key] for key in (
            "anterior_mean_mm", "anterior_sd_mm", "posterior_mean_mm",
            "posterior_sd_mm", "published_average_mm"
        )]
        if any(type(v) not in (int, float) or not math.isfinite(v) or
               v <= 0 or v > 100 for v in vals):
            raise ValueError("invalid source height or dispersion")
        am, _asd, pm, _psd, mean = vals
        if abs((am + pm) / 2 - mean) > 0.011:
            raise ValueError("published average disagrees with Table 2 anterior/posterior values")
        level = row["level"]
        if level != "C7":
            candidate = by_level.get(level)
            if not isinstance(candidate, dict) or (
                candidate.get("source") != "THORACIC_BODY_DISC_2011" or
                type(candidate.get("candidate")) not in (int, float) or
                abs(candidate["candidate"] - mean) > 0.011
            ):
                raise ValueError("primary Table 2 average conflicts with existing canonical level stack")
            if pm <= am:
                raise ValueError("unexpected direction of primary thoracic body wedge; recheck source")
        details.append({
            "level": level,
            "source_method": "radiographic isolated cadaveric segment",
            "anterior_height_mm": am,
            "posterior_height_mm": pm,
            "posterior_minus_anterior_mm": round(pm - am, 4),
            "posterior_anterior_height_ratio": round(pm / am, 6),
            "angle_deg": None,
            "status": "SOURCE_SHAPE_CONTRAST_ONLY_NOT_3D_ANGLE",
            "replaces_existing_source_height": False,
        })
    return {
        "kind": "READ_ONLY_THORACIC_PRIMARY_BODY_WEDGE_CONTRAST",
        "source_doi": src["doi"],
        "input_levels": len(rows),
        "thoracic_levels": len(rows) - 1,
        "all_T1_T12_posterior_taller": True,
        "matched_existing_12_thoracic_average_heights": True,
        "degrees_computed": 0,
        "body_geometry_changed": False,
        "anatomical_acceptance": False,
        "blocked": [
            "no matched per-level sagittal AP depth -> no angular wedge target",
            "detached mixed-sex cadaver radiographs != 1.82-m standing reference male",
            "no endplate angular frames, 3D facet/rib contacts or osseous surfaces",
            "no uniform distribution of 43.7-degree population-average kyphosis",
        ],
        "measurements": details,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, help="Optional new private JSON destination, outside repo")
    args = p.parse_args()
    report = evaluate(_load(LEDGER), _load(STACK), _load(CONSTRAINTS))
    output = json.dumps(report, indent=2) + "\n"
    if args.out is None:
        print(output, end="")
        return
    target = args.out.expanduser().resolve(strict=False)
    if not target.is_absolute() or target.is_relative_to(REPO.resolve()):
        raise ValueError("diagnostic output must stay outside original Git repository")
    if target.exists() or not target.parent.is_dir():
        raise ValueError("private output folder must exist and target must be new")
    target.write_text(output, encoding="utf-8")
    print("Wrote noncanonical source-only thoracic contrast:", target)


if __name__ == "__main__":
    main()
