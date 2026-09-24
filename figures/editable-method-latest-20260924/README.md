# Editable method diagram from the 21:38 reference

`method-diagram-editable.pptx` preserves the layout of the supplied `ChatGPT Image Sep 24, 2026, 09_38_25 PM.png`. It contains one slide with 463 native shapes, 98 editable text boxes, and 50 native groups. All text uses Times New Roman. There are no embedded bitmap images.

Select a module in PowerPoint and choose **Group > Ungroup** to edit its components. Icons have nested groups; ungroup again to edit individual vector paths. Text can be edited directly within groups. Curves and arrowheads are native shapes.

- `method-diagram-editable.pptx`: editable PowerPoint.
- `method-diagram-preview.png`: rendering of the final grouped PowerPoint.
- `method-diagram.svg`: complete vector figure with editable text.
- `method-diagram-vector.pdf`: vector export from the same diagram, with Times New Roman embedded.
- `icons/`: individual reusable SVGs used in this reconstruction.
- `source-icons/`: unchanged copies of the five supplied framework and language SVGs.
- `method-diagram-svg-assets.zip`: full SVG and individual SVG assets.

The original reference and previous diagram versions remain in their existing locations. This conversion is a separate asset and does not replace the manuscript's included figure. Fine icon shading and wave contours are simplified when represented as vector components.

## Rebuild

1. Run `uv run --with fonttools --with lxml scripts/prepare_method_latest_icons_20260924.py` to convert supplied SVG contours into native vector paths.
2. Use the bundled Node runtime to run `figures/rebuild_method_latest_20260924.mjs`, setting `RUNTIME_NODE_MODULES` and `RUNTIME_PYTHON` to the bundled paths. `METHOD_DIAGRAM_FONT_DIR` can override the Windows font directory.
3. Run `scripts/finalize_method_latest_20260924.py` with the bundled Python to apply native grouping and check editability.
4. Use the bundled Node runtime to run `scripts/validate_method_latest_20260924.mjs`, also setting `SKILL_DIR` to the presentation skill. On Windows/WSL, set `METHOD_DIAGRAM_VALIDATION_DIR` to a new local directory for the finalizer's atomic publication.
5. Export `method-diagram.svg` with Inkscape using Times New Roman and inspect the PDF. Build and validation artifacts are stored in `tmp/method-latest-20260924/`.

The final package and font checks passed. The grouped PPTX was imported and rendered with Artifact Tool; native execution in the PowerPoint desktop application was not part of these checks.
