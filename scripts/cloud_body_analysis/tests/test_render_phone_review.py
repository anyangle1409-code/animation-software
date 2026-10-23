"""Synthetic tests for source-preserving phone review contact sheets."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image

SRC = Path(__file__).resolve().parents[1] / "render_phone_review.py"
SPEC = importlib.util.spec_from_file_location("render_phone_review", SRC)
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)

class TestPhoneReview(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.sources = {}
        for i, model in enumerate(review.MODELS):
            folder = self.root / model / "visual_evidence_new"
            folder.mkdir(parents=True)
            for movement, spec in review.REVIEWS.items():
                for number in spec["samples"]:
                    name = f"{model}__{movement}__sample{number}__overlay__{spec['view']}.png"
                    im = Image.new("RGB", (160, 180), (70 + 40*i, 80, 90))
                    im.save(folder / name, "PNG")
            self.sources[model] = self.root / model
        self.out = self.root / "out"

    def test_all_three_review_sheets_have_complete_sources(self):
        manifest = review.produce(self.sources, self.out)
        self.assertEqual(len(manifest["sheets"]), 3)
        for sheet in manifest["sheets"]:
            self.assertEqual(len(sheet["panels"]), 9)
            self.assertTrue((self.out / sheet["filename"]).exists())
            self.assertTrue(sheet["diagnostic_only"])
            self.assertEqual(sheet["anatomical_approval"], "NOT_GRANTED")
            with Image.open(self.out / sheet["filename"]) as im:
                self.assertEqual(im.format, "JPEG")
                self.assertGreater(im.width, 900)
            self.assertEqual(len(sheet["contact_sheet_sha256"]), 64)
        d = json.loads((self.out / "phone_review_manifest.json").read_text())
        self.assertEqual(d["status"], "READ_ONLY_PHONE_REVIEW_NOT_ANATOMICAL_APPROVAL")

    def test_missing_expected_source_fails_closed(self):
        f = (self.sources["V14"] / "visual_evidence_new" /
             "V14__shoulder_press__sample06__overlay__back.png")
        f.unlink()
        with self.assertRaises(FileNotFoundError):
            review.produce(self.sources, self.out)

    def test_non_png_fails_closed(self):
        f = (self.sources["W8"] / "visual_evidence_new" /
             "W8__shoulder_press__sample00__overlay__back.png")
        f.write_bytes(b"fake image")
        with self.assertRaises(Exception):
            review.produce(self.sources, self.out)

    def test_small_image_fails_closed(self):
        f = (self.sources["R120"] / "visual_evidence_new" /
             "R120__shoulder_press__sample08__overlay__back.png")
        Image.new("RGB", (5, 5)).save(f)
        with self.assertRaisesRegex(ValueError, "too small"):
            review.produce(self.sources, self.out)

    def test_tampered_zip_rejected_before_use(self):
        import zipfile
        path = self.root / "fake.zip"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("some.png", b"")
        with self.assertRaisesRegex(ValueError, "SHA256"):
            review.PinnedEvidence("W8", path)

    def test_original_source_pngs_unchanged(self):
        f = (self.sources["W8"] / "visual_evidence_new" /
             "W8__squat__sample07__overlay__side.png")
        before = f.read_bytes()
        review.produce(self.sources, self.out)
        self.assertEqual(f.read_bytes(), before)

if __name__ == "__main__":
    unittest.main()
