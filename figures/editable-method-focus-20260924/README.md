# Focused editable method diagram

This revision responds to the layout feedback on the 15:56 method image.
The six upper modules share one top line and one bottom line.
Translator and Repair Agent are compact support modules, while Evidence handoff, the Verifier Agent's layered diagnosis, and Repository Context Management receive the strongest visual emphasis.

The Verifier table ends at `Gradients`; the two rows below the gradient divergence are removed from the Source and Target displays.
The three repository context modules use equal top and bottom edges.

- `method-diagram-editable.pptx`: one slide with native text, paths, boxes, arrows, and editable groups.
- `method-diagram.svg`: the matching vector diagram.
- `method-diagram-vector.pdf`: vector PDF exported from that SVG with embedded Times New Roman fonts.
- `method-diagram-preview.png`: preview rendered after final PPTX validation.
- `icons/`: individual SVG icon assets.

Select a module and use **Group > Ungroup** in PowerPoint to edit its components.
The supplied Python, PyTorch, Java, and MindSpore SVG paths are converted into native vector paths.
The PPTX contains no embedded raster images.

Rebuild with `figures/rebuild_method_focus_20260924.mjs`, `scripts/prepare_method_focus_icons_20260924.py`, `scripts/finalize_method_focus_20260924.py`, and `scripts/validate_method_focus_20260924.mjs` using the bundled presentation runtime.
Intermediates are under `tmp/method-flow-focus-20260924/`.
