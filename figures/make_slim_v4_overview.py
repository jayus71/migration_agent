"""Launch the shared editable PowerPoint/SVG builder with the presentation runtime."""
import os
from pathlib import Path
import subprocess

if __name__ == "__main__":
    subprocess.run([os.environ.get("RUNTIME_NODE", "node"),
                    str(Path(__file__).with_name("make_overview.mjs"))], check=True)
