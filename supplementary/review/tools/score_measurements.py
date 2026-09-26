"""Apply the recorded native numerical acceptance rule to two JSON files."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.native.score import compare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    args = parser.parse_args()
    result = compare(json.loads(args.reference.read_text()), json.loads(args.target.read_text()))
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result["accepted"] is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
