# 数据需求：故障条件下的逐步信号发散轨迹

## 一句话概括

把 6.6 的 50 步逐步对比实验**再跑一遍，但候选侧带故障**，两种参数耦合方式各跑一遍。

现有两份数据各有一半：6.6 有 50 步逐步轨迹但候选是无故障的 oracle（所以全是机器精度）；6.5 有故障注入但只比了第 1 步（所以是单点，画不出曲线）。缺的就是"带故障 × 跑满 50 步"。

---

## 一、这批数据用来干什么

论文的核心主张是三层语义反馈**有序**，即"上一层通过了，下一层才变得可测"，以及"前向层对得上并不能推断下面的层没坏"。

目前这个主张只有两种证据：

- 表 V：布尔检测率，全是 `1.000`。只说明信号响了，**没说离阈值多远**。
- 图 3（已完成）：把每个量除以自己的阈值，展示了幅值分离。但它是聚合单点，**没有时间维度**。

缺的是一条**轨迹**：在训练过程中，某一层什么时候开始发散、另一层是否始终对得上。特别是 `training` 故障那一类——前向和参考一致到机器精度，而参数更新层已经完全发散——这是分层主张最直接的证据，现在只能靠文字断言。

拿到数据后画一张逐步发散图，放进 Analysis 一节。

---

## 二、参照的现有脚本和数据

| 用途 | 路径 |
|---|---|
| 逐步对比逻辑（要复用） | `experiments/paper_section_65_66/run_section66_realdata_training_consistency.py` |
| 现有 600 行逐步数据（列格式照抄） | `experiments/paper_section_65_66/results_realdata_66/section66_realdata_training_consistency_steps_steps50.csv` |
| 现有 36 行故障注入数据（故障语义参照） | `experiments/paper_section_65_66/results_section65_signal_sanity_current/section65_signal_effectiveness_table.csv` |

最省事的做法：在 `run_section66_realdata_training_consistency.py` 上加故障注入和耦合方式两个开关。它的 `_run_torch_model` / `_run_torch4ms_model` / `_compare_steps` 已经把三个量按步算好了，改动量不大。

---

## 三、CSV 列格式

**和现有 600 行那份的 15 列完全一致，只在最前面加两列**：

```
coupling,fault,model,seed,step,torch_status,torch4ms_status,
torch_loss,torch4ms_loss,loss_abs_diff,loss_rel_diff,
torch_grad_norm,torch4ms_grad_norm,grad_norm_abs_diff,grad_norm_rel_diff,
param_update_rel_l2,param_update_cosine
```

新增两列取值：

- `coupling`：`teacher-forced` / `free-running`（见第五节）
- `fault`：`none` / `execution` / `numeric` / `training`（命名和现有 36 行那份一致）

后 15 列的语义、单位、算法都不要改，直接沿用现有实现。`none` 那一组是对照组，作用是确认改动后的脚本在无故障时仍然复现 6.6 的机器精度结果。

空值约定照现有做法：量不存在时留空（现有 36 行数据里 `execution` 故障的三个数值量、`training` 故障的梯度量都是空的），**不要填 0**。0 和"不存在"在这张图里含义完全相反。

---

## 四、实验网格

| 维度 | 取值 | 数量 |
|---|---|---|
| `coupling` | `teacher-forced`, `free-running` | 2 |
| `fault` | `none`, `execution`, `numeric`, `training` | 4 |
| `model` | `cnn`, `nlp`, `transformer`, `tiny_causal_lm` | 4 |
| `seed` | 300, 301, 302（和 6.6 一致） | 3 |
| `step` | **1 到 50，每步都记一行** | 50 |

总计 2 × 4 × 4 × 3 × 50 = **4800 行**。

其余超参照 6.6 的默认值：`--steps 50 --seeds 3 --batch-size 4 --lr 1e-2`，真实数据（CIFAR-10 / AG News）。

阈值也照现有：`loss_abs=0.02`、`grad_norm_abs=0.05`、`param_update_rel_l2=0.03`。

> 模型名沿用 6.6 那份 CSV 里的 `nlp`（不是 `mlp`）。这两个指同一个模型，论文里统一写作 MLP，数据文件保持 `nlp` 不用改。

---

## 五、两种耦合方式（都要跑）

区别只有一处：**每步开始时，候选的参数是不是重置成参考的参数。**

### A. `teacher-forced`（各步独立）

每步开始前，把候选模型的参数覆盖成参考模型在这一步开始时的参数，然后两边各跑一步、比这一步的三个量。

这样 50 步是 50 次独立的单步对比，故障不累积。它回答的是：**这个故障对单独一步的各层信号分别造成什么影响。**语义上和现有 6.5 的表一致，只是重复了 50 步。

预期结果：`training` 故障下前向层 50 步全程一致（机器精度），只有更新层发散。

实现提示：参考侧每步循环开头 `state_dict()` 存一份快照（注意要在 `optimizer.step()` **之前**存，存的是这一步的输入状态），候选侧每步开头 `load_state_dict()` 载入对应快照。

### B. `free-running`（自然跑法）

候选保留自己的参数，正常往下训练，故障效应逐步累积。

它回答的是：**一个在前向层早期看不出来的故障，后面会不会在前向层显现、第几步显现。**

预期结果：`training` 故障下前向层第 1 步一致，之后随着候选参数落后于参考而逐步发散；而更新层第 1 步就已经越过阈值。

### 为什么两种都要

A 证明的是"层与层逻辑上不可互相推断"，B 证明的是"只看前向的检查会漏过、或者要跑很久才发现，而更新层第 1 步就抓到了"。B 对论文的说服力更强（它给的是实用价值），A 和现有表格的语义衔接得上。两条曲线并排放，论证是完整的。

如果只能先出一种，**先跑 B**。

---

## 六、三类故障的语义

都注入在**候选侧（torch4ms）**，参考侧（PyTorch）保持干净。

### `execution`

候选在**第 20 步**抛异常中断（现有 36 行那份用的是 `ControlledExecutionFault: simulated torch4ms runtime/lowering failure`，沿用即可）。

第 20 步及以后 `torch4ms_status=failed`，三个数值量留空；前 19 步正常记录。

> 必须是中间步，不要第 1 步就抛。第 1 步抛的话曲线只有一个点，看不出"前面一直好、这里断掉"这个形态。

### `numeric`

候选前向算错但不崩溃——模拟目标框架某个算子实现不对：能跑完，但值不对。

参照现有数据的量级：`loss_abs_diff` 中位数约 0.49（阈值 0.02），最小 0.027，即每次都明显越过阈值。

一种实现方式：前向前把某个权重张量乘一个小系数（比如 1.05），前向后还原，使故障只作用于前向。具体手段不重要，只要满足"跑得完、前向值错、量级和现有数据相当"。

### `training`（最关键的一类）

候选前向和参考**一致到机器精度**，但参数不更新。

参照现有数据：`loss_abs_diff` ≈ 1e-6、`param_update_rel_l2` = 1.0、`param_update_cosine` = 0.0、梯度量为空。

一种实现方式：`backward()` 之后、`optimizer.step()` 之前把梯度清零，于是这一步没有任何更新发生，梯度量也测不到。

> 这一类是整张图的核心。前向对得上、更新层已经完全发散，正是"上层通过不能推断下层"的直接证据。如果只能保证一类跑对，保这一类。

---

## 七、输出

放在新目录，不要覆盖现有结果：

```
experiments/paper_section_65_66/results_section65_per_step_divergence/
├── section65_per_step_divergence_steps50.csv      # 4800 行，主产物
├── section65_per_step_divergence_raw_steps50.json # 含 started_at / models / seeds / thresholds / 故障参数
└── section65_per_step_divergence_summary_steps50.md
```

`raw json` 里请记上：故障注入的具体手段和参数（比如 numeric 的系数、execution 中断的步号）、两种耦合的实现说明。论文里要交代这些，缺了没法写。

---

## 八、跑完自查

对方交付前跑一下这几条，能挡掉绝大多数问题：

1. **行数**：4800（或按实际网格算的数）。每个 `(coupling, fault, model, seed)` 组合应有 50 行，`execution` 组除外（中断后仍应有行，只是数值列为空）。
2. **对照组复现**：`fault=none` 的两种 coupling 都应该和现有 6.6 结果一致——`loss_abs_diff` 最大约 3.8e-6，`param_update_rel_l2` 最大约 1e-4。**如果对照组不是机器精度，说明改动引入了额外差异，先查这个再看别的。**
3. **`training` + `teacher-forced`**：50 步的 `loss_abs_diff` 应全程 < 1e-5，同时 `param_update_rel_l2` 应全程 ≈ 1.0。这两条同时成立才说明这一类注对了。
4. **`training` + `free-running`**：`loss_abs_diff` 第 1 步应 < 1e-5，之后单调上升。
5. **`numeric`**：`loss_abs_diff` 应稳定 > 0.02（阈值）。
6. **`execution`**：第 20 步起 `torch4ms_status=failed`，数值列为空而**非** 0。
7. **空值**：确认量不存在时是空字符串，没有被 0 或 NaN 填掉。

---

## 九、优先级

全网格跑不动的话，按这个顺序砍：

1. **最小可用**：`fault=training`、`coupling=free-running`、`model=cnn`、1 个种子、50 步 = 50 行。图就能成立。
2. 加 `coupling=teacher-forced`（+50 行），两种耦合的对比就有了。
3. 加 `fault=numeric` 和 `execution`（×3），四类故障齐全。
4. 加满 3 个种子（画置信区间）。
5. 加满 4 个模型（挑最清楚的画，或做跨模型一致性）。

砍模型和种子对图的影响最小，**不要砍 `training` 这一类和 `none` 对照组**。
