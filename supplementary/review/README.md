# LaDiM supplementary material

This archive contains LaDiM's program and repository repair implementations, evaluation utilities, baseline configurations, and offline regression tests. It is an anonymous source-code supplement. Benchmark datasets, source-task collections, saved candidate programs, reference traces, trained weights, model responses, and author-owned framework bridges are intentionally excluded.

## Contents

| Directory | Contents |
| --- | --- |
| `program/` | Program-level diagnosis, independent evidence handoff, persistent repair history, tools, controller, and initial translation functions |
| `repository/` | Repository context, dependency planning, bounded translation, and repository measurement workers |
| `evaluation/` | Native framework measurements, numerical acceptance, repository comparison predicates, and additional measurement utilities |
| `configs/` | Recorded generation/repair budgets, baseline settings, public prompts, and dependency versions |
| `tests/` | Offline agent, history, edit-integrity, scoring, and repository-context regression tests |
| `tools/` | Archive verification, offline checks, and a program-level execution entry point |

The two implementation directories preserve the corresponding measured program and repository controller variants. Select one per Python process. The internal `autofix` package name is retained to keep import relationships intact. `target_library/` is a neutral optional workspace directory; its implementation is not supplied.

## Quick check

Use Linux and Python 3.11 or newer. The core agent uses the standard library. NumPy is required for numerical scoring; framework packages are needed only for executing user-supplied training programs.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-review.txt
.venv/bin/python tools/verify_package.py
.venv/bin/python tools/check_offline.py
```

The offline suite uses temporary synthetic unit fixtures and scripted model responses. It makes no API calls and does not reproduce the paper's benchmark results. `MANIFEST.sha256` covers every distributed file except the manifest itself.

## Read the implementation

Start with `program/autofix/autonomous/agent.py`, `tools.py`, and `experiment.py`. `AgentConfig` holds lifetime budgets, `diagnose` investigates using read-only production tools, and `repair` consumes the independent evidence while preserving repair history. The controller evaluates candidates after submissions and performs seed confirmation. `program/translation.py` preserves the shared initial-generation extraction and usage-recording functions; its prompt and generation parameters are in `configs/`.

For repository migration, read `repository/autofix/autonomous/repository.py`, `repository/orchestration.py`, and `repository/scripts/repository_shared_translation.py`. The repository tools maintain public symbol/import information, work-unit dependencies, evidence, and checkpoints. The context implementation preserves relevant observations across work units. The orchestration function retains the measured diagnosis and four-submission schedule and accepts an external evaluator factory. Repository-specific comparison functions and measurement workers are supplied separately from the withheld source repositories.

## Run on independently supplied inputs

`tools/run_program.py` connects the exported controller to the native evaluator. It requires a prepared run directory, a source program, candidate, public contract, and separate reference measurements. See `INPUT_CONTRACT.md` for their layout. Run `python tools/run_program.py --help` for the required arguments. Model execution additionally requires `AUTOFIX_LLM_API_KEY`, a suitable `AUTOFIX_LLM_BASE_URL`, and access to the requested model. Credentials must be supplied at runtime.

Native framework measurements can be collected with:

```bash
python -m evaluation.native.measure --program /path/to/source.py --contract /path/to/task.json --kind execution --runtime torch --seed 101 --out /path/to/reference.json
python -m evaluation.native.measure --program /path/to/candidate.py --contract /path/to/task.json --kind execution --runtime mindspore --seed 101 --out /path/to/target.json
python tools/score_measurements.py --reference /path/to/reference.json --target /path/to/target.json
```

The `--kind` value and public interfaces must match the supplied task contract; `execution` above is one supported interface family. These commands execute user-supplied Python programs. The LaDiM controller uses the supplied isolation implementation for candidate execution.

The withheld datasets and framework bridges are necessary for a complete reproduction of their respective paper experiments. This package supports source inspection, offline regression testing, scoring compatible saved measurements, and execution on independently prepared native-framework inputs. It contains no dataset download links, author repository links, or credentials.

## Baselines

`BASELINES.md` maps all baseline methods to the supplied settings and integration sources. Third-party baseline implementations and framework adapters are not vendored. Baseline configuration names identify external methods, not the authors. Native methods require their independently installed upstream packages and the recorded revisions. Preserve their original algorithms, prompts, parsers, tools, retries, and failed-attempt accounting.

`EXPORT_NOTES.md` documents the packaging changes and the verification boundary. The package does not contain Git history, author metadata, private worktree paths, or benchmark outcomes.
