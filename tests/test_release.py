"""Release checks must reject corruption even after a manifest is rehashed."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("verify_release", ROOT / "scripts/verify_release.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="switch-swe-release-test-")
        cls.root = Path(cls.tmp.name)
        shutil.copytree(ROOT / "data", cls.root / "data")
        shutil.copyfile(ROOT / "release_manifest.json", cls.root / "release_manifest.json")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def mutate(self, name, update, *, rehash=True):
        path = self.root / name
        original = path.read_bytes()
        manifest_path = self.root / "release_manifest.json"
        manifest_raw = manifest_path.read_bytes()
        self.addCleanup(path.write_bytes, original)
        self.addCleanup(manifest_path.write_bytes, manifest_raw)
        path.write_bytes(update(original))
        if rehash:
            manifest = json.loads(manifest_raw)
            manifest["files"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest_path.write_text(json.dumps(manifest))
        return verifier.verify(self.root)

    def test_frozen_release_passes(self):
        report = verifier.verify(self.root)
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["splits"], {"near": 100, "far": 100})

    def test_rehashed_prompt_edit_still_fails_identity(self):
        def edit(raw):
            cases = json.loads(raw)
            cases[0]["turns"][0]["prompt"] += " Modified."
            return json.dumps(cases).encode()
        report = self.mutate("data/cases.json", edit)
        self.assertIn("Frozen case bytes changed", report["errors"])

    def test_rehashed_split_overlap_fails(self):
        far = json.loads((self.root / "data/splits/far.json").read_text())
        def edit(raw):
            near = json.loads(raw)
            near[0] = far[0]
            return json.dumps(near).encode()
        report = self.mutate("data/splits/near.json", edit)
        self.assertIn("near split index differs", report["errors"])

    def test_rehashed_blob_corruption_fails_content_address(self):
        blob = next((self.root / "data/blobs").iterdir())
        report = self.mutate(str(blob.relative_to(self.root)), lambda raw: raw + b"\ncorrupt")
        self.assertIn(f"Blob bytes differ: {blob.name}", report["errors"])


if __name__ == "__main__":
    unittest.main()
