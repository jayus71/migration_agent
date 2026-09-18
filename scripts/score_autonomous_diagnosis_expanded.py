#!/usr/bin/env python3
"""Evaluator v2: preserve the frozen scoring rules; allow 32768 output tokens."""
import argparse
import hashlib
import json
from pathlib import Path

import score_autonomous_diagnosis as base

BASE_SHA256 = "d8acb0b0b7c8a037d762bc63cf978f4231c0dfc04e11bf1cd5e4bece14817f26"


def run(pack, rubric, config, output, *, execute=False, case_ids=None, transport=None):
    base_path = Path(base.__file__).resolve()
    if base.sha(base_path) != BASE_SHA256:
        raise ValueError("Frozen evaluator driver changed")
    pack, output = Path(pack).resolve(), Path(output).resolve()
    source = Path(base.read(pack / "private/mapping.json")["source_run"]).resolve()
    if output == pack or pack in output.parents or output == source or source in output.parents:
        raise ValueError("Evaluator output must remain outside repair/evidence inputs")
    original_config, original_version = base.config_from_manifest, base.VERSION
    provenance = {
        "version": "evaluator-expanded-output-v2",
        "base_driver_sha256": BASE_SHA256,
        "wrapper_sha256": base.sha(Path(__file__)),
        "source_repair_config_sha256": base.sha(Path(config)),
        "original_model_configuration": original_config(Path(config)),
        "evaluator_overrides": {"max_tokens": 32768, "transport_timeout_seconds": 600},
        "repair_configuration_changed": False,
        "prompts_and_scoring_rules_changed": False,
        "automatic_retries": 0,
    }
    base.preserve(output / "wrapper_manifest.json", provenance)

    def expanded_config(path):
        return {**original_config(path), "max_tokens": 32768}

    def expanded_transport(request, *, timeout):
        return (transport or base.send_once)(request, timeout=600)

    try:
        base.config_from_manifest = expanded_config
        base.VERSION = original_version + "-expanded-output-v2"
        return base.run(pack, Path(rubric), Path(config), output, execute=execute,
                        case_ids=case_ids, transport=expanded_transport)
    finally:
        base.config_from_manifest = original_config
        base.VERSION = original_version


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-export", type=Path, required=True)
    parser.add_argument("--rubric", type=Path, required=True)
    parser.add_argument("--run-config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case-id", action="append")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.execute and not base.os.getenv("AUTOFIX_LLM_API_KEY", "").strip():
        parser.error("--execute requires AUTOFIX_LLM_API_KEY")
    print(json.dumps(run(args.evidence_export, args.rubric, args.run_config, args.output,
                         execute=args.execute, case_ids=args.case_id), indent=2))


if __name__ == "__main__":
    main()
