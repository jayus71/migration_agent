#!/usr/bin/env python3
"""Export the editable SVG overview to the manuscript's vector PDF and PNG."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "figures/架构图0914.svg"
OUTPUT = ROOT / "figures/hierarchical_feedback_architecture"


def main():
    inkscape = shutil.which("inkscape")
    if inkscape is None:
        raise FileNotFoundError("Install Inkscape to export the editable overview")
    env = os.environ.copy()
    # The SVG uses Windows fonts, which WSL can read without installing them.
    windows_fonts = Path("/mnt/c/Windows/Fonts")
    with tempfile.TemporaryDirectory(prefix="ladim-overview-") as temporary:
        if windows_fonts.is_dir() and Path("/etc/fonts/fonts.conf").exists():
            config = Path(temporary) / "fonts.conf"
            config.write_text(
                '<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd">'
                '<fontconfig><include>/etc/fonts/fonts.conf</include>'
                f'<dir>{escape(str(windows_fonts))}</dir></fontconfig>'
            )
            env["FONTCONFIG_FILE"] = str(config)
        for extension in ("pdf", "png"):
            output = OUTPUT.with_suffix(f".{extension}")
            command = [inkscape, str(SOURCE), f"--export-filename={output}",
                       "--export-area-page"]
            if extension == "png":
                command.append("--export-width=2200")
            subprocess.run(command, check=True, env=env)
            print(f"Saved: {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
