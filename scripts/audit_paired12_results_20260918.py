"""Reconcile all paired12 outcomes against immutable inputs and provider usage."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = read(root / "manifest.json")
    complete = read(root / "complete.json")["summary"]
    summary = read(root / "summary.json")
    assert complete["methods"] == summary["methods"]
    assert summary["running"] == 0 and not summary["infrastructure_errors"]
    assert len(manifest["tasks"]) == 12 and len(manifest["methods"]) == 2
    implementation = read(root / "implementation.json")
    assert implementation["git_head"] == "694f6920ac89de66492d556e00dacb42fcd47154"
    for name, expected_hash in implementation["files"].items():
        assert sha(root / "code_snapshot" / name) == expected_hash
    rows, ledger, seen_ids = [], [], set()
    for task in manifest["tasks"]:
        task_id = task["anonymous_id"]
        expected = root / "private_inputs" / task_id
        for method in manifest["methods"]:
            case = root / "conditions" / task_id / method
            result = read(case / "result.json")
            assert result["status"] == "completed" and not result["initially_accepted"]
            assert result["accepted"] == result["final"]["accepted"]
            initial = case / "evidence/initial_code"
            original = {p.relative_to(expected).as_posix(): sha(p)
                        for p in expected.rglob("*.py") if p.name != "source.py"}
            snapshot = {p.relative_to(initial).as_posix(): sha(p) for p in initial.rglob("*.py")}
            assert original == snapshot, (task_id, method, "initial code")
            for name in ("source.py", "task.json"):
                assert sha(case / "workspace" / name) == sha(expected / name)
            agent = case / "evidence/agent"
            calls = []
            for path in sorted(agent.glob("call_*_request.json")):
                request = read(path)
                response_path = path.with_name(path.name.replace("_request", "_response"))
                response = read(response_path)
                response_id = response["id"]
                assert response_id and response_id not in seen_ids
                seen_ids.add(response_id)
                usage = response["usage"]
                assert all(isinstance(usage.get(k), int) for k in
                           ("prompt_tokens", "completion_tokens", "total_tokens"))
                assert usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]
                assert request["model"] == "deepseek-v4-flash"
                assert response["model"].startswith("deepseek")
                calls.append(dict(task=task_id, method=method, response_id=response_id,
                    prompt_tokens=usage["prompt_tokens"], completion_tokens=usage["completion_tokens"],
                    total_tokens=usage["total_tokens"], requested_model=request["model"],
                    actual_model=response["model"], request_sha256=sha(path),
                    response_sha256=sha(response_path)))
            totals = {k: sum(c[k] for c in calls) for k in
                      ("prompt_tokens", "completion_tokens", "total_tokens")}
            assert len(calls) == result["budget"]["calls"]
            assert result["budget"]["usage"]["unknown_usage_calls"] == 0
            assert all(result["budget"]["usage"][k] == v for k, v in totals.items())
            attempts = result["attempts"]
            accepted_attempts = [a["attempt"] for a in attempts if a.get("accepted")]
            assert bool(accepted_attempts) == result["accepted"]
            upstream = None
            if method == "matchfix_full_orchestration":
                baseline = read(agent / "baseline_manifest.json")
                assert baseline["upstream_commit"] == "66a52a5626f5e8b480abbcd4b0e7a287fb3d85a7"
                assert baseline["ground_truth_target_function"].startswith("empty;")
                worker = read(agent / "matchfix_full_01/worker_input.json")
                assert worker["operation"] == "full" and worker["analyses"] is None
                fragment = worker["fragment"]
                assert fragment["ground_truth_target_function"] == ""
                assert fragment["source_function"] == (expected / "source.py").read_text().splitlines()
                assert fragment["target_function"] == (expected / "candidate.py").read_text().splitlines()
                upstream = baseline["upstream_commit"]
            roles = [read(p) for p in sorted(agent.glob("matchfix_role_*.json"))]
            rows.append(dict(task=task_id, method=method, accepted=result["accepted"],
                accepted_at=min(accepted_attempts) if accepted_attempts else None,
                submissions=len(attempts), calls=len(calls), **totals,
                seconds=result["wall_time_sec"], source_sha256=sha(expected / "source.py"),
                initial_candidate_sha256=sha(expected / "candidate.py"), initial_inputs_equal=True,
                upstream_commit=upstream, upstream_role_records=len(roles),
                attempt_statuses=[a.get("stage", {}).get("status") for a in attempts],
                result_sha256=sha(case / "result.json")))
            ledger.extend(calls)
    methods = {}
    for method in manifest["methods"]:
        selected = [r for r in rows if r["method"] == method]
        assert len(selected) == 12
        accepted = sum(r["accepted"] for r in selected)
        cumulative = {str(n): sum(r["accepted_at"] is not None and r["accepted_at"] <= n
                                 for r in selected) for n in (1, 2, 4)}
        totals = {k: sum(r[k] for r in selected) for k in
                  ("calls", "prompt_tokens", "completion_tokens", "total_tokens", "seconds")}
        recorded = summary["methods"][method]
        assert recorded["accepted"] == accepted and recorded["completed"] == 12
        assert cumulative == recorded["accepted_by_attempt"]
        assert totals["prompt_tokens"] == recorded["prompt_tokens"]
        assert totals["completion_tokens"] == recorded["completion_tokens"]
        methods[method] = dict(accepted=accepted, planned=12, accepted_at=cumulative, **totals,
            tokens_per_accepted=totals["total_tokens"] / accepted if accepted else None,
            failed_tasks=[r["task"] for r in selected if not r["accepted"]])
    outcomes = {m: {r["task"]: r["accepted"] for r in rows if r["method"] == m}
                for m in manifest["methods"]}
    ours, baseline = outcomes["autonomous_layered"], outcomes["matchfix_full_orchestration"]
    overlap = Counter((ours[t], baseline[t]) for t in ours)
    report = dict(complete=True, protocol_version=manifest["protocol_version"],
        conditions=len(rows), unique_responses=len(seen_ids), new_model_calls=0,
        audit_scope="Offline reconciliation of existing runs; no candidate or baseline edits.",
        all_initial_inputs_equal=True, unknown_usage_calls=0, methods=methods,
        overlap=dict(both=overlap[(True, True)], ours_only=overlap[(True, False)],
                     baseline_only=overlap[(False, True)], neither=overlap[(False, False)]),
        input_hashes={name: sha(root / name) for name in
                      ("manifest.json", "implementation.json", "complete.json", "summary.json")},
        rows=rows)
    save(root / "paper_results.json", report)
    save(root / "usage_ledger.json", ledger)
    with (root / "paper_results.csv").open("w", newline="", encoding="utf-8") as stream:
        fields = [k for k in rows[0] if k != "attempt_statuses"]
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({k: v for k, v in report.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
