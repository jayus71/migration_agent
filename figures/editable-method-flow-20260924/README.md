# Editable method flow diagram

Reconstructed from `ChatGPT Image Sep 24, 2026, 03_56_07 PM.png`.
The 1672 × 941 canvas preserves the reference's upper migration flow, central orchestrator, lower repository context modules, and caption.
All text uses Times New Roman.

- `method-diagram-editable.pptx`: one slide with editable text and native vector objects.
- `method-diagram.svg`: the complete vector diagram with editable text.
- `method-diagram-vector.pdf`: vector PDF with embedded Times New Roman fonts.
- `method-diagram-preview.png`: preview rendered from the final grouped PPTX.
- `icons/`: individual SVG files for the four supplied logos and status symbols.

Select a module in PowerPoint and use **Group > Ungroup** to edit its components.
Icons use native vector paths, with nested groups where useful; they can be ungrouped again to edit individual parts.
Text boxes can also be edited inside their groups.
Arrows, diagnostic curves, file trees, and dependency graph components are native editable shapes.
The slide contains no embedded raster images.

The Python, PyTorch, Java, and MindSpore icons reuse paths from the user-supplied `figures/icons/` SVGs.
Their curves are sampled as vector paths; gradient shading is simplified and the Python raster shadow is omitted.
Other small icons and diagnostic curves are reconstructed to match the reference composition.
This is a standalone conversion of the supplied image; the manuscript's included method figure is unchanged.

## Rebuild

1. Run `scripts/prepare_method_flow_icons_20260924.py` using the repository Python environment with fontTools and lxml.
2. Run `figures/rebuild_method_flow_20260924.mjs` using the bundled Node.js runtime, with `RUNTIME_NODE_MODULES` and `RUNTIME_PYTHON` set.
3. Run `scripts/finalize_method_flow_20260924.py` using the bundled Python runtime.
4. Run `scripts/validate_method_flow_20260924.mjs`, additionally setting `SKILL_DIR` and a fresh Windows-local `METHOD_DIAGRAM_VALIDATION_DIR`.
5. Export the generated SVG with Inkscape, using a fontconfig configuration that includes the Windows Times New Roman fonts.

Build intermediates and validation receipts are under `tmp/method-flow-20260924/`.
