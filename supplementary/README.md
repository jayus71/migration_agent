# Anonymous supplementary archive

Upload only `ladim-supplementary.zip`. The adjacent SHA-256 file verifies the ZIP and is not a separate supplementary upload. The `review/` directory contains the maintained review documentation, wrappers, and export-specific tests used to construct the archive; it is not a second upload.

The ZIP contains the LaDiM implementation, evaluation utilities, recorded baseline configurations, and offline tests. Benchmark datasets and both framework bridge implementations are excluded. Author-owned repository names, repository links, personal paths, Git metadata, model responses, and experiment logs are excluded from the submitted archive.

Run `python3 scripts/build_review_supplement.py` from the project root to rebuild. This requires the local frozen implementation sources and experiment archives listed in the builder. The builder itself and its private source map are intentionally outside the submission. After rebuilding, extract the ZIP into a fresh directory, run `tools/verify_package.py` and `tools/check_offline.py`, and refresh the adjacent SHA-256 file.

The internal verification record is `docs/supplementary-review-20260926.md`. It is not included in the ZIP.
