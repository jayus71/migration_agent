# Editable method diagram

Reconstructed from the user-supplied `ChatGPT Image Sep 24, 2026, 11_33_02 AM.png`.
The three columns, role panels, diagnosis chain, workspace, code examples and footer retain the supplied image's composition.
Times New Roman follows the user's explicit confirmation on September 24.

- `method-diagram-editable.pptx`: one slide with native text and vector shapes.
- `method-diagram.svg`: the complete vector diagram, with editable text.
- `method-diagram-vector.pdf`: vector export with embedded Times New Roman fonts.
- `method-diagram-preview.png`: preview rendered from the final grouped PPTX.
- `icons/` and `method-diagram-svg-assets.zip`: individual SVG icons and the complete SVG.

In PowerPoint, select a module and use **Group > Ungroup** to edit its components.
Icons are nested groups, so a second ungroup may be useful for their individual parts.
Text boxes can be edited directly within a group.
Arrow routes and arrowheads are native vector shapes whose points and colors can be edited.

The original raster is a layout reference and is not embedded in the slide.
Small shaded icons were redrawn as vector components, so their contours and shading are approximate.
This standalone reconstruction does not replace the manuscript's included method figure.

## Rebuild

Use the bundled Node.js and Python runtimes with `@oai/artifact-tool`, Pillow and lxml.
Set `RUNTIME_NODE_MODULES`, `RUNTIME_PYTHON` and `SKILL_DIR` to the corresponding presentation runtime and skill paths.
`METHOD_DIAGRAM_FONT_DIR` can override the Times New Roman font directory.

1. Run `figures/rebuild_method_image_20260924.mjs` with the bundled Node.js.
2. Run `scripts/finalize_method_image_20260924.py` with the bundled Python.
3. Run `scripts/validate_method_image_20260924.mjs` with the bundled Node.js.
   On Windows with a WSL repository, set `METHOD_DIAGRAM_VALIDATION_DIR` to a fresh local directory because UNC shares do not support the finalizer's atomic hard link.
   The finalizer deliberately refuses to overwrite an existing final file in that directory.
4. Export the generated SVG with Inkscape using Times New Roman, then inspect the PDF.

Temporary layout, rendering and validation files are stored under `tmp/method-image-20260924/`.
