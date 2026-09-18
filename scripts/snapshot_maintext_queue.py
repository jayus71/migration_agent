"""Print compact progress without opening large model trajectories."""
import argparse
from collections import Counter
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("root", type=Path)
args = parser.parse_args()
result = {}
for name, planned in (("fixed50_v3", 200), ("natural10_v3", 40), ("signal12_v3", 36)):
    path = args.root / name / "progress.json"
    try:
        rows = json.loads(path.read_text())["completed"]
    except (FileNotFoundError, ValueError):
        rows = []
    result[name] = {"planned": planned, "completed": len(rows),
                    "statuses": dict(Counter(row["status"] for row in rows))}
try:
    result["continuation"] = json.loads((args.root / "continuation.json").read_text())
except (FileNotFoundError, ValueError):
    result["continuation"] = {"stage": "unknown"}
print(json.dumps(result))
