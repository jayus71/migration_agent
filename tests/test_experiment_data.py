import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fetch_data", ROOT / "scripts/fetch_experiment_data.py")
fetch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch)


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.payload = b"task,score\ntask-a,1\n"
        self.record = {
            "path": "snapshot/results.csv",
            "size": len(self.payload),
            "sha256": hashlib.sha256(self.payload).hexdigest(),
        }
        self.manifest = {"files": [self.record]}

    def archive(self, entries):
        archive = self.root / "test.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            for name, kind in entries:
                info = tarfile.TarInfo(name)
                info.type = kind
                if kind == tarfile.REGTYPE:
                    info.size = len(self.payload)
                    tar.addfile(info, io.BytesIO(self.payload))
                else:
                    info.linkname = "../../outside"
                    tar.addfile(info)
        return archive

    def test_valid_snapshot_and_modified_file_detection(self):
        archive = self.archive([(self.record["path"], tarfile.REGTYPE)])
        target = self.root / "extracted"
        fetch.extract(archive, target, self.manifest)
        fetch.verify(target, self.manifest)
        (target / self.record["path"]).write_bytes(b"x" * len(self.payload))
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            fetch.verify(target, self.manifest)

    def test_rejects_unsafe_or_unexpected_entries(self):
        for name, kind in [
            ("../outside", tarfile.REGTYPE),
            ("/absolute", tarfile.REGTYPE),
            ("snapshot/extra.csv", tarfile.REGTYPE),
            (self.record["path"], tarfile.SYMTYPE),
            (self.record["path"], tarfile.LNKTYPE),
        ]:
            with self.subTest(name=name, kind=kind):
                archive = self.archive([(name, kind)])
                with self.assertRaisesRegex(ValueError, "unexpected archive entry"):
                    fetch.extract(archive, self.root / "extracted", self.manifest)

    def test_rejects_duplicate_and_missing_files(self):
        entry = (self.record["path"], tarfile.REGTYPE)
        archive = self.archive([entry, entry])
        with self.assertRaisesRegex(ValueError, "unexpected archive entry"):
            fetch.extract(archive, self.root / "duplicate", self.manifest)
        archive = self.archive([])
        with self.assertRaisesRegex(ValueError, "missing files"):
            fetch.extract(archive, self.root / "missing", self.manifest)

    def test_rejects_wrong_content(self):
        archive = self.archive([(self.record["path"], tarfile.REGTYPE)])
        self.record["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            fetch.extract(archive, self.root / "extracted", self.manifest)

    def test_committed_inputs_match_source_hashes(self):
        manifest = json.loads((ROOT / "data/selected-manifest.json").read_text())
        records = manifest["selected_files"] + manifest["paper_input_files"]
        for record in records:
            with self.subTest(path=record["destination"]):
                path = ROOT / record["destination"]
                self.assertEqual(path.stat().st_size, record["size"])
                self.assertEqual(fetch.digest(path), record["sha256"])


if __name__ == "__main__":
    unittest.main()
