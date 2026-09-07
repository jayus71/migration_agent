# 摘要与引言：与 MOST 定稿的差距分析

对比对象：`conference_101719.tex`（LADDER，工作区当前版本） vs `/media/data-vg/data-b/hongbo/lora_merge-paper`
（MOST 定稿，即本目录下的 `main (59)(1).pdf`）。MOST 一侧读的是 `sections/*.tex` 源码
（已过滤 `%` 注释行）。

**本文档只做诊断，未改动 `.tex`。**

> **v2 修订**：第一版基本是按句长统计得出结论的，有两个后果——一是把表征当成了成因，
> 二是 §2.5「三分类命名」那条结论是错的（见 §4）。这一版重写为逻辑分析，句长数据
> 降级为佐证，放在 §5。

> **v3 修订**：v2 把论文的创新点压缩到"有序发现第一个故障"，定位太窄。"多 agent 多
> 反馈"同样不行——multi-agent 不新，审稿人一句话就打回来。这一版重新定位创新点为
> **训练语义的分层诊断设计**，三层：
>
> 1. **洞察**：训练计算有天然的顺序依赖（执行 → 前向值 → 梯度/更新），这条依赖链
>    可以用来做分层验证
> 2. **验证设计**：把训练验证从 pass/fail 一个 bit 分解为三个有序信号，每层对应一类
>    缺陷和一种修复策略
> 3. **操作化**：差分执行 + agent 循环把分层诊断变成可执行的定向修复
>
> 排序是这个设计的关键性质（消融表证实），agent 是实现它的架构，但创新的核心是
> **分层验证设计本身**。下面的修改建议按这个定位调整摘要和引言的论证链。

---

## 0. 结论

问题不在篇幅（摘要 197 词 vs MOST 179，引言 488 vs 483），也不主要在句子长短。
**核心问题是论证链上有两处扣子没扣死：**

1. **摘要里"论点"和"方法"之间断了一格**——第 4 句说关键在反馈的定位精度，第 5 句却
   回答"我们有几个 agent"，没有回答"我们怎么提升定位精度"。
2. **引言的正面主张全程无证据**——Table I 只能证明"单一判定不行"，证不出分层诊断
   有效，而论文里那个把分层设计钉死的消融实验（34/50 不分层 vs 50/50 分层排序），
   引言一个字都没提。

另有一处证据缺口（引言只有人为构造的例子，没有真实迁移数据）。

---

## 1. 摘要：论点与方法之间的扣子断了

### 1.1 MOST 的三句推进

MOST 摘要第 3、4、5 句是**同一件事往前推三格**：

| 句 | 内容 | 作用 |
|---|---|---|
| 3 | Existing methods operate on task updates in a task-agnostic space **without questioning whether it is well-suited** for merging. | 指认盲点：space 没被质疑过 |
| 4 | We argue that **the choice of merging space** is itself a critical but overlooked factor. | 把盲点转成论点：space 是关键因素 |
| 5 | To this end, we introduce MOST, which **optimizes the merging space** by minimizing a novel element-wise overlap objective... | 方法：优化 space |

`space 没被质疑` → `space 是关键因素` → `MOST 优化 space`。同一个名词贯穿三句，每句只往前
推一格，读者读完第 5 句就完整拿到了这篇论文。

### 1.2 LADDER 断在 4→5

| 句 | 内容 | 作用 |
|---|---|---|
| 3 | Existing pipelines validate against a single outcome... **without asking which training stage failed**. | 指认盲点 ✓ 与 MOST 同构 |
| 4 | We argue that repair depends on **how precisely the feedback locates a failure**... | 论点 ✓ |
| 5 | We introduce LADDER, **a three-agent framework in which a translator, a verifier, and a fixer iterate under an orchestrator**. | ✗ 答非所问 |
| 6 | The verifier runs the source and the translation as a pair and **reports the first stage at which they disagree**... | ← 论点的真正回应在这里 |

第 4 句立的论点是**反馈的定位精度**，第 5 句回答的却是**系统由几个模块组成**。
"三个 agent 在 orchestrator 下迭代"这件事，对"如何提升定位精度"这个论点没有任何贡献——
换成两个 agent、五个 agent，论点一样成立。

真正回应论点的是第 6 句（配对执行、报告第一个不一致的阶段）。也就是说**论证链在最关键的
位置插入了一句与论证无关的系统描述**，读者的注意力峰值被消耗在了模块清单上。

这才是"不够有力"的成因。第一版报告说的"峰值句长给了演员表"是这件事的表征：第 5 句不需要
长，因为它不承载论证；第 6 句本该是峰值，因为论证在那里。

**方向**：第 5 句必须直接回答第 4 句。参照 MOST 的 `To this end, we introduce X, which
[做那个关键因素]` 句式——LADDER 的对应写法是"引入 LADDER，它把训练验证按计算的依赖
顺序分解为执行、前向值、梯度与更新三个阶段，每个失败阶段直接命名缺陷类别并指向对应
的修复策略"。这里的关键词是**分层验证设计**，不是"报告第一个不一致"（太窄，只是设计
的一个性质），也不是"三个 agent 在 orchestrator 下迭代"（太泛，multi-agent 不新）。
三个 agent 的分工要么降到后面的短句，要么只留在正文（MOST 的摘要里完全没提自己有
几个模块）。

### 1.3 第 4 句的排他性断言：查过实验设计后，站得住

第 4 句后半句 `not on the power of the repair model` 声称修复模型的能力不是决定因素。
我原本判断这是无对照支撑的过度声称，**核实实验设计后收回这个判断**。§Experimental Setup 写着：

> Every condition runs on the same backbone (`deepseek-v4-flash`), the same decoding temperature
> (0.1), and the same four-attempt budget, and receives the same faulty translation, **so the
> differences reported below come from the feedback rather than from the model or the budget**.

主表本身就是那个对照：模型固定、预算固定、输入固定，只有反馈不同。摘要那半句和这句 setup
是同一个主张的两种说法，**不用删**——这是全文最干净的一条主张。

唯一的措辞注意：严格读，"不取决于模型能力"和"我们报告的差异不来自模型能力"不是一回事
（前者还额外要求换更强的模型也不会追平）。想更稳可以改成 `rather than on the power of
the repair model`，与 setup 句用同一个词。属于可改可不改。

### 1.4 摘要的句级口水

§1.2 诊断的是论证链断裂，但第 5 句答非所问同时也是口水化的最大来源——20 个词给了
演员表，零信息推进论证。除此之外还有几处句级问题：

| 句 | 原文片段 | 问题 |
|---|---|---|
| 1 | `can now translate` | `can now` 是虚词，直接 `translate` 更利落 |
| 5 | `a three-agent framework in which a translator, a verifier, and a fixer iterate under an orchestrator` | 整个从句是演员表，与 §1.2 是同一个病的两个症状 |
| 6 | `runs the source and the translation as a pair` | `as a pair` 多余——"runs X and Y" 已隐含配对 |
| 6 | `the source and the translation` | 后文再指可缩为 `both`，省 4 词 |

**根本原因**：第 5、6、7 句用**三句话做方法**，MOST 只用一句。因为第 5 句被浪费在
架构描述上，真正的方法内容被挤到第 6、7 句还得分两句说。修好 §1.2 之后，方法可以压
到两句：

> **句 5（方法）**：To this end, we introduce LADDER, which decomposes training
> verification into three ordered stages—execution, forward values, and
> gradients—so that the first failing stage names the defect class and the repair
> it requires.
>
> **句 6（操作化）**：The fixer edits at that stage instead of searching the program;
> an orchestrator bounds and rolls back attempts.

这样演员表没了，"as a pair" 没了，方法从三句压到两句，而且第 5 句直接接第 4 句的
"定位精度"。所以**论证链断裂和摘要口水化是同一个病**——修好 §1.2，口水自然被挤掉
大半；剩下的（`can now`、`as a pair`）顺手改掉即可。

---

## 2. 引言：反例是单向的，所以正面主张只能空口说

### 2.1 MOST 的反例做了两件事

MOST 的 P4（反例段）：

1. `This assumption, however, does not always hold.` —— 否定
2. 两个 task update 数学上正交（互不干扰），却在原空间的**每一个坐标上都重叠** —— **反例**
3. `However, a simple rotation reveals a space where each update occupies entirely disjoint
   dimensions, making any subsequent sparsification and merging trivially safe.` —— **同一个
   例子的另一面就是解法**
4. 原参数空间是模型架构的产物，与任务结构没有内在对齐 —— 上升为原理
5. `To validate this empirically, we visualize the element-wise overlap of real LoRA updates
   before and after...` —— 从构造例子走到**真实数据**
6. 旋转后 overlap 大幅下降，且这个下降与合并质量的提升直接相关 —— 真实数据的结论

关键在第 3 步：**同一个图，左半边证明"原空间不行"，右半边证明"旋转后就行"**。所以否定和
正面替代天然在同一段里，不需要另起一段。而且第 3 步里的 "a simple rotation" 已经把 MOST
的方法预告了——读者读到 P5 的 `orthogonal matrices U, V` 时是"对上了"，不是"又来一个新东西"。

### 2.2 LADDER 的 Table I 只做了一件事

LADDER 的 P4：

1. `Training code does not satisfy this assumption.` —— 否定
2. Table I：两个译文，一个正确，一个 backward 从不执行 —— 反例
3. 两个都跑完、都报同样的 loss，所以单一判定会接受一个从不更新参数的程序 —— 反例的结论
4. 这种判定也不说明失败在哪，而不同的失败需要不同的编辑 —— 第二个结论

**到此为止全是否定，没有一个字是正面的。** 于是 P5 只能另起一段从头讲道理：

> Training computation nevertheless imposes an order on what a translation can be asked to
> reproduce. It must first execute, then match the forward values, and finally match its
> gradients and parameter updates. Each stage presupposes the one before it, so the earliest
> stage at which the two executions disagree identifies the class of defect and the repair
> it calls for.

这一段**全程没有证据**，是纯粹的道理推演。而第 3 句（"最早的不一致阶段能识别缺陷类别和
所需修复"）是**全文最核心的主张**——它不只是说"排序"，而是说训练计算的依赖链本身构成了
一个分层诊断结构：每一层对应一类缺陷，因此也对应一种修复策略。这个分层验证设计才是论文
的创新核心。但这个主张被写成一个 `so ...` 从句里的推论，且无任何支撑。

所以第一版报告说的"P4+P5 合并"是不够的——**光合并段落，正面主张还是空口的**。

### 2.3 Table I 能承载什么、不能承载什么

Table I 的下半部分是：

```
Gradient norm      0.2834 | 0.2834 | ---
Parameter update   reference | matches | none
```

这两行**正是第三层信号**。左半边（Runs to completion / Loss）证明"单一判定看不出来"，
右半边已经在演示"分层信号能看出来"——只是正文没有说这后半句，表注也只解释了破折号的含义。

**但要分清 Table I 能证明什么。** 它是一步训练、两个程序，表里**没有"顺序"这个维度**，
所以它结构上不可能证明"排序有用"——它只能证明"一个判定不是充分的反馈单元，三个分层信号
能把这两个程序分开"。而 contribution 3 的主张是更强的：

> the **ordering, not the additional measurement**, is what repairs failures a whole-program
> verdict leaves unresolved.

拿 Table I 去论证这一条，等于在用"多测了两个量"去论证"排序才是关键"，正好是自己要否定的
那一半。

**方向**：P4 里补的那句只认领 Table I 能担的部分——"梯度范数与参数更新这两行把这两个程序
分开了，而单一判定不看这两行"。排序的主张留在合并后的 P4/P5 里作为论断，加一个指向消融的
前指。MOST 也是这么做的：Fig 1 同样证明不了 Riemannian 优化有用。

### 2.4 引言完全没提论文最强的那个结果

顺着上一条查消融时发现的，比原来那几条都重要。

`tab:feedback-ablation` panel (a) 是一个干净的"分层设计 vs 单纯多测量"隔离实验：

| 反馈 | 修复 | 首次成功 | Autodiff/optim 层 | 每次修复 token |
|---|---|---|---|---|
| 只有执行信号 | 33/50 | 58% | 0/4 | 4.7K |
| 三个信号，不排序 | 34/50 | 66% | 0/4 | 5.3K |
| **三个信号，排序（完整分层设计）** | **50/50** | **84%** | **4/4** | **3.8K** |

**多测两个量只多修 1 个（33→34），分层排序多修 16 个（34→50），而且 token 更少。**
这直接证明创新的核心不在"多反馈"（多测量几乎无效），而在**把反馈组织成分层诊断结构**
——按训练计算的依赖顺序排列信号，让每个失败阶段命名缺陷类别。这是全文最有说服力的
一个结果。

而**引言从头到尾没有提到这个实验存在**。P5 讲了一整段"为什么分层有用"的道理，全程
无证据，读者读完只能选择信或不信；但论文里其实有一张表把这件事钉死了。

MOST 的引言在对应位置做了什么：P4 讲完构造反例后，用 `To validate this empirically, we
visualize the element-wise overlap of **real LoRA updates**...` 把真实数据拉进引言，
所以读者进入方法章之前已经被说服了。

**方向**：合并后的 P4/P5 末尾加一句把这个结果前指进来。这一句同时解决三个问题——给
分层诊断设计一个证据锚点、把引言从纯道理推演里拉出来、并且让 contribution 3 有出处。

> 注：`PAPER_ISSUES_20260820.md` 第 7 条记录了 `results_section64_fault_feedback_ablation_v*`
> 五个互相矛盾的目录。但那是 panel (b)（12 任务逐个加信号）的历史中间结果，且该文档写于
> 8-20，当前表里 panel (a) 用的是 50 实例的数据。**引这个数字前建议确认一次 panel (a) 的
> 结果目录**，因为它现在要承担引言的论证重量。

### 2.5 只有构造例子，没有走到真实数据

MOST 的 P4 有一个明确的两段式：**构造的玩具例子（Fig 1a：二维 τ₁, τ₂）→ 真实数据
（Fig 1b：LLaMA3-8B 在 CodeAlpaca/MMLU 上真实 LoRA 的 overlap 热图）**，并用
`To validate this empirically` 显式标记这个跳转。

LADDER 只有构造例子。Table I 的表注自己承认："The right-hand column is a **controlled
instance** of a category observed in real migrations, with the backward pass **suppressed**."
——backward 是人为压制的。引言里没有任何一处出现真实迁移数据。

这在审稿时是个实打实的攻击点：整个引言的动机建立在一个人为构造的例子上。

**方向**：论文别处有 25 个 fault category 的真实统计。引言需要一句把真实数据带进来，
类似"在 N 个真实 MindSpore 迁移失败中，有 M 个属于跑得通但训练行为错误的类别"。
这一句能同时解决 §2.4 的证据缺口和这里的构造性问题。（需要你确认这个数字取得到。）

### 2.6 P1 的定位：问题被讲了三遍

MOST 的 P1 是**背景 → 机会**：适配器多了 → "This naturally raises the question of whether
multiple adapters can be composed into a single model, i.e., the goal of model merging" →
merging 比联合多任务训练更划算。**整段没有提到任何困难**，问题留到 P2 的
"In practice, however, ..." 才引爆。

LADDER 的 P1 是**背景 → 问题**：第一句讲翻译系统进展，第二句就 "Cross-framework migration
of DL training code **raises a stricter problem**"，第三句展开这个问题涉及哪些计算。

后果是三段都在做"问题"这件工作：

| 段 | 做什么 |
|---|---|
| P1 第 2–3 句 | 抽象地说这个问题更难（涉及张量计算、自动微分、优化器状态） |
| P2 中间那句 | 把它具体化成三种失败形态 |
| P4 + Table I | 把其中一种失败形态实证演示一遍 |

同一件事三个抽象层级各讲一遍。MOST 只用一段半。**这就是"啰嗦"最实在的来源**——不是句子长，
是一件事讲了三遍。

**方向**：P1 改成"背景 → 机会"（跨框架迁移训练代码是自然的下一步，且有现实需求），
问题统一到 P2 引爆；P2 的三种失败形态压成一句或直接交给 Table I。

### 2.7 缺一个权威锚点

MOST 的 P2 有一个关键动作：

> To understand when and why merging succeeds, **Ortiz-Jimenez et al. identify weight
> disentanglement** ... **as the key factor** determining merging quality. This insight
> establishes a clear target.

先借别人的权威把"什么是好目标"确立成公认事实，再论证现有方法都没真正达到它。这样 MOST 的
主张是**在公认目标上的定位**，不是自创标准。

LADDER 没有这个动作，"反馈的定位精度是关键"完全是自己立的。

不过要说明：这一条**取决于该领域有没有这样一篇公认文献**。MOST 能这么写是因为
Ortiz-Jimenez 那篇确实是 model merging 领域的公认定性工作。如果 migration repair 领域
没有对等的文献，硬凑一个反而更弱——这条你判断。

---

## 2.8 方法章（§3）的内部重复

前面的诊断集中在摘要和引言。方法章有一个不同类型的问题：**同一个信息在多处重述**，
而不是只在第一次需要的地方出现、后面引用。

#### "阶段 → 缺陷 → 修复"映射出现了五次

| 位置 | 内容 |
|---|---|
| 引言 P5 | "fails to execute → compatibility fix, divergent forward → operator, divergent gradient → differentiation/optimizer" |
| 方法 §3.2 | 用公式 + 文字把 index 1/2/3 各对应什么再说一遍 |
| 方法 §3.3 各信号段 | 每个 `\paragraph` 内部各说一遍这个信号对应什么缺陷 |
| 方法 §3.3 Repair guidance 段 | "Execution failures guide compatibility edits, forward-value failures guide operator-semantics edits..." 第四遍 |
| 方法 §3.4 第一段 | "the fixer edits the translation using the first failing stage and its evidence" 第五遍 |

MOST 不会这么做——它的方法章每一段只推进新信息，引言概括过的东西不在方法章逐句重复。

#### §3.2（What Makes a Diagnosis Useful）开头是元叙述

> Before describing the signals, we state the property the feedback must have.

"在讲 X 之前，我先说一下 Y 需要满足什么性质"——这是作者写给自己的路标，不是写给
读者的内容。直接给出公式和性质即可。

#### §3.3 Repair guidance 段是纯复述

三句话：

1. "The verifier emits the status of each signal, the first failing stage, the
   supporting metrics, and likely repair cues." —— 前面各信号段已经各自说了自己 emit 什么
2. "Execution failures guide compatibility edits, forward-value failures guide
   operator-semantics edits, and gradient and update failures guide backward or
   optimizer edits." —— 第四遍映射
3. "The report turns the signals into an interface between validation and repair
   rather than a collection of independent metrics." —— 概念总结，不带新信息

**整段可以删掉**，或压成一句放在 §3.2 公式之后。

#### §3.4 第一段和引言 P6 几乎是同一段话

引言 P6：
> A translator produces a translation, and a verifier executes it alongside the
> source... A fixer then edits the translation at that stage... An orchestrator
> repeats the cycle...

方法 §3.4：
> A translator produces an initial translation, the verifier compares paired
> source and translated executions, and the fixer edits the translation using the
> first failing stage... An orchestrator controls repair rounds...

**两段只差几个形容词。** 方法章的这一段应该只做引言没做的事——停止规则、rollback
策略、adapter 接口、控制流细节——而不是把循环从头复述一遍。"Figure 1 shows the
iterative repair loop." 之后直接进入引言没有给过的技术细节即可。

#### 另一处小的重复："A translator produces a translation"

这个同义反复在引言 P6 和方法 §3.4 各出现一次。两处都应该删掉或改写——translator
在 contributions 和前文已经定义过了，这里直接说 "The pipeline begins with an initial
translation" 或直接跳过。

**方向**：方法章的修剪原则是**每个信息只在它第一次需要出现的地方出现，后面引用而不是
重述**。具体操作：

1. §3.2 删掉元叙述开头，直接从公式和性质开始
2. §3.3 Repair guidance 段整段删除或压成一句
3. §3.4 第一段只保留 "Figure 1 shows the iterative repair loop."，然后直接进入引言
   没有给过的技术细节（停止规则、rollback、adapter 接口）
4. "A translator produces a translation" 两处都改掉

---

## 3. 上述之外，逻辑上没问题的地方

为避免把"和 MOST 不一样"都当成缺陷，以下几处 LADDER 是对的：

- **P3 三分类的 move 与 MOST 同构**：`Existing systems supply repair feedback in three main
  ways.` → 三类各一句 → `Despite their variety, all three share an implicit assumption that...`
  与 MOST 的 `three main strategies` → 三类 → `Despite their variety, all these strategies
  share a critical implicit assumption:` 逐句对应。
- **盲点句式对**：两边都用"没有问过 X"（`without questioning` / `without asking`）而不是
  "现有方法效果不好"。这个区别很重要——说别人效果差，贡献就是刷分；说别人没问过这个问题，
  贡献就是开辟维度。
- **相关工作换一套名字是对的**，见 §4。

一处小的收束差异：MOST 的共同假设句**回指了三类各自的空间**（"whether the original parameter
space or an SVD-derived subspace"），把三类收拢到一个维度上。LADDER 的假设句
（"one verdict on the whole program is a sufficient unit of repair feedback"）没有回指三类。
可以补，但不是问题。

---

## 4. 更正：三分类命名（第一版此条为错）

第一版说"MOST 引言与相关工作用同一套名字，LADDER 用了两套，是缺陷"。**这是错的**，
第一版是从 PDF 截图读的印象，没查源码。实际情况：

| | MOST 引言 | MOST 相关工作 |
|---|---|---|
| 一 | `Sparsification-based methods` | `\paragraph{Space-agnostic merging.}` |
| 二 | `Subspace-alignment methods` | `\paragraph{Space-aware merging.}` |
| 三 | `Optimization-based methods` | `\paragraph{Interference-aware optimization.}` |

MOST **也是两套名字**。而且这是刻意的：引言按别人**自己的机制**命名（稀疏化 / 子空间对齐 /
优化），相关工作按 **MOST 的卖点轴**重新命名（space-agnostic → space-aware →
interference-aware），并在开头显式声明这次重铸：`We group related work into three categories
**based on their treatment of the merging space**`。

LADDER 做的是同一件事：引言按系统类型命名（Translation pipelines / Repair agents /
Conversion and differential-testing tools），相关工作按反馈方式重铸（outcome-level
validation / search-based fault localization / conversion or single-property comparison），
开头也声明了 `We group related work by **how it obtains repair feedback**`。**结构完全正确，
不需要改。**

唯一可提的细节：MOST 引言三类的名词是平行的（都是 `... methods`），LADDER 是三个不同的名词
（pipelines / agents / tools），平行度稍弱。属于可改可不改。

另外 LADDER 的相关工作是无标题自然段，MOST 用 `\paragraph{}` 加粗小标题——加上标题能让三分类
一眼可见。这是排版问题，不是逻辑问题。

---

## 5. 句长数据（佐证，不是结论）

放在最后，因为它们是上面那些逻辑问题的**表征**，不是独立发现。

```
MOST   摘要:  23 24 18 18 [41] 12 13 14 16     mean 19.9  stdev 8.4
LADDER 摘要:  16 23 20 21  25  28 11 18 [35]   mean 21.9  stdev 6.6

MOST   引言:  mean 19.5  stdev 7.9  (n=24, 483 词)
LADDER 引言:  mean 18.7  stdev 7.1  (n=26, 488 词)
```

- 摘要峰值位置的差异（MOST 在第 5 句方法处，LADDER 在第 9 句数字处）**就是 §1.2 那个断裂
  的读数**：第 5 句不承载论证所以不需要长。修好 §1.2，峰值自然回到第 5 句。
- 引言的句长节奏其实已经和定稿对齐了（18.7/7.1 vs 19.5/7.9）。**引言的问题全在结构和证据，
  不在句子。**
- Contributions 三条 35/33/39 词（MOST 22/19/16），第三条不是实验套语而是塞了跨框架泛化
  ＋排序两件事。注意：排序那半句是有实验支撑的真主张（§2.4），不能当成"该移走的消融结论"，
  要拆的是跨框架那半句。
- 结论章 147 词、最长句 44 词（MOST 73 词、最长 22）。规范要求 70–100 词。

### 摘要里的数字：一处未提交的改动

`git diff --stat` 显示工作区只改了 2 行（第 37 行摘要、第 48 行引言 P2），其余都是已提交的
稳定文本。

- `40982c5`（"Rewrite the abstract and contributions on MOST's logic, **not its numbers**"）
  当时专门去掉了摘要里的数字。
- HEAD（`4428422`, 8-29）的结尾是无数字的两句：`... at a fraction of its token cost.
  The same loop carries over from MindSpore to JAX.`
- 工作区（8-30 15:44，未提交）改成了一句 35 词、含 4 个数字的句子。

**数字留不留我不建议照搬 MOST 的零数字规则**——MOST 是 AAAI 系 ML，LADDER 投 IEEEtran/SE，
SE 摘要带头条数字很常见。这条你定。但如果按 §1.2 重写第 5 句，末句是否放数字就是独立的
一个决定，跟论证链无关了。

---

## 6. 修改清单（按重要性）

**逻辑（必改）**

1. 摘要第 5 句改成直接回应第 4 句的论点（分层验证设计：把训练验证按计算依赖分解为
   三个有序阶段，每层命名缺陷类别与修复策略），agent 分工降级。§1.2
2. 合并后的 P4/P5 末尾加一句前指分层消融（34/50 不分层 → 50/50 分层排序），给
   分层诊断设计一个证据锚点。§2.4
3. 引言 P4 补一句点明 Table I 下半部分——只认领"三个信号能把两个程序分开"，**不要**用它
   论证排序。§2.3
4. P4 + P5 合并，方法回第 5 段。§2.2 / §2.3
5. P1 改成"背景 → 机会"，问题统一到 P2 引爆，消除三层重复。§2.6

**口水与重复（必改）**

6. 摘要第 5–7 句从三句压到两句（见 §1.4 示例），同时清理 `can now`、`as a pair` 等
   废词。与 item 1 同步做——论证链修好后方法自然从三句压到两句。§1.4
7. 方法 §3.3 Repair guidance 段删除或压成一句——"阶段→缺陷→修复"映射的第四遍复述。§2.8
8. 方法 §3.4 第一段只保留 Figure 引用，其余是引言 P6 的复述，删掉，直接进入引言没
   给过的技术细节（停止规则、rollback 策略、adapter 接口）。§2.8
9. 方法 §3.2 删掉 "Before describing the signals, we state the property..." 元叙述
   开头，直接从公式和性质开始。§2.8
10. "A translator produces a translation" 同义反复，引言 P6 和方法 §3.4 各出现一次，
    两处都改掉。§2.8

**证据（建议）**

11. 引言补一句真实迁移数据，解决"动机建立在人为构造例子上"的攻击点。§2.5
12.（需你判断）P2 补权威锚点，如果该领域存在对等的公认文献。§2.7
13. 确认 `tab:feedback-ablation` panel (a) 的结果目录——它要开始承担引言的论证重量。§2.4 注

**格式（顺手）**

14. Contributions 压到 ≤30 词（现 35/33/39，MOST 是 22/19/16）。第三条塞了跨框架泛化
   ＋分层排序两件事，拆开：分层排序那半句是真主张且有实验支撑，留着；跨框架那半句可
   并入第二条。
15. 结论压到 70–100 词，拆掉 44 词那句。
16. 相关工作加 `\paragraph{}` 小标题。

**不用改**

- 三分类在引言和相关工作用两套名字——MOST 也是这么做的。§4
- 摘要第 4 句的 `not on the power of the repair model`——共享 backbone 的实验设计支撑得住。§1.3
