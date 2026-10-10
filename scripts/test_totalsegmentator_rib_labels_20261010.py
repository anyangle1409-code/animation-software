"""No-network adversarial tests for pinned official rib label schema semantics."""
import ast
import base64
import json
import unittest
from unittest.mock import patch

from anatomy_fit.verify_totalsegmentator_rib_labels import (
    extract_contract, validate_source_contract, expected_rib_map,
    source_from_github, git_object_sha, SOURCE_BLOB, SOURCE_URL,
)

def fixture(*, remove_caveat=False, corrupt_legacy=False,
            swapped_v2=False, add_legacy_cartilage=False, malicious_code=False):
    def row_mapping(base, extras=None):
        rows = expected_rib_map(base)
        rows.update(extras or {})
        return rows
    v1 = row_mapping(58, {116: "costal_cartilages"} if add_legacy_cartilage else None)
    if corrupt_legacy:
        v1[58] = "rib_right_1"
    v2 = row_mapping(92, {116:"sternum", 117:"costal_cartilages"})
    if swapped_v2:
        v2[92], v2[104] = v2[104], v2[92]
    part = row_mapping(1, {25:"sternum",26:"costal_cartilages"})
    text = (
        f"class_map = {{'total_v1': {v1!r}, 'total': {v2!r}}}\n"
        f"class_map_5_parts = {{'class_map_part_ribs': {part!r}}}\n"
        "# 11 ribs / cervical Halsrippe / 13. rib variation\n"
    )
    if remove_caveat:
        text = text.replace("Halsrippe", "unknown")
    if malicious_code:
        text += "raise RuntimeError('DO NOT EXECUTE REMOTE CODE')\n"
    return text.encode("utf-8")


class RibVersionLabelTests(unittest.TestCase):
    def test_source_only_contract_with_provisional_flags(self):
        raw = fixture()
        contract = extract_contract(raw, expected_blob=git_object_sha(raw))
        validate_source_contract(contract)
        self.assertEqual(contract["subject_count_in_scope"], 0)
        self.assertFalse(contract["cp1_gate6_approved"])
        self.assertFalse(contract["derived_legacy_v1_2022_dataset_mapping_proven"])
        self.assertFalse(contract["patient_ct_masks_downloaded"])

    def test_versioned_source_rib_ids_exact_and_different(self):
        raw = fixture()
        c = extract_contract(raw, expected_blob=git_object_sha(raw))
        self.assertEqual(c["versioned_maps"]["legacy_v1"]["rib_class_id_by_name"]["rib_left_1"], 58)
        self.assertEqual(c["versioned_maps"]["later_total_v2"]["rib_class_id_by_name"]["rib_left_1"], 92)
        self.assertEqual(c["versioned_maps"]["later_rib_part"]["rib_class_id_by_name"]["rib_left_1"], 1)
        self.assertEqual(c["versioned_maps"]["legacy_v1"]["rib_class_id_by_name"]["rib_right_12"], 81)
        self.assertEqual(c["versioned_maps"]["later_total_v2"]["rib_class_id_by_name"]["rib_right_12"], 115)
        self.assertEqual(c["versioned_maps"]["later_rib_part"]["rib_class_id_by_name"]["rib_right_12"], 24)

    def test_sternum_cartilage_missing_in_v1_but_present_in_later_maps(self):
        raw = fixture()
        c = extract_contract(raw, expected_blob=git_object_sha(raw))
        self.assertIsNone(c["versioned_maps"]["legacy_v1"]["costal_cartilages_class_id"])
        self.assertIsNone(c["versioned_maps"]["legacy_v1"]["sternum_class_id"])
        self.assertEqual(c["versioned_maps"]["later_total_v2"]["costal_cartilages_class_id"],117)
        self.assertEqual(c["versioned_maps"]["later_rib_part"]["costal_cartilages_class_id"],26)

    def test_source_python_is_ast_parsed_never_executed(self):
        raw = fixture(malicious_code=True)
        c = extract_contract(raw, expected_blob=git_object_sha(raw))
        self.assertTrue(c["read_only_upstream_source_parsed_as_AST_no_code_execution"])

    def test_changed_hash_rejected(self):
        raw = fixture()
        with self.assertRaisesRegex(ValueError, "hash"):
            extract_contract(raw, expected_blob="0"*40)

    def test_changed_rib_id_rejected(self):
        raw = fixture(corrupt_legacy=True)
        with self.assertRaisesRegex(ValueError, "Unexpected rib"):
            extract_contract(raw, expected_blob=git_object_sha(raw))

    def test_swapped_bilateral_labels_rejected(self):
        raw = fixture(swapped_v2=True)
        with self.assertRaisesRegex(ValueError, "Unexpected rib"):
            extract_contract(raw, expected_blob=git_object_sha(raw))

    def test_new_cervical_rib_caveat_must_be_present(self):
        raw = fixture(remove_caveat=True)
        with self.assertRaisesRegex(ValueError, "caution"):
            extract_contract(raw, expected_blob=git_object_sha(raw))

    def test_legacy_cartilage_falsification_rejected(self):
        raw = fixture(add_legacy_cartilage=True)
        with self.assertRaisesRegex(ValueError, "sternum"):
            extract_contract(raw, expected_blob=git_object_sha(raw))

    def test_claiming_patient_rib_coverage_rejected(self):
        raw = fixture()
        c = extract_contract(raw, expected_blob=git_object_sha(raw))
        c["individual_subject_rib_presence_proven"] = True
        with self.assertRaisesRegex(ValueError, "anatomical approval"):
            validate_source_contract(c)

    def test_claiming_dataset_label_binding_rejected(self):
        raw = fixture()
        c = extract_contract(raw, expected_blob=git_object_sha(raw))
        c["derived_legacy_v1_2022_dataset_mapping_proven"] = True
        with self.assertRaisesRegex(ValueError, "anatomical approval"):
            validate_source_contract(c)

    def test_claiming_commercial_rights_rejected(self):
        raw = fixture()
        c = extract_contract(raw, expected_blob=git_object_sha(raw))
        c["license_commercial_import_approved"] = True
        with self.assertRaisesRegex(ValueError, "anatomical approval"):
            validate_source_contract(c)

    def test_source_git_sha_algorithm(self):
        self.assertEqual(git_object_sha(b"test content"), "08cf6101416f0ce0dda3c80e627f333854c4085c")

    def test_remote_blob_getter_uses_pinned_endpoint(self):
        raw = b"sample payload"
        payload = {"sha":SOURCE_BLOB, "size":len(raw), "encoding":"base64",
                   "content":base64.b64encode(raw).decode()}
        class Response:
            def __enter__(self): return self
            def __exit__(self, *_): return None
            def geturl(self): return SOURCE_URL
            def read(self, n): return json.dumps(payload).encode()
        with patch("anatomy_fit.verify_totalsegmentator_rib_labels.urllib.request.urlopen",
                   return_value=Response()) as fetch:
            with self.assertRaisesRegex(ValueError, "blob SHA"):
                source_from_github()
            self.assertTrue(fetch.called)

    def test_reject_remote_redirect_even_with_source_body(self):
        raw=b"sample"
        payload={"sha":SOURCE_BLOB,"size":len(raw),"encoding":"base64",
                 "content":base64.b64encode(raw).decode()}
        class Redirect:
            def __enter__(self): return self
            def __exit__(self,*_): pass
            def geturl(self): return "https://attacker.example/no"
            def read(self,n): return json.dumps(payload).encode()
        with patch("anatomy_fit.verify_totalsegmentator_rib_labels.urllib.request.urlopen",
                   return_value=Redirect()):
            with self.assertRaisesRegex(ValueError, "redirected"):
                source_from_github()

    def test_nonliteral_map_code_refused_without_execution(self):
        src = (
            "class_map = {'total_v1': __import__('os').system('exit 99'), 'total': {}}\n"
            "class_map_5_parts = {'class_map_part_ribs': {}}\n"
        ).encode()
        with self.assertRaisesRegex(ValueError, "Nonliteral"):
            extract_contract(src, expected_blob=git_object_sha(src))


if __name__ == "__main__":
    unittest.main()
