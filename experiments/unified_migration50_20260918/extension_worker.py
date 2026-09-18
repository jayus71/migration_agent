"""Trusted wrapper for the unchanged cross-language training evaluator."""

import argparse
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    for name in ('repo', 'pairing', 'candidate', 'reference', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--task', required=True)
    parser.add_argument('--seed', type=int, required=True)
    args = parser.parse_args()
    sys.path[:0] = [str(args.pairing), str(args.repo)]
    from verify_candidate import evaluate
    result = evaluate(args.candidate, args.reference, args.output, args.task, args.seed)
    (args.output / 'wrapper_result.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
