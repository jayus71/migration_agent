"""Describe frozen manuscript inputs without executing any candidate program."""
from pathlib import Path
import ast
import hashlib
import json
import statistics
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def describe(name, payload):
    text = payload.decode("utf-8-sig")
    try:
        classes = [node.name for node in ast.walk(ast.parse(text)) if isinstance(node, ast.ClassDef)]
    except SyntaxError:
        classes = []
    return {"source": name, "sha256": hashlib.sha256(payload).hexdigest(),
            "nonblank_lines": sum(bool(line.strip()) for line in text.splitlines()),
            "classes": classes}


def archive_sources(relative, predicate):
    path = ROOT / relative
    with tarfile.open(path) as archive:
        rows = [describe(member.name, archive.extractfile(member).read())
                for member in archive if member.isfile() and predicate(member.name)]
    return rows


def main():
    collections = {}
    main_manifest = json.loads((ROOT / "data/benchmarks/unified50_20260918/manifest.json").read_text())
    rows = []
    for task in main_manifest["tasks"]:
        path = ROOT / "data/benchmarks/unified50_20260918/public" / task["task"] / "source.py"
        row = describe(str(path.relative_to(ROOT)), path.read_bytes())
        assert row["sha256"] == task["source_sha256"]
        rows.append(row)
    assert len(rows) == 50
    collections["mindspore_migration"] = rows
    language_root = ROOT / "data/audits/unified50-preflight-20260918/final_review/cross_language"
    rows = []
    for task in json.loads((language_root / "manifest.json").read_text())["tasks"]:
        path = language_root / "private_inputs" / task["anonymous_id"] / "source.py"
        row = describe(str(path.relative_to(ROOT)), path.read_bytes())
        assert row["sha256"] == task["source_sha256"]
        row["program"] = task["original_id"]
        rows.append(row)
    assert len(rows) == 18
    collections["java_migration"] = rows
    collections["natural_repairs"] = archive_sources(
        "output/maintext-ablations-20260918/archives/original_natural10_v3.tar.gz",
        lambda n: "/without_edit_format_feedback/private_inputs/" in n and n.endswith("/source.py"))
    collections["training_signals"] = archive_sources(
        "output/maintext-ablations-20260918/archives/training_signal16_v2_complete.tar.gz",
        lambda n: "/all_observations/conditions/" in n and n.endswith("/workspace/source.py"))
    collections["jax_repairs"] = archive_sources(
        "output/maintext-jax-autonomous-20260918/maintext_jax_complete_20260918.tar.gz",
        lambda n: "/formal_v5/conditions/" in n and "/autonomous_layered/" in n
        and n.endswith("/workspace/source.py"))
    assert len(collections["natural_repairs"]) == 10
    assert len(collections["training_signals"]) == 16
    assert len(collections["jax_repairs"]) == 6
    collections["source_target_repairs"] = archive_sources(
        "output/paired12-matchfix-20260918-evidence.tar.gz",
        lambda n: n.startswith("paired12-matchfix-20260918-v1/private_inputs/")
        and n.endswith("/source.py"))
    assert len(collections["source_target_repairs"]) == 12
    repository_archive = ROOT / "output/repository-migration-20260921/final-evidence.tar.gz"
    with tarfile.open(repository_archive) as archive:
        for repository in ("timeseries", "twotower"):
            prefix = repository + "/source/"
            manifest = json.load(archive.extractfile(repository + "/manifest.json"))
            rows = []
            for member in archive.getmembers():
                if not member.isfile() or not member.name.startswith(prefix):
                    continue
                relative = member.name[len(prefix):]
                if not relative.endswith((".py", ".ipynb")):
                    continue
                payload = archive.extractfile(member).read()
                assert hashlib.sha256(payload).hexdigest() == manifest["source_hashes"][relative]
                if relative.endswith(".ipynb"):
                    notebook = json.loads(payload)
                    payload = "\n".join("".join(c["source"]) for c in notebook["cells"]
                                        if c["cell_type"] == "code").encode()
                rows.append(describe(member.name, payload))
            collections[repository] = rows
    output = {"length_definition": "Nonblank physical source lines, including comments. "
              "Notebook lengths count code cells only. Program means count each distinct source hash once. "
              "Repository totals include all frozen Python files and notebook code cells.",
              "collections": {}}
    for name, rows in collections.items():
        lengths = [row["nonblank_lines"] for row in rows]
        unique = {row["sha256"]: row for row in rows}
        output["collections"][name] = {"count": len(rows), "unique_sources": len(unique),
                                      "mean_lines": statistics.mean(r["nonblank_lines"] for r in unique.values()),
                                      "task_weighted_mean_lines": statistics.mean(lengths),
                                      "total_lines": sum(lengths), "min_lines": min(lengths),
                                      "max_lines": max(lengths), "sources": rows}
    target = ROOT / "data/paper_figures/collection_statistics.json"
    target.write_text(json.dumps(output, indent=2) + "\n")
    coverage = [
        ("mindspore_migration", "PyTorch to MindSpore", "Generated translations", "Operators, CNNs, MLPs, Transformers, language models"),
        ("natural_repairs", "Initial translations", "Five fail and five pass their first evaluation", "Recurrent, convolutional, attention, and set models"),
        ("training_signals", "Training signal ablation", "Controlled training faults", "CNN, image MLP, Transformer, causal language model"),
        ("jax_repairs", "JAX repair", "Supplied faulty candidates", "MLP and CNN"),
    ]
    table = [r'\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}>{\raggedright\arraybackslash}p{3.1cm}>{\raggedright\arraybackslash}p{3.1cm}>{\raggedright\arraybackslash}p{4.9cm}r@{}}',
             r'\toprule', r'\textbf{Collection} & \textbf{Candidate construction} & \textbf{Model or operation coverage} & \textbf{Tasks} \\', r'\midrule']
    for key, label, construction, models in coverage:
        count = output['collections'][key]['count']
        table.append(f'{label} & {construction} & {models} & {count}' + r' \\')
    table += [r'\bottomrule', r'\end{tabular*}']
    (ROOT / 'figures/TABLE_task_collections.tex').write_text('\n'.join(table) + '\n')
    print(json.dumps({key: {k: v for k, v in value.items() if k != "sources"}
                      for key, value in output["collections"].items()}, indent=2))


if __name__ == "__main__":
    main()
