#!/usr/bin/env python3
"""Safely inventory original NLM GE CT intensity-calibration header evidence.

Only inspect selected original source headers; never output raw header lines,
person/operator info or source CT pixels. Use an exact source SHA from the
previously pinned 72-slice bundle. Report numeric metadata ONLY when the
field key matches a strict physics-oriented allowlist. A GE "Hounsfield
annotation offset" must not automatically be treated as PNG pixel intercept.

This read-only screen establishes what source metadata is available; it
does NOT itself verify a PNG stored16 -> calibrated HU mapping.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

import nlm_ct_scanner_geometry_header as ge
import nlm_pelvis_region_scout as scout
import pelvic_ct_series_manifest as series

EXACT_FIELDS = {
    'hounsfield number offset': 'ge_hounsfield_annotation_offset',
    'hounsfield offset': 'ge_hounsfield_annotation_offset',
    'rescale intercept': 'dicom_rescale_intercept_if_original',
    'rescale slope': 'dicom_rescale_slope_if_original',
    'ct number offset': 'ct_number_offset_metadata',
    'image pixel scale': 'original_ge_pixel_scale_metadata',
}
SELECTED_IDS = ('cvm1734f','cvm1800f')
VALUE_RE = re.compile(r'^\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\b')
IDENTITY_RE = re.compile(r'^cvm\d{4}f$')


def extract_intensity_fields(original_header):
    if not isinstance(original_header,bytes) or len(original_header)>ge.MAX_TEXT_BYTES:
        raise ValueError('invalid source header format or byte limit')
    fields={}
    for line in original_header.decode('utf-8','replace').splitlines():
        if ':' not in line:
            continue
        name,raw_number=line.split(':',1)
        key=re.sub(r'\.{2,}','',name).strip().lower()
        alias=EXACT_FIELDS.get(key)
        if alias is None:
            continue
        m=VALUE_RE.match(raw_number)
        if m is None:
            raise ValueError('original GE CT calibration field is not a valid numeric scalar')
        value=float(m.group(1))
        if not math.isfinite(value):
            raise ValueError('original GE CT calibration field nonfinite')
        if alias in fields and fields[alias]!=value:
            raise ValueError('inconsistent duplicate original GE intensity field')
        fields[alias]=value
    return fields


def inspect_pinned_sources(bundle,download=None):
    series.validate_series_bundle(bundle)
    if download is None:
        download=scout._safe_download
    sources={r['source_id']:r for group in bundle['series'] for r in group['slices']}
    if set(SELECTED_IDS)-set(sources):
        raise ValueError('calibration source reference absent from immutable 72-slice CT bundle')
    rows=[]
    for sid in SELECTED_IDS:
        if not IDENTITY_RE.fullmatch(sid):
            raise ValueError('unsafe original source header name')
        raw=download(ge.ROOT+sid+'.txt',ge.MAX_TEXT_BYTES)
        sha=hashlib.sha256(raw).hexdigest()
        if sha!=sources[sid]['source_header_sha256']:
            raise ValueError('original NLM GE scanner header SHA mismatch')
        # Validate the complete recognized GE geometric field inventory
        # before accepting any source calibration context.
        safe=ge.scanner_geometry_from_text(raw)
        fields=extract_intensity_fields(raw)
        if abs(safe['image_location_superior_mm']-sources[sid]['scanner_centre_RAS_mm'][2])>1e-4:
            raise ValueError('original scanner superior source position changed')
        rows.append({
            'source_id':sid,
            'source_GE_header_sha256':sha,
            'scanner_slice_superior_mm':safe['image_location_superior_mm'],
            'recognized_calibration_or_offset_context':fields,
            'technical_header_numeric_fields_only':True,
            'raw_header_text_or_patient_identifiers_exported':False,
            'GE_annotation_values_validated_as_PNG_HU_intercept':False,
        })
    return {
        'schema_version':1,
        'kind':'NLM_GE_CT_PIXEL_VALUE_CALIBRATION_SOURCE_CONTEXT',
        'status':'SOURCE_METADATA_ONLY_PNG_TO_HU_REMAINS_UNVERIFIED',
        'original_NLM_source_headers_sha256_verified':True,
        'source_count':len(rows),
        'source_rows':rows,
        'GE_annotation_is_not_PNG_intensity_calibration_evidence':True,
        'source_PNG_stored_scalar_to_HU_slope_and_intercept_verified':False,
        'water_air_phantom_or_matched_original_DICOM_crosscheck_verified':False,
        'anatomical_bone_threshold_selected':False,
        'skeleton_or_skin_changed':False,
        'canonical_promotion_allowed':False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-bundle',type=Path,required=True)
    p.add_argument('--live-original-source',action='store_true')
    args=p.parse_args()
    if not args.live_original_source:
        p.error('explicit --live-original-source required')
    source=json.loads(args.source_bundle.read_text(encoding='utf-8'))
    result=inspect_pinned_sources(source)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
