"""Expose Ivy's swallowed compiler import error inside the repair sandbox."""
import json
import os
from pathlib import Path
import sys
import traceback


if len(sys.argv) > 1:
    run = Path(sys.argv[1])
    sys.path.insert(0, str(run / "code_snapshot"))
    from autofix.autonomous.sandbox import run_isolated
    python = Path("/media/main/whj/venvs/trackc_ivy/bin/python")
    workspace = run / "conditions/task_001/ivy_clean_gate/workspace"
    print(json.dumps(run_isolated(workspace, python, Path(__file__),
        extra_reads=[str(python.resolve().parent.parent)]), indent=2))
else:
    os.environ["HOME"] = os.environ["TMPDIR"]
    os.environ["XDG_CACHE_HOME"] = os.environ["TMPDIR"]
    os.chdir(os.environ["TMPDIR"])
    ivy_root = Path(os.environ["TMPDIR"]) / ".ivy"
    ivy_root.mkdir(exist_ok=True)
    os.environ["IVY_ROOT"] = str(ivy_root)
    try:
        import ivy
        from ivy.tracer import trace_graph
        from ivy.transpiler import transpile
        print("Ivy compiler available")
    except Exception:
        traceback.print_exc()
