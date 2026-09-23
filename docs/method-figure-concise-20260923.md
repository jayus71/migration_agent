# 方法图删减说明文字

日期：2026-09-23。
修改前检查点：`a00280b`。
用户指出图片文字仍然过多，尤其各标题下面都有小字，并质疑是否落实了顶会方法图参考。

本轮重新查看本地 SWE-agent、Self-Refine、PatchPilot、Automated Design of Agentic Systems 四张图片。
参考的是短标签、图形对象及明确关系的组织方式，不将其概括为所有顶会图片均无说明文字。
此前提示词主动要求了多项重复职责句，本轮撤回这些要求。

## 当前预览

`figures/design-drafts/ladim_method_times_new_roman_concise_20260923.png`
SHA-256：`71228ac6b676ce56421415d2209b2e337dc4cd5728ad662392fb7586aedb1835`。
生成方式：内置 `image_gen`，以上一版 Python / Java 预览作编辑目标。
保留 Times New Roman 要求、Python / Java 对照、诊断信号及完整仓库模块名。

主要删减为 Translator/Repair 职责句、Orchestrator/Repository Context Management 总说明、三个动作的括号解释、三个仓库模块的副说明、重复语言字段、能力口号和证据内容重复列表。
Layered Diagnosis、Source/Target、五类信号、First divergence 和证据类型是方法或对象标签，继续保留。
视觉检查确认解释句已删除、主要标题与组件名保留，仓库层用文件树、依赖图和证据文档表达。
图为设计预览，未替换论文图形或生成PPT，没有实验或稿件内容修改。

## 完整提示词

```text
Use case: precise-object-edit for an academic method diagram. The supplied image is the edit target. The user's strongest correction is: TOO MUCH TEXT, especially a small explanatory sentence underneath virtually every title. Remove those explanations decisively. Preserve the existing overall organization, all named method components, Python source and Java target, TIMES NEW ROMAN typography, blue/green/cream/lavender semantic colors, waveform comparison and simple repository mini-diagrams. Make ONE refined figure. Do not introduce new explanatory wording.

TYPOGRAPHY: All visible labels and code must use Times New Roman. Module names in bold Times New Roman, other text in regular Times New Roman. Keep labels comfortably readable. Do not shrink text to fit. Wrap the two longest repository titles onto two balanced lines if needed.

EXACT DELETIONS (remove the text boxes themselves, leave no tiny replacement captions):
- "Translate language and framework"
- "Revise candidate using evidence"
- "Restore gradient flow"
- "Coordinate agents and return verification results"
- "(assign tasks to agents)"
- "(run tests / acceptance checks)"
- "(update results for next iteration)"
- "Support cross-file migration with dependency tracking and evidence management"
- "Files, imports and symbols"
- "Arrange work units by dependency"
- "Retrieve evidence and rebuild context"
- "Source language" and its duplicate "Python" value
- "Source framework" (keep one PyTorch label or logo)
- "Target language" and its duplicate "Java" value
- "Single file or repository"
- The bottom-right three-line promotional list "Cross-framework", "Cross-language", "Repository-scale"
- All source/target/translated-code comments and unnecessary ellipses scattered as decoration.
- "(repository)" beneath the two outer titles.
DO NOT reinsert any deleted sentence anywhere.

CONTENT TO RETAIN, stated as a restrictive text inventory:
1. Left object: title "Source program", small Python logo and ONE "Python" label, compact code "def train():" plus an ellipsis, a small file tree "src/", "model.py", "train.py", and ONE "PyTorch" label. No explanatory prose.
2. Translator: only heading "Translator", small consistent robot icon, one document labeled "Initial candidate" containing short code strokes or "def train():" and an ellipsis. No subtitle under Translator.
3. Verifier: heading "Verifier Agent". Keep the scientific term "Layered Diagnosis" as the title of the waveform comparison itself, aligned with the column labels "Source" and "Target", not as a small sentence under the agent heading. Keep row labels "Execution", "Forward values", "Gradients", "Parameter updates", "Next forward". Checkmarks for execution, matching blue forward traces, blue source gradient versus diverging red target gradient, light gray lower traces. One callout "First divergence". Preserve clean small vertical dependency arrows. No numbers, legends, badges, or descriptive footnotes.
4. Narrow evidence column: heading "Evidence handoff", tiny consistent line icons with just "Code observations", "Test results", "Code locations", "Hypotheses".
5. Repair Agent: only heading "Repair Agent" and a small robot. Keep the small card "Edit candidate" with two short edit lines "- h = layer(x).detach()" and "+ h = layer(x)". Keep "Repair history" with three slim record bars, only numerals 1, 2, 3 and result icons; no "Attempt" repeated and no textual explanation.
6. Right object: heading "Target program", small Java logo and ONE "Java" label, short Java code "public void train() {" followed by ellipsis and closing brace, small tree "src/", "Train.java", "Utils.java". Preserve a visibly separate compact "Framework migration" inset containing "PyTorch → MindSpore / JAX", broken onto readable short lines. It represents another migration dimension, not the Java framework. No other small labels.
7. Middle control band: only "Orchestrator" and three equally spaced action labels with simple line icons: "Schedule work", "Submit & verify", "Return measurements". NO subtitles, NO parentheses, NO explanations, NO pass/fail branching. Reduce this band's height substantially after removing explanation rows. Use modest arrows and light separators instead of thick nested card borders. Preserve the verification exit toward the right target tower and the short feedback connections.
8. Bottom shared band: heading "Repository Context Management" ONLY, with no sentence to its right. Three aligned panels have these full titles: "Repository Structural Analysis", "Repair Dependency Graph Planning", "Evidence Retrieval / Context Reconstruction".
   - First panel: small file tree and linked document/symbol icons. Use minimal file labels; remove the redundant Functions / Classes / Imports legend.
   - Second panel: simple four-node dependency DAG; no explanation beneath title, no legends.
   - Third panel: small archive, evidence-sheet icons and arrow to document labeled "Context". Remove the repeated list of Code snippets / Test results / Error logs / Hypotheses because the evidence column already names its contents.

SPACING: After deleting text, close the resulting gaps and rebalance the SAME composition. Move graphics nearer their headings. Reduce the total figure height rather than leaving empty strips where captions were. Keep all central bands the same left/right boundaries, consistent heading baselines and generous but controlled whitespace. Slightly enlarge the remaining meaningful diagrams within their panels. Outer source and target objects stay balanced. Avoid a dashboard feel: thin uniform outlines, clean flat fills, no shadows/glow/gradients, few nested frames. No overall slide title, no additional caption or footer. The final image must contain no long explanatory sentences anywhere. The ONLY text allowed is the restrictive inventory above and minimal code/file labels. Produce one complete, sharp, uncropped figure.
```

