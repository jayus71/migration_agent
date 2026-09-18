"""Record interpreter and installed package versions without environment secrets."""
import importlib.metadata
import json
from pathlib import Path
import platform
import sys


output = Path(sys.argv[1])
if output.exists():
    raise RuntimeError("Refusing to overwrite a runtime snapshot")
packages = sorted(({"name": dist.metadata.get("Name"), "version": dist.version}
                   for dist in importlib.metadata.distributions()), key=lambda row: row["name"] or "")
output.write_text(json.dumps({"python": sys.version, "executable": sys.executable,
                             "platform": platform.platform(), "packages": packages}, indent=2))
