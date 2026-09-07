# Zhekai Du 写作风格：来源、测量及自检

日期：2026-09-07。主交付：[Academic-Writing-DNA.md](Academic-Writing-DNA.md)。本记录说明证据出处与局限，不是论文技术正确性审查。

## 语料边界

实际分析目录为 `pdfs/`，共 6 个 PDF。逐篇核对作者栏，Zhekai Du 均列首位；不含此前下载的非第一作者稿件。身份线索为 UESTC 署名、OpenAlex `A5003786587` 与 ORCID `0000-0002-9406-3920`。不据此推断个人写作份额，也不宣称已核实中文姓名或当前职称。

| ID | 论文与本地文件 | 使用版本及公开标识 |
| --- | --- | --- |
| P004 | [Adversarial Energy Disaggregation for Non-intrusive Load Monitoring](pdfs/P004_2021_Adversarial_Energy_Disaggregation_for_Non_intrusive_Load_Monitoring.pdf) | arXiv 2108.01998v1；正式题名 Adversarial Energy Disaggregation，DOI 10.1145/3477301；所持稿仍含 ACM 出版占位符 |
| P006 | [Cross-Domain Gradient Discrepancy Minimization for Unsupervised Domain Adaptation](pdfs/P006_2021_Cross_Domain_Gradient_Discrepancy_Minimization_for_Unsupervised_Domain_Adaptation.pdf) | CVPR 2021 相关稿；arXiv 2106.04151v1；DOI 10.1109/CVPR46437.2021.00393 |
| P021 | [Diffusion-Based Probabilistic Uncertainty Estimation for Active Domain Adaptation](pdfs/P021_2023_Diffusion_Based_Probabilistic_Uncertainty_Estimation_for_Active_Domain_Adaptation.pdf) | NeurIPS 2023 会议重印 PDF；DOI 10.52202/075280-0749；按所持 PDF 计正文到第 10 页 |
| P033 | [Domain-Agnostic Mutual Prompting for Unsupervised Domain Adaptation](pdfs/P033_2024_Domain_Agnostic_Mutual_Prompting_for_Unsupervised_Domain_Adaptation.pdf) | CVPR 2024 相关稿；arXiv 2403.02899v1；DOI 10.1109/CVPR52733.2024.02206 |
| P042 | [LoCA: Location-Aware Cosine Adaptation for Parameter-Efficient Fine-Tuning](pdfs/P042_2025_LoCA_Location_Aware_Cosine_Adaptation_for_Parameter_Efficient_Fine_Tuning.pdf) | 明示 ICLR 2025；arXiv 2502.06820v2；含大量附录，总页数 40 |
| P047 | [Triplet Decomposition and Extensions: A General Framework for Parameter-Efficient Fine-Tuning](pdfs/Triplet_Decomposition_and_Extensions_A_General_Framework_for_Parameter-Efficient_Fine-Tuning.pdf) | 用户本地提供；TPAMI 2026 接收作者版，非完全编辑的最终出版版；DOI 10.1109/TPAMI.2026.3720458 |

TPAMI §1 明示扩展 LoCA，理论与方法有继承关系。因此语言描述统计按 6 篇等权，但“跨论文共有习惯”不能把这两篇重复当成独立研究支持；也未据此做统计显著性推断。

本次没有取得、也没有分析：P007 电池寿命与荷电状态估计；P009 Learning Transferrable and Interpretable Representations for Domain Generalization；P012 Energy-Based Domain Generalization for Face Anti-Spoofing。它们保留在目录清单中，但不参与统计。

## 逐篇证据

以下页码是 PDF 的物理页码，优先通过章节和图表编号定位。观察均指所持版本，不保证与最终出版稿完全一致。

### P004：AED

- 摘要、§1（PDF p.1–4）：从节能应用到 NILM/BSS 的不可辨识性，再把 GAN 的对抗学习改造为共享表示网络和多个判别器。引言不仅提出方法，也预先回应训练成本、推理部署与智能插座的比较。
- §1：三个贡献条目及文章路线图；这种广背景加部署说明比后来的会议论文展开得更多。
- §3：符号、网络结构、对抗目标与实现相连接；Fig.2 是框架、Fig.3 是具体网络。§4 按数据集、实现、结果、分析展开，Fig.4–5 给信号轨迹，Table 4 给消融。
- §5（p.15）：先总结，再承认多个预训练模型的代价；跨家庭和未见电器被列作后续研究，不能当作全部已证实能力；另有隐私和住户知情讨论。
- 视觉核对 p.2：横排电器时序小图解释任务，单栏，图注在下。Fig.1–7，Table 1–4；文献编号连续 1–41。

### P006：CGDM

- §1、Fig.1（p.1–2）：不是泛称域偏移困难，而是指出两个分类器可能一致地分错；代理损失小与目标分类正确之间存在缺口。
- §1：直接硬伪标签可能导致错误扩散；梯度一致性和聚类伪标签各有对应的论证职责。末尾三个贡献条目。
- §3–4：先给目标与训练步骤，后单列理论分析。§5 主结果后安排 t-SNE、收敛趋势、超参数和组件消融（Fig.3–5）。
- §5.3（p.8）：逐类别梯度对齐没有明显增益，因此采用计算更省的整批梯度方案。这是明确报告“不值得增加复杂性”的例子。
- §5.2 的 ImageCLEF 描述说明部分基线未报告随机性，本稿也未报告对应随机性。DNA 不将此做法推荐给新论文。
- 视觉核对 p.1：双栏，右上动机图用颜色/形状区分域与类别，显示错误匹配。Fig.1–5，Table 1–3；文献 1–45。

### P021：DAPM

- §1（p.1–2）：ADA 既有工作更重代表性，确定性输出的不确定性估计仍可能失准；随后对比已有 Dirichlet 建模，解释潜变量不确定性为何也要考虑。
- §3：用 ELBO 串起 VAE、扩散分类器、无标签蒸馏和两阶段训练；§3.4 说明 t-test 选样，而不是只罗列模块名。
- §4.2–4.3（p.8–10）：承认 Office-Home ADA 准确率未必最佳，用 ECE、相同模型上的选择策略比较和标注预算曲线解释贡献所在。讨论采样数量收益饱和及计算/存储代价；承认无主动学习时基础分类表现一般。
- Fig.2 支持校准主张，Fig.3 支持标注预算/敏感性，Fig.4 用选样分布辅助解释；Table 3–4 比较选择策略与组件。结论仅一短段，不机械补出独立 Discussion。
- 视觉核对 p.6：Fig.1 使用跨栏宽度的阶段框、彩色数据路径、冻结说明；实际为单栏。正文 Fig.1–4、Table 1–4；参考文献 1–67。附录不并入正文图表计数。

### P033：DAMP

- §1、Fig.1（p.1–2）：用关闭源监督的诊断，直接检验旧方法是否真正利用源知识。图中 DAPrompt 有/无源监督为 74.5/74.1，DAMP 为 78.2/76.3（Office-Home，ResNet-50）；这里是原文报告，不是本项目结果。
- §1–3：域无关文本提示、实例条件信息、视觉提示分别回应不同问题，互相依赖自然引出 cross-attention，再交代正则项。引言末尾三个贡献。
- §4.3：不仅比较“有无某模块”，还比较独立提示、单向投影及双向交互；Table 4 的策略比较明确移除正则以控制变量。Table 5 展示逐项组件贡献。
- §4.3：token 数量增加后收益饱和，过低置信阈值会伤害性能。原文个别超参数符号和语法有明显笔误，不学习为风格。
- 视觉核对 p.1：双栏，上下两部分直接对比旧/新方法；动机示意嵌入小规模实验数字。正文 Fig.1–5、Table 1–5；参考文献 1–73。

### P042：LoCA

- §1–3（p.1–4）：从 PEFT 分类与低秩约束出发，指出 FourierFT 的经验成功缺少比较解释；随后报告随机位置频域分解在分析条件下可能更差，最优位置选择才形成优势。
- §2–4：分布观察、假设、理论比较、iDCT 等效实现、离散位置梯度构成设计链。主文中的“假设检验不拒绝”不能被新写作升级为对分布假设的证明。
- §5.5（p.9–10）：比较不同参数预算和交替优化策略，解释为何不一直联合更新；承认特定任务可以有不同结果，理论针对期望表现。补充成本在附录，而非把“参数少”当作运行更快的替代证据。
- §6 放在实验后，§7 是短结论；引言未列独立贡献清单。不要强行改写为“三条贡献 + 前置相关工作”。
- 视觉核对 p.3：单栏；Fig.1 三联分布、假设检验、谱密度图，与后续假设/命题同页。正文 Fig.1–4、Table 1–5；主参考文献在 p.11–14，共 71 条；附录从 p.15 起。
- 参考文献用作者年份格式。用 `pdftotext -layout` 按悬挂缩进列出条目首行，再核对四页，计数为 18+18+18+17=71，不依赖只识别数字编号的 skill 脚本。

### P047：LoTA / TPAMI

- §1（p.1–2）：提出两个研究问题，再引入统一分解、可学习正交变换及基选择；列四条贡献；另按理论/方法/实验三个维度说明对 LoCA 的扩展。
- §3–5：先将不同 PEFT 写到统一三元分解中，再提炼变换矩阵和核心矩阵的设计选择；§5 把三个计算困难分别映射到 Householder 参数化、有限差分、交替优化。这是一种清晰的“问题编号对应解法”的组织方法。
- §5.5（p.7）：最终报告的可训练参数仅计后期系数，而早期还优化位置和 Householder 参数。提取风格不等于认定该预算口径可直接迁移；新稿应同时交代阶段、状态和真实资源开销。
- §6（p.8–14）：覆盖多种任务；§6.6 通过收敛/预算曲线、矩阵可视化、案例、Table 8 组件消融解释机制。正文 Table 7 明确报告 LoRA 更快，LoTA 有额外内存代价，权重合并后不增加推理延迟。
- §7（p.14–15）较长讨论扩展到研究方向判断。“PEFT 核心设计空间趋于耗尽”属于该文判断，不应写成公认事实或 Zhekai Du 的恒定立场。
- 视觉核对 p.3：双栏，Fig.1 用同构矩阵示意比较四类方法，图注仅一句。正文 Fig.1–7、Table 1–8；参考文献 1–79。仅当前 17 页文件为语料，不推断缺失的独立补充附件内容。

## 定量口径

### 文件用途

- [corpus_manifest.json](corpus_manifest.json)：6 个 PDF 的相对路径、SHA-256、总页数与全文抽取近似词数；`first_page_author_check` 只是姓名出现检测，第一作者身份另由作者栏人工核对。
- [quantify_raw_pdf.json](quantify_raw_pdf.json)：skill 对原始 PDF 的输出。包含公式、图表、参考文献、页眉和附录，不能直接用来描述正文语言。
- [prose_selection.json](prose_selection.json)：规范化文本中的行范围；按摘要、引言、结论拼接。保留内联公式，去除图文混排、页眉、页脚、单位及贡献列表序号；TPAMI 贡献条目因抽取阅读顺序错位而重新排序。
- [prose_metrics.json](prose_metrics.json)：每节近似英文词数、引文组与条目次数、PDF 和规范化文本哈希。
- [quantify_report.json](quantify_report.json)：skill 对净化散文的语言测量，仅采用语言字段。
- [layout_selection.json](layout_selection.json) 与 [layout_metrics.json](layout_metrics.json)：正文图表/文献人工核对值、六张 Fig.1 的图注行范围与近似词数。

### 语言测量的解释

英文词计数为 `[A-Za-z]+(?:'[A-Za-z]+)?`，不是真实词元数或汉字数。按篇均值 24.37 词/句；各篇范围 19.73–27.59。短/长句比例先在各篇内计算再等权平均。散文总计 6828 词，分篇为 1635、1030、1021、965、809、1368。

第一人称为 `I/we/our/us/my` 正则命中数除以句数；被动代理仅识别部分 be+ed 结构，漏掉不规则分词，也可能匹配形容词。因此不能写成“50% 第一人称句、17% 被动句”。分句对缩写和内联公式仍有误差，统计应辅助阅读，不作身份识别或硬性模仿目标。

已做 Unicode NFKC、断行连字拼接、空白清理，但 PDF 有些单词在抽取时已经粘连，未凭语言直觉大量改写原文。由于当前样本按整节拼接，不提供虚假的段长均值；连接词频率也不作跨体裁唯一指纹。

标点统计采用“每千字符”，不是“每千词”。去引文后的散文几乎无分号/长破折号，冒号主要用于列举；该结果受清理口径影响，不推荐把 0 当成禁用规则。高频领域术语随 NILM/DA/PEFT 变化，未将技术词 Top 10 冒充稳定写作习惯。

### 引文测量

skill 只有识别到 Markdown `# References` 时才计算非零引用密度，其期刊词表偏生物医学。原始 PDF 输出的零引用、零参考文献不能照抄；净化散文本来就移除了引文，也不能用其零值。

补充脚本在移除标记前识别数字引用及作者年份括号组，数字范围展开；每个被引条目的一次出现算一次，重复引用也计数。以去引文后的同节英文词数为分母，分别计算条目和组的密度。作者年份组通过年份识别，本样本中相应年份括号已检查为引用用途。

| ID | 摘要词数 | 引言词数 | 结论词数 | 引文条目/千词 | 引文组/千词 |
| --- | --- | --- | --- | --- | --- |
| P004 | 230 | 1147 | 258 | 20.80 | 12.84 |
| P006 | 195 | 759 | 76 | 15.53 | 8.74 |
| P021 | 214 | 729 | 78 | 29.38 | 18.61 |
| P033 | 191 | 704 | 70 | 27.98 | 12.44 |
| P042 | 194 | 535 | 80 | 33.37 | 17.31 |
| P047 | 213 | 943 | 212 | 19.74 | 19.74 |

没有进行 DOI 级参考文献消歧、所有被引 venue 排名、自引率或引用正确性审计。不能用 skill 白名单的空结果推断未引用计算机会议。

### 图表与套话

skill 只把 Markdown 图片/表格识别为图表，不理解 PDF 图注。主文改用按编号人工核对：图总数 32、表总数 29，均值分别 5.33 和 4.83；均不计附录，子图不拆算。

六篇 Fig.1 的图注近似词数依序 44、26、61、58、57、6，均值 42。只抽样每篇第一张图，不能表述成全部图注均值。图注内少量符号会被英文正则当作词，故保留“近似”标识。已渲染检查的 PDF 页分别为 2、1、6、1、3、3；截图在忽略的 `texts/rendered/`。

原始 quantifier 的 `state-of-the-art` 等命中混有参考文献和模型生成案例。实际散文样本仅命中三类；另在方法/结果正文核对 `facilitates`（LoCA §4、LoTA §5）、`in recent years`（CGDM §3）、`cutting-edge`（LoCA §5.1）。LoCA 附录中 `in conclusion` 出现在展示的模型回答内，已排除出作者语言归纳。套话清单是编辑提醒，不表示所有命中都构成语义错误。

## 复现

在仓库根目录运行，依赖 Python、pypdf、Poppler `pdftotext`；截图另用 `pdftoppm`。原始 PDF 不会被修改，提取文本写入 Git 忽略的 `texts/`。

```bash
python3 literature/zhekai-du/prepare_style_corpus.py
python3 literature/zhekai-du/measure_style.py
python3 /home/jayus71/.codex/skills/academic-writing-dna-skill/scripts/quantify.py literature/zhekai-du/pdfs --no-jieba --output literature/zhekai-du/quantify_raw_pdf.json
python3 /home/jayus71/.codex/skills/academic-writing-dna-skill/scripts/quantify.py literature/zhekai-du/texts/prose --no-jieba --output literature/zhekai-du/quantify_report.json
```

行选择是针对当前 PDF 和抽取结果的人工审阅配置，不是任意新论文的通用解析器。更换 PDF/Poppler 后须对照记录的哈希与选段边界重新核对，不能直接沿用行号。`catalog.json` 中 P047 记为用户提供，不伪造下载地址；保留以前公开下载失败记录作为历史。

## 自检与未验证项

1. **独立试写：完成替代检查，未完成 Claude 盲评。** 按 skill 的独立会话要求，新 Codex 会话只读 DNA，写出约 200 词的假设研究引言，未接触 PDF。见 [TRANSFER-CHECK.md](TRANSFER-CHECK.md)。根会话核对其论证结构和不虚构结果的边界；没有赋予相似度分数。由于平台没有独立 Claude 会话，本次不宣称达到 skill 的盲评 7/10 阈值。
2. **L0：可观察元信息齐全；投稿规范待核查。** 明确区分实有页数、原稿版本和投稿上限，没有捏造最新 venue 规则。
3. **L1：通过来源区分。** 散文中三类套话，以及其他正文中三类措辞有具体来源。排除了模型回答中的 `in conclusion`；没有为凑满五条而把它算作作者用语。
4. **L2：覆盖实际体裁。** 会议、期刊相关稿各有对应结构，综述和学位论文明确无样本；保留 LoCA 无贡献清单、后置相关工作的例外。
5. **L4：完成可复核补充测量。** 条目密度高于 skill 通用 5–15 区间，并不表示这些方法论文变成综述；记录了分母和引文组/条目差异，不强行改数值。
6. **L5：提供完整论证链。** DAPM 的主张、指标、未胜出的情形、回应与有限结论都有章节锚点。
7. **L6：完成编号计数和代表页视觉检查；未核查投稿须知。** 图注均值明确为六张 Fig.1 抽样。没有把 PDF 解析失败的零值作为事实。
8. **长度：主 DNA 少于 5000 字符。** 主结论与可迁移规则留在主文档，长证据和局限在本附件。

不宣称“8 项全部通过”。独立试写反馈指出连接词可能被机械重复、混合诊断研究的模板选择不够清晰；主 DNA 已增加相应说明。精确的段落节奏与作者特异性仍需后续真实写作反馈，不能仅凭一次试写确认。

## 文件与发布范围

Git 中包含写作 DNA、分析记录、试写检查、文献清单、测量结果及语料处理脚本，云端可直接读取。PDF、抽取文本、截图及原始检索响应继续由该目录 `.gitignore` 忽略，仅保留在本地。此次分析与发布未修改研究代码、论文稿件或技能安装目录。
