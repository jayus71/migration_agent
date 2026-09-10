#!/usr/bin/env python3
"""Update terminology in the existing overview without changing its layout."""
from pathlib import Path
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "figures_to_be_redrawed/hierarchical_feedback_architecture.png"
OUTPUT = ROOT / "figures/hierarchical_feedback_architecture.png"


def font(size, bold=False):
    filename = "ARIALNB.TTF" if bold else "ARIALN.TTF"
    candidates = [Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / filename,
                  Path("/mnt/c/Windows/Fonts") / filename,
                  Path("/usr/share/fonts/truetype/dejavu") /
                  ("DejaVuSansCondensed-Bold.ttf" if bold else "DejaVuSansCondensed.ttf")]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    raise FileNotFoundError("Install Arial Narrow or DejaVu Sans Condensed")


def main():
    image = Image.open(SOURCE).convert("RGB")
    if image.size != (1691, 930):
        raise ValueError("The label coordinates require the original overview image")
    draw = ImageDraw.Draw(image)

    def label(box, text, size, color, bold=False, align="left", background_x=None):
        x0, y0, x1, y1 = box
        # Sample only a known clean column inside the same card, never a border
        # or connector. Keep every erase rectangle inside the card's interior.
        clean_x = x1 if background_x is None else background_x
        for y in range(y0, y1):
            draw.line((x0, y, x1 - 1, y), fill=image.getpixel((clean_x, y)))
        typeface = font(size, bold)
        bounds = draw.multiline_textbbox((0, 0), text, font=typeface, spacing=1)
        width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
        if width > x1 - x0 or height > y1 - y0:
            raise ValueError(f"Label does not fit: {text}")
        x = x0 if align == "left" else x0 + (x1 - x0 - width) / 2
        draw.multiline_text((x - bounds[0], y0 + (y1 - y0 - height) / 2 - bounds[1]),
                            text, font=typeface, fill=color, spacing=1, align=align)

    label((1345, 323, 1518, 365), "Repair Agent", 28, "#AB480A", True)
    label((834, 396, 1154, 422), "Forward values", 23, "#003CC4", True)
    label((834, 484, 1154, 512), "Gradients and parameter updates", 22, "#431482", True)
    draw.rectangle((807, 513, 1157, 548), fill=image.getpixel((1157, 546)))
    for left, right, text in [(813, 915, "Gradient norm"),
                              (923, 1039, "Parameter update"),
                              (1047, 1155, "Optimizer")]:
        draw.rounded_rectangle((left, 515, right, 545), radius=5,
                               fill="#FAF8FC", outline="#A387BD", width=1)
        label((left + 5, 519, right - 5, 541), text, 16, "#202020", align="center")
    label((1040, 431, 1138, 453), "Layer difference", 16, "#202020", align="center")
    label((887, 565, 1041, 587), "First failing stage", 20, "#202020", align="center")
    label((1387, 111, 1509, 138), "Checks passed", 20, "#202020", align="center")
    label((1118, 701, 1407, 729), "Final verification", 27, "#431482", True)
    label((1156, 736, 1407, 759), "Execution", 22, "#202020")
    label((1156, 767, 1407, 790), "Forward values", 22, "#202020")
    label((1156, 797, 1407, 822), "Gradients and parameter updates", 19, "#202020")
    label((373, 706, 865, 739), "torch4ms / MindSpore or TorchAX / JAX", 24,
          "#202020", True)
    label((290, 409, 428, 434), "target conventions", 20, "#202020")
    label((1300, 457, 1517, 486), "revised candidate", 22, "#202020")
    label((1009, 111, 1118, 138), "retain or roll back", 17, "#202020", align="center")
    image.save(OUTPUT)
    print(f"Saved: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
