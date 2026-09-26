"""Build the explicitly allowlisted, data-free anonymous review supplement.

This maintainer script and its private source map are NOT shipped in the ZIP.
Run under Linux from the manuscript checkout. No network or model calls occur.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "ascend-torch4ms"
REVISION = "694f6920ac89de66492d556e00dacb42fcd47154"
REPOSITORY = ROOT / "output/repository-migration-20260921/final/implementation_final"
DESTINATION = ROOT / "supplementary/ladim-supplementary.zip"
TEMPLATES = ROOT / "supplementary/review"
FILES: dict[str, bytes] = {}
SOURCES: list[dict] = []


def frozen(path):
    return subprocess.check_output(["git", "show", REVISION + ":" + path], cwd=UPSTREAM).decode()


def anonymize(text):
    # Only exported copies change. Keep a private mapping outside the submission.
    text = text.replace("torch4ms", "target_library").replace("Torch4ms", "TargetLibrary")
    text = text.replace("torchax", "jax_bridge").replace("TorchAX", "JAX bridge").replace("Torchax", "JaxBridge")
    text = text.replace("/media/main/whj/projects/target_library", "/opt/ladim")
    text = text.replace("/media/main/whj/miniconda3/envs", "/opt/ladim/environments")
    text = text.replace("/home/whj/", "/home/reviewer/")
    for old in ("jayus71", "feixiao13"):
        text = text.replace(old, "anonymous")
    return text


def put(name, text, source="authored review documentation", original=None):
    if name in FILES:
        raise ValueError("Duplicate destination: " + name)
    data = anonymize(text).encode()
    if name.endswith(".py"):
        ast.parse(data.decode(), filename=name)
    FILES[name] = data
    SOURCES.append({"destination": name, "source": source,
                    "source_sha256": hashlib.sha256((original if original is not None else text).encode()).hexdigest(),
                    "export_sha256": hashlib.sha256(data).hexdigest()})


def copy_file(source, destination=None):
    p = ROOT / source
    put(destination or source, p.read_text(), source)


def replace_function(text, name, replacement):
    nodes = [n for n in ast.walk(ast.parse(text)) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]
    if len(nodes) != 1:
        raise ValueError((name, len(nodes)))
    n = nodes[0]
    lines = text.splitlines(keepends=True)
    lines[n.lineno - 1:n.end_lineno] = [replacement.rstrip() + "\n"]
    return "".join(lines)


def core(prefix, repository=False):
    names = ["__init__", "agent", "tools", "progress", "observations", "sandbox", "baselines", "swe_upstream"]
    if repository:
        names.append("repository")
    put(prefix + "autofix/__init__.py", '"""LaDiM implementation for anonymous review."""\n')
    for name in names:
        path = "autofix/autonomous/" + name + ".py"
        if repository:
            source = str((REPOSITORY / path).relative_to(ROOT))
            text = (REPOSITORY / path).read_text()
        elif name in ("baselines", "swe_upstream"):
            source = "experiments/unified_migration50_20260918/integration_snapshot/" + name + ".py"
            text = (ROOT / source).read_text()
        else:
            source = REVISION + ":" + path
            text = frozen(path)
        put(prefix + path, text, source)
    # The inherited evaluator used an omitted author-owned bridge. Keep its
    # generic lifecycle/tool/snapshot helpers; native measurements override paired.
    original = frozen("autofix/autonomous/evaluation.py")
    text = original.replace("from autofix.verifiers.paired_code_report import generate_paired_code_harness\n", "")
    text = replace_function(text, "paired", '''    def paired(self, *, seed=None, timeout=180):
        raise NotImplementedError("Use UnifiedEvaluator or supply a task-specific evaluator.")''')
    text = replace_function(text, "backend_attested", '''def backend_attested(report):
    raise NotImplementedError("Use the selected native evaluator's backend checks.")''')
    put(prefix + "autofix/autonomous/evaluation.py", text, REVISION + ":autofix/autonomous/evaluation.py", original)
    original = frozen("autofix/autonomous/experiment.py")
    text = replace_function(original, "prepare", '''def prepare(*args, **kwargs):
    raise RuntimeError("Benchmark preparation is excluded from this data-free review package.")''')
    text = replace_function(text, "evaluator_for", '''def evaluator_for(run, task, workspace, evidence, python, manifest):
    raise RuntimeError("Inject UnifiedEvaluator or the evaluator for your supplied task.")''')
    text = re.sub(r'^BASE_COMMIT = .*\n|^I_REL = .*\n', '', text, flags=re.M)
    # Runtime locations become caller-supplied, without touching native algorithms.
    text = text.replace("import argparse\n", "import argparse\nimport os\n")
    text = text.replace('Path("/media/main/whj/projects/torch4ms/external_baselines/MatchFixAgent-66a52a5")', 'Path(os.environ["LADIM_MATCHFIX_ROOT"])')
    text = text.replace('"/media/main/whj/miniconda3/envs/matchfixagent/bin/python"', 'os.environ["LADIM_MATCHFIX_PYTHON"]')
    text = text.replace('"/media/main/whj/projects/torch4ms/external_baselines/SWE-agent-v1.1.0"', 'os.environ["LADIM_SWE_ROOT"]')
    text = text.replace('"/media/main/whj/miniconda3/envs/sweagent110/bin/python"', 'os.environ["LADIM_SWE_PYTHON"]')
    text = text.replace('"/media/main/whj/projects/torch4ms/experiments/autonomous_verifier_20260917/swe_native_vendor"', 'os.environ["LADIM_SWE_VENDOR"]')
    put(prefix + "autofix/autonomous/experiment.py", text, REVISION + ":autofix/autonomous/experiment.py", original)


def native_measurement():
    path = "experiments/unified_migration50_20260918/measure.py"
    original = (ROOT / path).read_text()
    text = original
    # Remove author-owned bridge execution branches, retaining native framework
    # and external MSAdapter measurement branches byte-for-byte.
    lines = text.splitlines(keepends=True)
    nodes = [n for n in ast.walk(ast.parse(text)) if isinstance(n, ast.If)
             and ast.unparse(n.test) in ("name == 'torch4ms'", "self.name == 'torch4ms'")]
    for n in sorted(nodes, key=lambda n: n.lineno, reverse=True):
        if n.orelse:
            end = n.orelse[0].lineno - 1
            lines[n.lineno - 1:end] = []
            lines[n.lineno - 1] = lines[n.lineno - 1].replace("elif ", "if ", 1)
        else:
            lines[n.lineno - 1:n.end_lineno] = []
    text = "".join(lines).replace("'torch4ms', ", "")
    put("evaluation/native/measure.py", text, path, original)


def configurations():
    path = ROOT / "data/audits/unified50-preflight-20260918/final_review/manifest.json"
    main = json.loads(path.read_text())
    keys = ("model", "temperature", "thinking_mode", "reasoning_effort", "max_calls", "max_output_tokens",
            "max_seconds", "max_repair_attempts", "per_call_output_tokens", "diagnosis_calls_per_stage",
            "repair_calls_per_stage", "memory_policy", "workflow_policy", "repair_budget",
            "generation_configuration", "methods", "acceptance", "cost", "statistical_unit", "feedback")
    put("configs/program_comparison.json", json.dumps({k: main[k] for k in keys}, indent=2) + "\n", str(path.relative_to(ROOT)))
    baseline = {k: {"commit": v["commit"], "implementation_bundled": False} for k, v in main["native_baselines"].items()}
    baseline.update(intertrans={"commit": "84d2d4337dc82d848772cf834440ba17497b7683", "implementation_bundled": False},
                    ivy={"conversion_api": "ivy.transpile", "training_api": "flax.nnx.value_and_grad + optax.sgd", "implementation_bundled": False},
                    torch2jax={"conversion_api": "torch2jax.t2j", "training_api": "jax.value_and_grad + optax.sgd", "implementation_bundled": False})
    put("configs/baseline_versions.json", json.dumps(baseline, indent=2) + "\n")
    cross = json.loads((path.parent / "cross_language/manifest.json").read_text())
    keys2 = ("model", "temperature", "thinking_mode", "reasoning_effort", "max_calls", "max_output_tokens", "max_seconds",
             "max_repair_attempts", "per_call_output_tokens", "diagnosis_calls_per_stage", "repair_calls_per_stage",
             "source_framework", "target_framework", "ordinary_test_repair", "generation_reuse")
    put("configs/language_comparison.json", json.dumps({k: cross[k] for k in keys2}, indent=2) + "\n")
    protocol = json.loads((REPOSITORY.parent / "protocol.json").read_text())
    put("configs/repository_comparison.json", json.dumps({k: v for k, v in protocol.items() if k not in ("context_fix", "progress_snapshots")}, indent=2) + "\n")
    readiness = json.loads((ROOT / "data/audits/unified50-preflight-20260918/readiness/summary.json").read_text())
    put("configs/recorded_native_packages.json", json.dumps(readiness["python_packages"], indent=2) + "\n")
    with tarfile.open(ROOT / "output/maintext-jax-autonomous-20260918/maintext_jax_complete_20260918.tar.gz") as archive:
        name = "maintext_jax_autonomous_20260918/formal_v5/manifest.json"
        recorded = json.load(archive.extractfile(name))
        keep = ("methods", "model", "temperature", "temperature_effective", "thinking_mode", "reasoning_effort",
                "max_calls", "max_output_tokens", "max_seconds", "max_repair_attempts", "per_call_output_tokens",
                "max_context_chars", "acceptance", "memory_policy", "workflow_policy", "diagnosis_calls_per_stage",
                "repair_calls_per_stage", "method_protocols", "counting")
        record = {k: recorded[k] for k in keep}
        record["external_converters"] = {"ivy": {"conversion": "ivy.transpile", "optimizer": "optax.sgd"},
                                         "torch2jax": {"conversion": "torch2jax.t2j", "optimizer": "optax.sgd"}}
        record["learning_rate"] = 0.01
        record["framework_bridges_bundled"] = False
        put("configs/jax_comparison.json", json.dumps(record, indent=2) + "\n", name)
    with tarfile.open(ROOT / "output/intertrans-completion-20260918-evidence.tar.gz") as archive:
        prefix = "intertrans-completion-20260918/code_snapshot/n18/"
        for name, output in (("pairing/intertrans_adapter.py", "configs/intertrans_adapter.py"),
                             ("training_interface.txt", "configs/language_training_interface.txt"),
                             ("pairing/candidate_worker.py", "evaluation/language_candidate_worker.py")):
            text = archive.extractfile(prefix + name).read().decode()
            put(output, text, prefix + name)
    put("configs/intertrans.json", json.dumps({
        "model": "deepseek-v4-flash", "maxGeneratedTokens": 131072, "temperature": 0.1, "top-p": 0.95,
        "used_languages": ["JavaScript", "Python"], "seed_language": "Java", "target_language": "Python",
        "numExecutionWorkers": 1, "numInferenceWorkers": 1, "useComputeEfficientMode": True,
        "earlyStop": False, "verifyIntermediateTranslations": False, "expansionIntermediaryNodes": 3,
        "applyRegexInferenceOnly": True, "useTranscoderTestFormat": False, "useInferenceCache": False,
        "useResponseCache": False, "useExecutionCache": False, "inferenceSeed": -1,
        "seeds": [101, 202, 303], "transport_timeout_seconds": 3600,
        "prompt_construction": "intertrans_adapter.py plus language_training_interface.txt and supplied public metadata",
        "evaluation_service": "External dataset-specific service; excluded with benchmark inputs."}, indent=2) + "\n")


def assemble():
    core("program/")
    core("repository/", repository=True)
    for package in ("evaluation", "evaluation/native"):
        put(package + "/__init__.py", '"""Evaluation utilities."""\n')
    for name in ("score", "evaluator", "domain", "components"):
        source = "experiments/unified_migration50_20260918/" + name + ".py"
        text = (ROOT / source).read_text().replace("experiments.unified_migration50_20260918", "evaluation.native")
        put("evaluation/native/" + name + ".py", text, source)
    native_measurement()
    source = "scripts/run_maintext_jax_autonomous.py"
    text = (ROOT / source).read_text()
    chunks = [ast.get_source_segment(text, n) for n in ast.parse(text).body
              if isinstance(n, ast.FunctionDef) and n.name in {"finite", "measurements"}]
    put("evaluation/jax_measurements.py", '"""Recorded JAX loss, gradient-norm and update differences."""\nimport math\n\n' + "\n\n".join(chunks) + "\n", source, text)
    # Keep the actual shared initial-translation functions and prompt, excluding
    # launch paths coupled to withheld task manifests or private worktrees.
    source = "experiments/unified_migration50_20260918/translation.py"
    text = (ROOT / source).read_text()
    wanted = {"extract", "cte_candidate", "generate"}
    functions = [ast.get_source_segment(text, n) for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name in wanted]
    put("program/translation.py", '"""Shared initial generation and exact provider-usage receipts."""\nimport hashlib\nimport json\nimport re\n\n' + "\n\n".join(functions) + "\n", source, text)
    tree = ast.parse((ROOT / "experiments/unified_migration50_20260918/prepare_review.py").read_text())
    system = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "SYSTEM" for t in n.targets))
    put("configs/translation_prompt.txt", system + "\n")
    copy_file("experiments/unified_migration50_20260918/cte_config.yaml", "configs/codetransengine.yaml")
    configurations()
    for name in ("test_autonomous_agent", "test_autonomous_edit_guard", "test_autonomous_memory", "test_autonomous_observations"):
        source = "tests/" + name + ".py"
        original = frozen(source)
        text = original
        if name == "test_autonomous_agent":
            # A neutral directory name has a different lexicographic position.
            text = text.replace('["candidate.py", "source.py", "task.json", "torch4ms/ops.py"]',
                                'sorted(["candidate.py", "source.py", "task.json", "torch4ms/ops.py"])')
        put("tests/program/" + name + ".py", text, REVISION + ":" + source, original)
    source = "experiments/unified_migration50_20260918/test_score.py"
    put("tests/program/test_score.py", (ROOT / source).read_text().replace("experiments.unified_migration50_20260918", "evaluation.native"), source)
    scripts = ("repository_bootstrap", "repository_shared_translation", "repository_timeseries_worker", "repository_twotower_candidate_worker")
    for name in scripts:
        source = REPOSITORY / "scripts" / (name + ".py")
        put("repository/scripts/" + name + ".py", source.read_text(), str(source.relative_to(ROOT)))
    # Export the final repository scheduling function with caller-supplied input
    # roots and evaluator factory, replacing only private launch dependencies.
    source = REPOSITORY / "scripts/repository_migration_experiment.py"
    original = source.read_text()
    functions = []
    for node in ast.parse(original).body:
        if isinstance(node, ast.FunctionDef) and node.name in {"configuration", "named_tests", "make_workspace", "run"}:
            value = ast.get_source_segment(original, node)
            if node.name == "run":
                value = value.replace("def run(repository, method):\n    assert_frozen()\n    root = bind(repository)",
                    "def run(repository, method, root, evaluator_factory, adapter_factory=None):\n    root = Path(root).resolve()")
                value = value.replace("ev = evaluator(repository, ws, folder / 'evidence')", "ev = evaluator_factory(repository, ws, folder / 'evidence')")
                value = value.replace("adapter_for(method, agent)", "adapter_factory(method, agent)")
                value = value.replace("digest(RUN / 'freeze.json')", "digest(root / 'freeze.json')")
            functions.append(value)
    header = '''"""Final repository repair schedule over externally prepared inputs.

Supply evaluator_factory(repository, workspace, evidence) returning an object
with tool(request) and final(), and adapter_factory(method, agent) for baselines.
    The prepared root contains source/, task.json, manifest.json, freeze.json
    and translation/. The caller validates its frozen external input manifest.
"""
from dataclasses import asdict, replace
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import time
import traceback
from autofix.autonomous.agent import AgentConfig, AutonomousAgent
from autofix.autonomous.tools import WorkspaceTools
from autofix.autonomous.repository import RepositoryAgent, RepositoryTools

BUDGET = dict(model='deepseek-v4-flash', max_calls=80, max_output_tokens=480000,
              max_seconds=3600, per_call_output_tokens=32768)

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\\n')

def read(path):
    return json.loads(path.read_text())

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def hashes(root):
    return {p.relative_to(root).as_posix(): digest(p) for p in sorted(root.rglob('*'))
            if p.is_file() and not any(x.startswith('.') or x == '__pycache__' for x in p.relative_to(root).parts)}

'''
    put("repository/orchestration.py", header + "\n\n".join(functions) + "\n", str(source.relative_to(ROOT)), original)
    # Export repository comparison predicates without dataset preparation code.
    for name, functions, constants in (("repository_timeseries_pilot", {"compare", "protocol"}, set()),
                                        ("run_repository_twotower", {"compare"}, {"THRESHOLDS"})):
        source = REPOSITORY / "scripts" / (name + ".py")
        text = source.read_text()
        chunks = []
        for node in ast.parse(text).body:
            if isinstance(node, ast.FunctionDef) and node.name in functions:
                chunks.append(ast.get_source_segment(text, node))
            elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in constants for t in node.targets):
                chunks.append(ast.get_source_segment(text, node))
        label = "timeseries" if "timeseries" in name else "twotower"
        put("evaluation/" + label + ".py", '"""Recorded repository acceptance predicates."""\nimport numpy as np\n\n' + "\n\n".join(chunks) + "\n", str(source.relative_to(ROOT)), text)
    for name in ("test_repository_context", "test_repository_context_fix", "test_repository_bootstrap"):
        copy_file("scripts/" + name + ".py", "tests/repository/" + name + ".py")
    for path in sorted(TEMPLATES.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            copy_file(str(path.relative_to(ROOT)), str(path.relative_to(TEMPLATES)))


FORBIDDEN = re.compile(r"jayus71|feixiao13|\bwhj\b|torch4ms|torchms|torchax|gitee\.com|migration_agent|/media/main/|/home/(?!reviewer/)[\w-]+/|C:\\\\Users|BEGIN (?:RSA |OPENSSH )?PRIVATE KEY|sk-[A-Za-z0-9_-]{18,}", re.I)


def main():
    assemble()
    problems = []
    for name, data in FILES.items():
        if FORBIDDEN.search(name) or FORBIDDEN.search(data.decode()):
            problems.append(name)
        if any(p in {".git", "__pycache__", "datasets", "private_inputs", "private_references"} for p in Path(name).parts):
            problems.append(name)
    if problems:
        raise RuntimeError("Anonymity/export audit failed: " + repr(problems))
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(FILES.items())}
    FILES["MANIFEST.sha256"] = "".join(f"{sha}  {name}\n" for name, sha in manifest.items()).encode()
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(DESTINATION, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(FILES.items()):
            info = zipfile.ZipInfo("ladim-supplementary/" + name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    assert DESTINATION.stat().st_size < 100_000_000
    with zipfile.ZipFile(DESTINATION) as archive:
        assert archive.testzip() is None
        assert not archive.comment
    private = ROOT / "output/supplementary-review"
    private.mkdir(parents=True, exist_ok=True)
    (private / "private-source-map.json").write_text(json.dumps(SOURCES, indent=2) + "\n")
    report = {"archive": str(DESTINATION), "bytes": DESTINATION.stat().st_size,
              "sha256": hashlib.sha256(DESTINATION.read_bytes()).hexdigest(), "files": len(FILES),
              "anonymity_scan": "passed", "zip_integrity": "passed", "datasets_included": False,
              "adapter_implementations_included": False, "model_calls": 0}
    (private / "build-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
