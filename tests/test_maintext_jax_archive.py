import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest


spec = importlib.util.spec_from_file_location("jax_archive", Path(__file__).parents[1] / "scripts/archive_maintext_jax_final.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class JaxArchiveTests(unittest.TestCase):
    def test_every_file_is_verified_and_corruption_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            root = folder / "evidence"
            run = root / "formal_v5"
            analysis = run / "final_analysis"
            (analysis / "final_patch_audit").mkdir(parents=True)
            (run / "manifest.json").write_text(json.dumps({"tasks": [], "methods": []}))
            for name in ("summary.json", "comparison.json", "initial_states.json", "final_patch_audit/audit.json"):
                (analysis / name).write_text("{}")
            archive = folder / "good.tar.gz"
            report = module.create(root, archive)
            self.assertEqual(report["verified_entries"], 5)
            self.assertEqual(module.verify(archive)["sha256"], report["sha256"])
            corrupted = folder / "corrupt.tar.gz"
            with tarfile.open(archive) as source, tarfile.open(corrupted, "w:gz") as destination:
                for member in source.getmembers():
                    if member.isfile():
                        data = source.extractfile(member).read()
                        if member.name.endswith("/summary.json"):
                            data = b"[]"
                        destination.addfile(member, io.BytesIO(data))
                    else:
                        destination.addfile(member)
            with self.assertRaisesRegex(ValueError, "File mismatch"):
                module.verify(corrupted)


if __name__ == "__main__":
    unittest.main()
