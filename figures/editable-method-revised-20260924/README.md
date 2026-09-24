# Revised editable method diagram

This is a separately saved revision of `../editable-method-flow-20260924/method-diagram-editable.pptx`. The original folder and generator are preserved byte-for-byte relative to commit b570a20.

The six upper modules share their top and bottom edges. Translator and Repair Agent are narrower, with compact code illustrations. Blue emphasizes layered diagnosis, orange emphasizes evidence handoff, and green emphasizes repository context management. All text uses Times New Roman with dark text colors.

The verifier retains five aligned rows. The source and target curves remain for Execution, Forward values, and Gradients. The source gradient stays blue, while the divergent target is red. Neutral pause symbols replace the curves in Parameter update and Next forward. These are schematic diagnostic illustrations, not measured experimental plots.

Repeated explanatory text, the four Not compared labels, the long caption, and auxiliary agent details were removed. Source and target language/framework rows and file-tree panels are aligned.

- `method-diagram-editable.pptx`: one slide, 346 native shapes, 76 editable text boxes, and 37 groups. No raster images.
- `method-diagram.svg`: matching vector figure with editable text.
- `method-diagram-vector.pdf`: matching vector PDF with embedded Times New Roman.
- `method-diagram-preview.png`: rendered final PPTX preview.
- `icons/`: separate SVG logo assets and original status symbols.
- `method-diagram-svg-assets.zip`: SVG figure, SVG icon assets, and this README.

Use PowerPoint Group > Ungroup to edit individual icon components, shapes, and connectors. Text remains editable within its groups.

## Rebuild

Use the bundled Node.js, Python, and artifact-tool runtimes. First run `scripts/prepare_method_flow_icons_20260924.py`, then `figures/revise_method_flow_20260924.mjs`, `scripts/finalize_method_revised_20260924.py`, and `scripts/validate_method_revised_20260924.mjs`. Set RUNTIME_NODE_MODULES, RUNTIME_PYTHON, SKILL_DIR, and a fresh Windows-local METHOD_DIAGRAM_VALIDATION_DIR. Build intermediates are in `tmp/method-revised-20260924/`.

Export the SVG with Inkscape and a fontconfig configuration including Windows Times New Roman. The original flow directory is never a build output of this revision.
