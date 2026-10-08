"""Evaluate the Holcombe et al. 2017 adult rib demographic regression model.

This module only predicts the nine published rib shape/orientation parameters.
It deliberately does NOT invent the reference age/weight or reconstruct a
3-D HGPT rib centreline until the logarithmic-spiral coordinate transform and
HGPT thoracic-frame mapping are independently implemented and tested.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "ORIGINAL_V1_WORK/anatomy/rib_demographic_model_holcombe2017_v1.json"


def load_model(path: Path = MODEL_PATH) -> dict:
    return json.loads(path.read_text())


def predict_parameter(model: dict, rib: int, parameter: str, *, age_years: float, sex: int, height_m: float, weight_kg: float) -> float:
    if not 1 <= rib <= 12:
        raise ValueError("rib must be 1..12")
    if sex not in (0, 1):
        raise ValueError("sex must use source coding: 0=male, 1=female")
    if not all(math.isfinite(v) for v in (age_years, height_m, weight_kg)):
        raise ValueError("demographic predictors must be finite")
    if age_years < 18:
        raise ValueError("adult reference model: age_years must be >= 18")
    if height_m <= 0 or weight_kg <= 0:
        raise ValueError("height_m and weight_kg must be positive")
    scales = model["scales"][parameter]
    raw = model["levels"][str(rib)]["coefficients_raw"][parameter]
    if len(raw) != 5 or len(scales) != 5:
        raise ValueError("each parameter requires five coefficients and scales")
    if not all(math.isfinite(float(v)) for v in [*raw, *scales]):
        raise ValueError("coefficients and scales must be finite")
    predictors = [1.0, age_years, float(sex), height_m, weight_kg]
    result = sum(float(c) * float(s) * x for c, s, x in zip(raw, scales, predictors))
    if not math.isfinite(result):
        raise ValueError("nonfinite rib prediction")
    return result


def predict_rib(model: dict, rib: int, *, age_years: float, sex: int, height_m: float, weight_kg: float) -> dict:
    return {
        parameter: predict_parameter(
            model, rib, parameter,
            age_years=age_years, sex=sex, height_m=height_m, weight_kg=weight_kg,
        )
        for parameter in model["scales"]
    }


def predict_all(model: dict, *, age_years: float, sex: int, height_m: float, weight_kg: float) -> dict:
    return {
        str(rib): predict_rib(model, rib, age_years=age_years, sex=sex, height_m=height_m, weight_kg=weight_kg)
        for rib in range(1, 13)
    }


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--age", type=float, required=True)
    ap.add_argument("--sex", type=int, choices=[0, 1], default=0)
    ap.add_argument("--height-m", type=float, required=True)
    ap.add_argument("--weight-kg", type=float, required=True)
    args = ap.parse_args()
    print(json.dumps(
        predict_all(load_model(), age_years=args.age, sex=args.sex, height_m=args.height_m, weight_kg=args.weight_kg),
        indent=2,
    ))
