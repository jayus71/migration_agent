# 方法图 Times New Roman 预览稿

当前交付为保留原图Python / Java语言对照的版本，见文末后续纠正。
中间Python / Python预览保留作历史记录。

日期：2026-09-23。
修改前检查点：`07e0e64`。
用户认为按上一轮建议生成的图不及前一版，并明确要求后续生成指定 Times New Roman。
本轮使用内置 `image_gen`，以前一版用户附件作为构图参考，生成并局部修正位图预览。
未制作 PPT，未替换论文包含的图形。

## 本轮决定

- 统一在生成提示词中指定 Times New Roman，标题使用粗体，说明使用常规体。此要求取代上一轮的无衬线建议。
- 恢复前一版的宽松模块比例、源/目标波形、三项 Orchestrator 职责和简洁仓库示意。
- 撤回将主图展开为数值检查表、细粒度控制流和密集具体例子的设计建议。科学流程核对继续保留，以少量连线表达。
- 保留角色、证据交接、修复历史、两个完整仓库组件名称及两个目标框架。
- 把目标示意改为 Python 与 MindSpore / JAX，修复卡使用移除不必要 detach 的概念示意，接受出口连接验证带。

用户最新批评附件 SHA-256：`1a75362472c180efc1cf6ca2579b4e76a047df9c34036e37080d78eacd55239e`。
构图参考附件 SHA-256：`a83985c7ae8cdd2f9be4153903c780fcd724406587ff4876b9be4a7d53a43a27`。

## 交付与检查

位图预览：`figures/design-drafts/ladim_method_times_new_roman_20260923.png`。
内置工具生成后进行了两次局部修正，分别纠正目标语言/补丁/出口连线及右下角小字。
视觉检查涵盖完整画布、模块对齐、主要标签、目标框架、反馈出口及最终小字。
Times New Roman 已在每一轮提示词中明确指定；位图没有可供核验的字体对象或嵌入字体元数据。
修复代码、波形及尝试记录是机制示意，不是新增实验数据。
最终产物仍是供用户比较的设计预览；没有替换作者的可编辑图形或执行实验。
未变的论文未重新编译，固定基线对照保持。

## 第一轮完整提示词

```text
Use case: infographic-diagram. Create ONE polished academic method overview figure for LaDiM by carefully refining the supplied reference image. Image 1 is the preferred older design and the composition reference. Retain its recognizable overall structure and relatively spacious presentation. The desired result is a research-paper method figure, with restrained flat vector-like artwork, not a software dashboard.

MANDATORY TYPOGRAPHY: Every title, subtitle, label, annotation, file-tree label and code-like text MUST use TIMES NEW ROMAN. Use Times New Roman Bold for module headings and regular Times New Roman for body text. No sans-serif lettering. No Arial, Calibri or rounded UI fonts. Serif letterforms must be visibly clear throughout, including the small text. Render exact English wording legibly.

COMPOSITION: Wide landscape canvas with the same two side towers and three central horizontal tiers as the reference. The upper central tier contains Translator, a wider Verifier Agent, a narrow Evidence handoff, and Repair Agent. The middle tier is a shallow Orchestrator band with three equal action cells. The lower tier is Repository Context Management with three aligned component panels. Keep all three central tiers aligned on their left and right edges. Align top-row module headings, use consistent internal padding and horizontal arrow baselines. Give Verifier the most room, keep the central evidence list narrow, and retain sensible breathing room. Input/output towers are moderate width, not tall cramped slivers. No overall page title.

MAIN TIER:
- Left tower heading "Source program (repository)". Show a small clean source-code card and miniature file tree, plus compact labels "Source language" and "Source framework". A small Python mark is allowed but do not create a wall of repeated logos. Footer "Single file or repository".
- "Translator" with a small outlined robot icon. Subtitle "Translate language and framework". One compact code-document illustration labeled "Initial candidate", with only a few short lines/ellipsis, not a full program listing.
- "Verifier Agent", subtitle "Layered Diagnosis". Two narrow column headers "Source" and "Target". Five evenly spaced rows: "Execution", "Forward values", "Gradients", "Parameter updates", "Next forward". Execution uses simple check symbols. Other rows use delicate schematic waveforms, NOT numerical cells. Forward waveforms agree. Source gradient stays blue, target gradient diverges and is red, with one small red callout "First divergence". Lower downstream observations are light neutral gray. A small unobtrusive vertical guide conveys the order of training computations. Do not add a badge saying Illustrative example, question-mark cells, numeric measurements, path names, file line numbers, or mini legends.
- "Evidence handoff": a slim document with just four readable rows, "Code observations", "Test results", "Code locations", "Hypotheses". Tiny line icons are optional. Do not expand the four rows into separate large nested cards.
- "Repair Agent", subtitle "Revise candidate using evidence". One simple edit-document labeled "Edit candidate", with a red removed-line strip and a green added-line strip; use short abstract code strokes rather than a fabricated specific algorithm or numeric example. A compact "Repair history" below with three stacked slim records and subtle result icons. No invented attempt-specific fixes.
- Right tower heading "Accepted target program (repository)". A small code-document and file tree. Compact "Target language" and "Target framework" labels. Show "MindSpore / JAX" in small Times New Roman text. Bottom short labels "Cross-framework", "Cross-language", "Repository-scale".

ORCHESTRATOR:
Use a pale warm cream band, not a gray dense flowchart. Heading "Orchestrator", short explanation "Coordinate agents and return verification results". Only three equally sized action cells: "Schedule work", "Submit & verify", "Return measurements". Simple arrows between these cells. Do not include a Pass/Fail decision diagram, extra candidate boxes, initial-verification branches, or nested control-flow loops. Show clear short upward connections for measurements to Verifier and for feedback to Repair. A single clean feedback line from Repair's submission to verification and back may be routed in the band margin. The accepted output is reached by a thin outer connector from verification to the right tower; do not draw an unchecked direct Repair-to-accepted shortcut. Do not restore a two-headed Verifier/Repair arc implying both independent agents restart each round.

REPOSITORY TIER:
Pale lavender band with heading "Repository Context Management". Three aligned light panels:
1. "Repository Structural Analysis": a small file tree and a few file/function/import icons; short supporting phrase "Files, imports and symbols".
2. "Repair Dependency Graph Planning": a simple four-node dependency DAG with generous space; short phrase "Arrange work units by dependency". No W1-W5 text-filled task boxes, no legend and no repeated explanatory sentence.
3. "Evidence Retrieval / Context Reconstruction": small flat archive icon, short stack of evidence documents, an arrow into a small context document; short phrase "Retrieve evidence and rebuild context".
Keep these formal module names complete. Use clean mini-diagrams, not tables of features. Connect the support band to the Orchestrator with only two short aligned vertical connectors.

VISUAL FINISH: Pure white page, minimal pastel fills, dark charcoal / dark navy Times New Roman text, muted blue for translation and diagnosis, muted green for repair/output, pale ochre for orchestration, muted lavender for repository support, restrained red only at divergence or edit deletion. Uniform thin borders, subtle small corner radii, crisp fine arrows, no gradients, no shadows, no glow, no 3D, no bright electric-blue UI outlines. Small robot icons consistent in size and line style. Remove excessive boxing within boxes. No dense quantitative or implementation details. Preserve the visual simplicity of the reference. Produce a single high-resolution complete figure, with no cropping and all text comfortably readable.
```

## 第二轮局部修正提示词

```text
Edit this generated LaDiM method diagram with a STRICT LOCAL CORRECTION. Keep the composition, all panel positions and dimensions, colors, icons, waveforms, spacing and TIMES NEW ROMAN typography unchanged. Do not redesign, add panels, or increase detail.

Make only these exact corrections:
1. Rightmost "Accepted target program (repository)" tower: replace the Java logo with a small Python logo and change the word below it from "Java" to "Python". In its code card use ONLY "# target code", "def train():", and "..." on separate lines, all in Times New Roman. Change the miniature tree's "Train.java" to "train.py" and "Utils.java" to "utils.py". Under "Target language", change "Java" to "Python". Keep "Target framework" and "MindSpore / JAX" unchanged. This depicts Python to Python framework migration.
2. Repair Agent edit card: remove the existing "y = model(x)" / "y = model.forward(x)" example completely. Replace the red removed line with "-  h = layer(x).detach()" and the green added line with "+  h = layer(x)". Render these exact characters legibly in Times New Roman, with a small serif annotation "Restore gradient flow" below. This is a schematic illustration of removing an unwanted graph break, not a numerical experiment. No extra code or numbers.
3. Remove the short arrow directly connecting the right edge of Repair Agent to the Accepted target tower. Instead place a single short right-pointing navy arrow from the RIGHT EDGE of the ORCHESTRATOR band to the LEFT EDGE of the target tower, at the vertical level of the Orchestrator action cells. This arrow must clearly originate from the verification band. Keep the other existing arrows unchanged.
4. Fix the text inside the bottom-right context document to read exactly "Reconstructed context for next iteration" in Times New Roman, split onto short readable lines if necessary.

Everything else must stay unchanged. All visible text must retain TIMES NEW ROMAN, including headings, code, file trees and small annotations. Preserve a clean, high-resolution complete image and the white margins.
```

## 第三轮文字修正提示词

```text
Make ONE tiny text correction to this exact diagram. In the small document box at the extreme bottom-right, inside Evidence Retrieval / Context Reconstruction, replace the currently misspelled multi-line text with exactly TWO words on TWO lines:
"Current"
"context"
Use TIMES NEW ROMAN, same dark navy color, comfortably readable. Keep the small document icon above these words. Keep that box's dimensions and position exactly unchanged.

Do not change any other text, shapes, arrows, colors, icons, sizing, margins, or layout anywhere in the image. Preserve every other pixel as closely as possible. This is a local text replacement, not a redesign.
```

## 用户后续纠正：保留 Python / Java 的跨语言对照

用户指出，将右侧 Java 换为 Python 后，图上失去了原有的源/目标语言差异。
此前代理把总览收窄为 Python 的跨框架示例，是对图意的擅自调整。
本轮在检查点 `342b421` 后恢复左侧 Python、右侧 Java，保留 Times New Roman 和其余布局。
右侧语言、代码与文件后缀一并恢复，框架迁移改为独立小分区，避免把 MindSpore / JAX 标为 Java 的运行框架。
这仍是用户要求的总览设计示意，不将示意方向记成新测量的实验。

当前交付预览：`figures/design-drafts/ladim_method_times_new_roman_python_java_20260923.png`。
此前 Python / Python 预览保留作历史版本。
视觉检查确认 Java 标识、Java 代码和文件后缀恢复，源侧 Python、所有中央模块和验证出口保留。
使用内置 `image_gen` 完成局部修改。

### 恢复 Java 的完整提示词

```text
Image 1 is the editable image target. Perform only this local correction on the RIGHTMOST tower. Preserve all other panels, text, linework, waveforms, arrows, colors and layout exactly. ALL text remains TIMES NEW ROMAN, bold Times New Roman headings and regular Times New Roman labels. The user specifically wants source Python and target Java to visually demonstrate cross-language migration. Do not change the left source Python.

RIGHTMOST TOWER CHANGES:
- Keep the heading "Accepted target program (repository)".
- Replace only the rightmost Python logo with the familiar small Java steaming-cup logo, and set its caption to "Java".
- The code card should say "// target code" then "public void train() {" then "..." then "}". Use Times New Roman and fit comfortably.
- In the file tree retain "src/" and "model/", change "train.py" to "Train.java", and "utils.py" to "Utils.java".
- Under "Target language", set the value to "Java".
- Replace the current "Target framework / MindSpore / JAX" block with a visually separate compact inset titled "Framework migration", followed by these TWO small lines: "PyTorch →" and "MindSpore / JAX". Put a thin divider above this inset. This inset lists a SEPARATE framework-migration capability; do NOT label MindSpore/JAX as Java frameworks or place them beneath "Target framework".
- Keep the bottom capability labels "Cross-framework", "Cross-language", "Repository-scale" in their current locations.
- Keep the verification arrow entering the rightmost tower from the Orchestrator unchanged.

No other changes anywhere. In particular keep left source Python/PyTorch, all central components, simple waveform diagnosis, three Orchestrator action cells, repository components and font unchanged. Do not add explanations outside the diagram. Keep the same canvas and all panel boundaries.
```

