# Editable introduction figure

`repair_cases.pptx` contains one editable slide. The left panel shows two
isomorphic abstract PyTorch and MindSpore networks with every forward edge
preserved. A separate backward return arc contains one red break in the target
network, while the head-side segment remains intact. The short `Missing mapping`
callout refers to the archived operator-mapping mechanism.

The upper-right panel names SWE-agent and MatchFixAgent and summarizes their
code, test, and semantic-analysis feedback workflow. It is a conceptual
comparison of feedback and fault inference, not a measured outcome for I-09.
The lower-right panel shows LaDiM's recorded execution, loss, gradient, and
parameter-update checks. It reports detection, with no claim of successful repair.

## Evidence and design

The builder reads `data/paper_figures/intro_motivation_evidence.json`. The displayed
loss difference is rounded from 4.76837158203125e-7; six upstream parameter tensors
have zero target updates, while the head parameters update as in the source.
The recorded repair outcome is `STOP_NO_PROGRESS`. The missing high-level
GroupNorm mapping and NumPy value-copy fallback come from static tracing of
archived code in [the mechanism review](../docs/natural-translation-cause-review-20260916.md).

[The design record](../docs/intro-figure-design-20260916.md) explains the evidence
boundary and caption. The generated [layout reference](../output/imagegen/intro-layout-reference-v3.png)
and [prompt](../output/imagegen/intro_motivation_prompt.txt) guide the arrangement.
The native reconstruction corrects the generated reference's forward-edge
semantics and makes the two right panels exactly equal in size. No raster
reference is embedded in the PPTX.

## Generation

Run `make_repair_cases.mjs` with the bundled Node.js runtime, then run
`export_repair_cases.ps1` with Windows PowerShell. The JavaScript accepts
`CODEX_ARTIFACT_RUNTIME`, `CODEX_PRESENTATIONS_SKILL`, and `CODEX_REPAIR_BUILD`
overrides. It stages validation on NTFS because the finalizer uses atomic hard
links, which the WSL UNC share does not support.

The exporter opens the single-slide PPTX through Microsoft PowerPoint and saves
`training_repair.pdf` and `training_repair.png`. Text, neurons, forward edges,
backward arcs, marks, borders, and connectors remain native PowerPoint objects.
The PDF retains vectors and selectable text.

## Layout and validation

The canvas is 1056 × 377 CSS pixels (11 × 3.9271 inches), an approximately 2.80:1
aspect ratio. At a manuscript width of 5.5 inches, the smallest text is 8.25 points.
The left panel extends from y=8 to y=369. The two right panels are each 654 × 174
pixels, at y=8 and y=195, with matching 39-pixel title bars and common horizontal
padding. Their combined top and bottom boundaries match the left panel exactly.
The PNG is 1650 × 589 pixels, equivalent to 300 dpi at 5.5 inches wide.

The presentation finalizer passed package integrity, slide geometry, Arial font
policy, and Artifact Tool re-import checks. The delivered slide has 118 native
shapes and 38 connectors, no picture objects, and no media files. `pdfimages -list`
reports no PDF images, and `pdftotext` extracts all labels. Visual inspection of
the PowerPoint PNG and a PDF render at 5.5 inches wide found no text clipping or
unintended overlaps. The result label intentionally uses three lines.

Generation and export use archived measurements and do not run experiments.
