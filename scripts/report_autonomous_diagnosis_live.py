#!/usr/bin/env python3
"""Aggregate independent evaluator versions, retaining failed pilot costs."""
import argparse
from collections import Counter
import json
from pathlib import Path
import aggregate_autonomous_diagnosis as aggregation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    exports = [p.parent.parent for p in (root / "exports").rglob("private/mapping.json")]
    assessment_roots = [p.parent for folder in root.glob("assessments*")
                        for p in folder.rglob("evaluation_manifest.json")]
    # A worker can create its manifest before its bundle; defer that root until
    # a subsequent snapshot rather than misclassifying an in-flight write.
    assessment_roots = [p for p in assessment_roots if list((p / "bundles").glob("*.json"))]
    report = aggregation.aggregate(assessment_roots, exports, root / "code/fixed50-private-diagnosis-rubric-20260917.json")
    aggregation.write_report(report, args.output, exports)
    statuses = Counter()
    for folder in root.glob("assessments*"):
        for path in folder.glob("*/*/cases/*/coverage.json"):
            statuses[json.loads(path.read_text())["status"]] += 1
    print(json.dumps({"roots":len(assessment_roots), "groups":len(report["groups"]),
                      "coverage_statuses_all_versions":statuses, "usage":report["usage"]}))


if __name__ == "__main__":
    main()
