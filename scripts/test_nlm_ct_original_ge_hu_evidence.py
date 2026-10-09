"""Original GE CT numeric calibration-metadata inventory, never a clinical HU claim."""
import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'anatomy_fit'))
import nlm_ct_original_ge_hu_evidence as hu
import nlm_ct_scanner_geometry_header as ge

MANIFEST=HERE.parent/'ORIGINAL_V1_WORK/anatomy/audit/nlm_pelvic_ct_full_series_candidate_bundle_20261009.json'


def make_header(row):
    cx,cy,z=row['scanner_centre_RAS_mm']
    x_size,y_size=row['pixel_spacing_mm']
    width,height=row['scanner_grid']
    half_x=x_size*width/2
    half_y=y_size*height/2
    vals={
        'width_pixels':width,'height_pixels':height,
        'pixel_spacing_x_mm':x_size,'pixel_spacing_y_mm':y_size,
        'slice_thickness_mm':row['slice_thickness_mm'],
        'series_nominal_slice_spacing_mm':3.0,
        'image_location_mm':z,'scanner_R_centre_mm':cx,
        'scanner_A_centre_mm':cy,'scanner_S_centre_mm':z,
        'R_TL_mm':cx+half_x,'A_TL_mm':cy+half_y,'S_TL_mm':z,
        'R_TR_mm':cx-half_x,'A_TR_mm':cy+half_y,'S_TR_mm':z,
        'R_BR_mm':cx-half_x,'A_BR_mm':cy-half_y,'S_BR_mm':z,
        'normal_R':0,'normal_A':0,'normal_S':1,
    }
    s='Patient Name..........................: PRIVATE PATIENT NEVER ECHO\n'
    s+='Patient ID............................: IMPORTANT PRIVATE IDENTIFIER\n'
    for key,val in ge.KEYS.items():
        s+=key+'.'*(49-len(key))+': '+str(vals[val])+'\n'
    s+='Hounsfield number offset.............: -1024\n'
    return s.encode('ascii')


def original_case():
    b=json.loads(MANIFEST.read_text())
    out={}
    for g in b['series']:
        for row in g['slices']:
            if row['source_id'] in hu.SELECTED_IDS:
                raw=make_header(row)
                row['source_header_sha256']=hashlib.sha256(raw).hexdigest()
                out[ge.ROOT+row['source_id']+'.txt']=raw
    return b,out


class GEHUCalibrationMetadata(unittest.TestCase):
    def test_context_metadata_is_not_calibrated_HU(self):
        raw=b'Hounsfield number offset.............: -1024\n'
        d=hu.extract_intensity_fields(raw)
        self.assertEqual(d['ge_hounsfield_annotation_offset'],-1024)

    def test_unknown_malicious_patient_field_never_leaks(self):
        raw=(b'Patient Name...................: SECRET ID\n'
             b'Hounsfield number offset......: -1024\n')
        self.assertNotIn('SECRET',json.dumps(hu.extract_intensity_fields(raw)))

    def test_rescale_slope_and_intercept_are_only_context(self):
        d=hu.extract_intensity_fields(
            b'Rescale Slope......: 1\nRescale Intercept......: -1024\n')
        self.assertEqual(d['dicom_rescale_slope_if_original'],1)
        self.assertEqual(d['dicom_rescale_intercept_if_original'],-1024)

    def test_missing_hu_information_is_valid_unknown(self):
        self.assertEqual(hu.extract_intensity_fields(
            b'Patient Name.........: NOBODY\n'),{})

    def test_calibration_numeric_format_must_be_finite(self):
        with self.assertRaisesRegex(ValueError,'not a valid numeric'):
            hu.extract_intensity_fields(b'Rescale Slope......: not-a-number\n')

    def test_source_intensity_field_oversized_header_rejected(self):
        with self.assertRaisesRegex(ValueError,'byte limit'):
            hu.extract_intensity_fields(b'A'*(ge.MAX_TEXT_BYTES+1))

    def test_real_72_bundle_safely_exposes_two_reference_source_rows(self):
        b,fixtures=original_case()
        self.assertEqual(set(fixtures),{ge.ROOT+x+'.txt' for x in hu.SELECTED_IDS})
        self.assertEqual(sum(len(g['slices']) for g in b['series']),72)

    def test_pinned_test_headers_do_not_imply_calibrated_hu(self):
        b,fixtures=original_case()
        result=hu.inspect_pinned_sources(b,lambda url,limit: fixtures[url])
        self.assertEqual(result['source_count'],2)
        self.assertEqual(result['source_rows'][0]['scanner_slice_superior_mm'],-342)
        self.assertEqual(result['source_rows'][1]['scanner_slice_superior_mm'],-408)
        for row in result['source_rows']:
            self.assertTrue(row['technical_header_numeric_fields_only'])
            self.assertFalse(row['GE_annotation_values_validated_as_PNG_HU_intercept'])
            self.assertEqual(row['recognized_calibration_or_offset_context']['ge_hounsfield_annotation_offset'],-1024)
        self.assertFalse(result['source_PNG_stored_scalar_to_HU_slope_and_intercept_verified'])
        self.assertFalse(result['anatomical_bone_threshold_selected'])
        self.assertFalse(result['canonical_promotion_allowed'])
        self.assertNotIn('PRIVATE PATIENT',json.dumps(result))

    def test_forged_header_SHA_cannot_be_substituted(self):
        b,fixtures=original_case()
        k=next(iter(fixtures))
        fixtures[k]+=b'\n'  # physically different original bytes
        with self.assertRaisesRegex(ValueError,'header SHA mismatch'):
            hu.inspect_pinned_sources(b,lambda url,limit: fixtures[url])

    def test_source_geometry_mismatch_rejected_even_for_correct_hash(self):
        b,fixtures=original_case()
        key=ge.ROOT+hu.SELECTED_IDS[0]+'.txt'
        raw=fixtures[key].replace(b'Image location'+b'.'*(49-len('Image location'))+b': -342.0',
                                  b'Image location'+b'.'*(49-len('Image location'))+b': -300.0')
        # Re-pin the altered test header, to prove scanner mismatch fails independently.
        fixtures[key]=raw
        for group in b['series']:
            for row in group['slices']:
                if row['source_id']==hu.SELECTED_IDS[0]:
                    row['source_header_sha256']=hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ValueError,'image-location|scanner superior'):
            hu.inspect_pinned_sources(b,lambda url,limit: fixtures[url])

    def test_inspection_does_not_modify_source_bundle(self):
        b,fixtures=original_case()
        before=json.dumps(b,sort_keys=True)
        hu.inspect_pinned_sources(b,lambda url,limit: fixtures[url])
        self.assertEqual(before,json.dumps(b,sort_keys=True))


if __name__=='__main__':
    unittest.main()
