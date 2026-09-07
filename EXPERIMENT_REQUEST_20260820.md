# 实验请求：Bug 修复与补充实验

| 项目 | 值 |
|---|---|
| 日期 | 2026-08-20 |
| 对应仓库 | `gitee.com/feixiao13/ascend-torch4ms`，分支 `codex/llm-fixer-capability` |
| 对应论文 | `conference_101719.tex` |
| 依据 | 对已交付数据与代码的逐条核验，所有结论附 `文件:行号`，可自行复核 |

## 这份文档怎么读

第一部分是 **5 个 bug**，其中 3 个会让论文里的数字站不住，必须修。→ 给写代码的同学

第二部分是 **11 项实验**，每项写明「论文哪个主张需要它 / 现在缺什么 / 怎么跑 / 怎么验证跑对了」。→ 给跑实验的同学

第三部分是 **7 张图**。图放在最后，因为图是数据的结果而不是目的——先确认数据，图自然就有了。每张图注明依赖哪项实验，以及现在为什么画不出来。其中**图 1、图 2、图 4 不需要任何新实验**。

**行号说明**：所有 `文件:行号` 都已在 `codex/llm-fixer-capability` 分支 HEAD（`f3c84bb`）上逐条复核过，可直接定位。

**本机环境说明**：论文侧这台机器三个 conda env 全都没有 MindSpore，`import torch4ms` 直接失败；CIFAR-10 / AG News 也不在本地。已交付数据的 `data_checks` 路径是 `/media/main/whj/projects/torch4ms/...`，说明实验是在另一台机器上跑的。**所有实验都需要在那台机器上执行**，论文侧只能做数据核验和画图。

---

# 第一部分：需要修复的 Bug

按严重程度排。前三个直接影响论文数字。

## Bug 1（严重）：T-MSA 的损失函数被改写，导致它永远不可能通过

**位置**：`experiments/baselines/track_a/T-MSA/run_t_msa.py:42-58`（`MSA_IMPORT_BLOCK` 起于 `:42`，替身类 `:49-56`，覆盖赋值 `:58`）

脚本往候选源码里注入一个 `nn.CrossEntropyLoss` 替身类：

```python
class _MSAStableCrossEntropyLoss(_MSA_ORIGINAL_CROSS_ENTROPY_LOSS):
    def __init__(self, *args, **kwargs):
        if "reduction" not in kwargs:
            kwargs["reduction"] = "sum"
        elif kwargs["reduction"] == "mean":     # 显式要求 mean 也被改成 sum
            kwargs["reduction"] = "sum"
        super().__init__(*args, **kwargs)

nn.CrossEntropyLoss = _MSAStableCrossEntropyLoss
```

**后果**：`sum` 与 `mean` 相差一个 batch size 倍数，候选 loss 必然与参考差数倍，`loss_ok` 判定必然失败。**T-MSA 报的 `0.0%` 是这行代码的产物，不是 MSAdapter 的能力。**

**怎么改**：删除该替身，使用 MSAdapter 原生 `nn.CrossEntropyLoss`。若原生实现确有数值不稳定问题（类名 `Stable` 暗示了这个动机），应作为一条 finding 记录并在论文中披露，而不是静默改写后报告它失败。

**怎么验证**：重跑后检查 `last_step_abs_loss_diff` 是否落在 `0.02` 量级附近，而非 batch size 的倍数。

## Bug 2（严重）：MindSpore 候选的 strict 判定永远不可能通过

**位置**：`experiments/baselines/track_a/T-DIRECT/verify_t_direct_candidate.py:312`

MindSpore 分支把梯度范数写死为 `None`，PyTorch 分支（`:411`）才真算：

```python
result["_grad_norm"] = None          # :312  MindSpore 分支
result["_grad_norm"] = _torch_grad_norm(model)   # :411  PyTorch 分支
```

而判定链要求它非 `None`：

```python
# :468-469  只有两边都有值才算这个差
if ref.get("grad_norm") is not None and cand_grad is not None:
    comparison["last_step_abs_grad_norm_diff"] = abs(...)
# :479  差值为 None 则 grad_ok 恒为 False
grad_ok = comparison["last_step_abs_grad_norm_diff"] is not None and ... <= GRAD_NORM_ABS_THRESHOLD
# :481  三者相与
result["translation_success_at_1"] = bool(loss_ok and grad_ok and param_ok)
```

**后果**：任何 MindSpore 后端的候选，`grad_ok` 恒为 `False`，strict 永远过不了。**T-MSA 与 T-X2MS 的 `0.0%` 是构造出来的**。这两个 baseline 连"有没有可能通过"都没被测过。

**怎么改**：在 MindSpore 分支实现真实的梯度范数读取。若目标框架确实无法暴露梯度范数，则该指标应记为"不可测"并在报告中显式区分，不能与"测了但不达标"合并成同一个 `False`。

**怎么验证**：修改后 T-MSA / T-X2MS 的 `strict_success` 应当不再是 `0.0%`；若仍为 0，检查 `errors["strict_metrics"]` 里三个数值各是多少，确认是真的不达标。

## Bug 3（严重）：候选与参考用不同学习率训练

**位置**：`experiments/baselines/track_a/T-DIRECT/verify_t_direct_candidate.py`

候选侧六处写死 `lr=1e-3`（`:301, 303, 388, 390, 398, 400`），参考侧读任务特定学习率（`:427`）：

```python
lr = float(TASKS[task].get("lr", 1e-3))   # :427  参考侧
```

而 `TASKS`（`:20-24`）里 `image_mlp` 是 `2e-3`、`resnet` 是 `8e-4`。

**后果**：五个任务里有两个，候选与参考用不同学习率训练。**即使翻译完全正确，参数更新也不可能等价**，`param_ok` 必然失败。

**怎么改**：候选侧统一改成读 `TASKS[task]["lr"]`，与参考侧一致。

**怎么验证**：`image_mlp` 和 `resnet` 两个任务的 `param_update_rel_l2` 应显著下降。

## Bug 4（中等）：Table I 的验收判据与论文描述不一致

**论文原话**（`conference_101719.tex:150`）：

> A repair counts as verified only when the patched candidate passes all three checks **against the source execution** … holds Δloss≤0.02, Δgrad≤0.05, Δparam≤0.03 **at every checked step**

**实际代码**：判定 `ok` 的是每类故障各自的 probe，三个阈值（`0.02/0.05/0.03`）在 `autofix/faults/` 下**任何 probe 里都没有出现过**。实际判据：

| 故障类 | 实例数 | 实际 `ok` 判据 | 与参考比？ |
|---|---|---|---|
| execution | 20 | 形状 / dtype / `isfinite` / `value > 0` | 否 |
| numerical | 14 | `max_abs_diff <= 1e-6`（`controlled_cases.py:424`） | **是**，且比 0.02 严得多 |
| gradient_update | 16 | 参数名单匹配 + 冻结参数无梯度 + 首个可训练参数有梯度（`core_gradient_mapping.py:82-87`） | **否** |

注意偏差不是单向的：numerical 比论文写的**更严**，gradient_update 比论文写的**更松**。

**两条路选一条**：

- **(a) 补验收**：结构检查留作诊断，另加一道成对阈值验收。**验收函数已经写好了**——`experiments/paper_section_65_66/run_section66_realdata_training_consistency.py:294` 的 `_strict_pass()`，逐步查三个阈值、任一缺失即失败，正是论文描述的东西。接上即可，不用重写。→ 见实验 A。
- **(b) 改论文**：把 `:150` 改成实际判据的描述。零成本，但论文的验收强度弱于现在的说法。

**建议选 (a)**，因为 (b) 会削弱论文最核心的方法论主张。

## Bug 5（轻微，但需在论文中澄清）：外部方法的分阶段状态是合成的

**位置**：`autofix/examples/run_external_repair_pilot.py:360-367`

```python
def _stage_status(fault_type: str, passed: bool) -> dict[str, Any]:
    return {
        "compile_status":   "pass",                                                   # 恒为 pass，从不检测
        "execution_status": "pass" if passed or fault_type != "execution" else "fail",
        "numerical_status": "pass" if passed or fault_type != "numerical" else "fail",
        "gradient_status":  "pass" if passed or fault_type != "gradient_update" else "fail",
        "update_status":    "pass" if passed or fault_type != "gradient_update" else "fail",
    }
```

输入只有「注入的是哪类故障」和「整体过没过」两个值，输出五个状态列。`compile_status` 恒为 `pass`。其余四列：整体过了就全 `pass`；整体没过，只有与注入故障同类的那列写 `fail`，另外三列**仍写 `pass`**。

**举例**：一个 gradient/update 故障修完没过，记录为「编译 pass、执行 pass、数值 pass、梯度 fail、更新 fail」。其中"执行 pass"和"数值 pass"没有任何检测支撑。

**说明**：内部方法（含 LADDER）也是同一个 probe 布尔值按故障层聚合，**所以这不是对外部方法的区别对待**，六个方法记账方式一致，横向比较仍然公平。

**后果**：Table I 的 `Exec. / Num. / Grad./upd.` 三列容易被读成"分别测了三层"，实际是"按注入故障类型分组的实例计数"。表脚注已写 "Stage denominators are 20 execution, 14 numerical, and 16 gradient/update instances"，但列名仍有误导性。

**怎么改**：要么实测每阶段（成本高），要么在正文明确这三列是按故障类型分组的实例计数。实验 A 做完后，这三列可以变成真正实测的。

---

# 第二部分：需要跑的实验

按优先级排。每项列出「论文哪个主张需要它」，因为没有对应主张的实验不值得跑。

## 优先级总览

11 项。A–F 是原有的（D、F 目标有调整），G–K 是新增的。

| | 实验 | 服务的论文主张 | 需要 LLM | 依赖 |
|---|---|---|---|---|
| **A** | Table I 成对阈值重验 | RQ1 验收口径与论文一致 | **不需要** | Bug 4 |
| **B** | 故障池 50 → 60 实例 | RQ1 规模 | 需要 | — |
| **C** | 梯度算错的故障（新增故障类型） | **Introduction 的问题陈述** | 不需要 | 需改代码 |
| **D** | 真实学习动力学下的特异性（原「加 batch 加步数」，目标已换） | 阈值不是在静止轨迹上校准的 | 不需要 | — |
| **E** | Track A 修 bug 后重跑 | 新增一张翻译工具对比表 | 部分需要 | Bug 1/2/3 |
| **F** | ~~真实数据集扩充~~ **已并入 D 和 I** | — | — | — |
| **G** | **多故障实例（一个候选 2–3 个故障）** | 打破 100% 天花板 | 需要 | — |
| **H** | **换 LLM 重跑主表 + 3 seeds** | 机制跨模型成立；论文可复现 | 需要 | — |
| **I** | **真实翻译产物端到端（不注入故障）** | 外部效度，挡住「种 bug 实验」 | 需要 | — |
| **J** | **反馈粒度消融 + 反序条件** | RQ2 拆开「信号存在」与「信号多具体」 | 需要 | — |
| **K** | **补 `predicted_layer` 日志字段后重跑** | 定位准确性——baseline 产不出的证据 | 需要 | 需改代码 |

**离线包（零机器成本，今天就能做）**：特异性 2×2、阈值敏感性、验证开销 = 1 步。三项都只用已交付的 4800 行数据重分析，不需要跑任何东西。数字见文末附录，已经算好了。

**如果只能跑四项：K、G、I、H。**

- **K** 是唯一 baseline 结构上产不出的证据（我们能说出故障在哪一层，它们只能说"没修好"），成本最低
- **G** 是打破天花板最便宜的手段——现在 LADDER 50/50、JAX 6/6，满分意味着所有对比和统计检验都失去信息量
- **I** 挡住最硬的那一击：50 个实例是往已知正确实现里注入故障，不是真实翻译产物
- **H** 顺带解决论文从不点名 LLM 这个可复现性缺陷（实际用的是 `deepseek-v4-flash`）

**为什么天花板是真问题**：LADDER 50/50 vs MatchFixAgent 47/50，配对检验只有 3 个不一致对，精确检验双侧 p=0.25——统计上什么都证明不了。同理 Table III 的 12/12 vs 8/12 是 4 个不一致对，双侧 p=0.125。**先把池子做难，统计检验才有意义。** 在那之前，建议正文以 Repair@1（84.0%）为头条指标，Repair@4 退居次要，这是零成本的立即改善。

---

## 实验 A：Table I 成对阈值重验（不需要 LLM，优先做）

### 论文主张

`:150`「三个检查全过、逐步成立」才算 verified。目前实际判据见 Bug 4，与此不符。

### 现在缺什么

一道成对阈值验收。**修复过程已经完整存盘，所以不需要重新调 LLM**：

- 外部三个方法（`r_direct` / `r_swe` / `r_matchfix`）：各 50 个 `.py` 候选文件，在 `experiments/baselines/full_hier_fixed50/<baseline>/candidates/`
- 内部三个方法（`r_exec` / `r_flat` / `r_hier`）：各 50 个子目录，每个装 `attempt_NN.json`，内含完整补丁：

```json
{"action": "replace",
 "find_text":    "def boundary_op(x):\n    return x + 1.0",
 "replace_text": "def boundary_op(x):\n    return TorchLikeTensor(x + 1.0)",
 "applied": true}
```

### 怎么跑

1. 对六个方法 × 50 实例，把存盘的 edit 重新应用到干净的候选上
2. 跑一次成对训练对比（参考 PyTorch vs 修复后候选），逐步记录 `loss_abs_diff` / `grad_norm_abs_diff` / `param_update_rel_l2`
3. 用 `_strict_pass()`（`run_section66_realdata_training_consistency.py:294`）判定，**不要重新实现判据**
4. 输出与现有 `summary.csv` 同格式，另加一列 `strict_success_paired` 以便对比

### 成本

token 接近零。时间 = 300 次（6 方法 × 50 实例）成对训练验证。

### 验证跑对了

- **每个实例都要有三个数值**，不能有 `None`（除非候选真的崩了，那种情况 `torch4ms_status=failed`）
- `fault=none` 的对照（若有）应落在机器精度
- 与现有 `strict_success` 逐实例对比，输出一张差异表：**哪些实例原来记成功、重验后失败**。这张差异表是这个实验最重要的产物

### 预期结果

**数字可能会掉。** 现在"改到能跑但数算错"记成功，重验后会记失败。哪个方法掉得多不好预测——这正是要测的东西。请如实报告，不要因为数字变差就回退。

---

## 实验 B：故障池 50 → 60 实例

### 论文主张

RQ1 的规模。目前 50 实例 / 25 类，是论文最容易被质疑规模的地方。

### 现在缺什么

`autofix/faults/registry.py` 里有个 `EXTRA_FAULTS`，5 个故障**已实现但没进论文池**：

| ID | runner | 说明 |
|---|---|---|
| `UP-01` | `candidate_training` | 已实现，有测试覆盖 |
| `MX-01` | `candidate_training` | 已实现 |
| `MX-02` | `candidate_training` | 已实现 |
| `BL-01` | `candidate_training` | `MX-01` 的 low-hint 变体 |
| `BL-02` | `candidate_training` | `MX-02` 的 low-hint 变体 |

五个全在 `EXTRA_FAULTS`（`registry.py:312`），全是 `status="implemented"`，全在 `candidate_training.CASES`（`candidate_training.py:17`）里，而 `runner.py:115` 的派发链第一个判断就是这个集合，**所以不需要新增路由代码**。测试覆盖见 `test/test_autofix_phase1.py:3617`（`extra_faults()` 含 BL-01/BL-02）、`:3700-3713`（GR-01/UP-01 的修复流程）。

### 怎么跑

1. 在 `run_section65_real_fault_repair.py:40-66` 的 `FAULT_MODEL_PAIRS` 里加 5 行，为每个故障指定两个模型
2. **必须同时补 `LAYER_LABELS`（`:68-72`）**——它目前只映射 `EX`/`NU`/`GR`，`UP`/`MX`/`BL` 前缀会导致聚合出错
3. `fixed50_instances()`（`:182-195`）会自动生成 A/B 实例，无需改动
4. 注意 `mixed` 是 `FaultLayer` 的合法取值（`registry.py:7`），但现有聚合列没有建模它——若 `MX` 归到 `mixed` 层，聚合逻辑要一并处理
5. 六个方法全跑，保持与现有 Table I 同配置（`--real-llm --blind --repair-attempts 4`）

### 成本

这是**唯一需要大量 LLM 调用**的实验。参考现有消耗：SWE-agent 7.6M token、MatchFixAgent 5.2M token（50 实例）。加 10 实例约按比例增加 20%。

### 验证跑对了

- 60 实例 / 30 类，每类 2 个实例
- 分层计数要和新的 `LAYER_LABELS` 对得上，总数守恒
- 现有 50 个实例的结果应与旧跑分**大致一致**（同配置、同代码）。若差异显著，说明改动引入了副作用，先查这个

### 备注

仓库里还有一个现成的故障实例：`experiments/llm_tiny_smoke/` 下两个脚本的 diff 是**一行位置差**（梯度范数记录挪到了 `optimizer.step()` 前后）。这是个典型的 GR 族故障，可以考虑收进池子，但需要先包装成标准 FaultSpec。

---

## 实验 C：梯度算错的故障（新增故障类型，服务论文的问题陈述）

论文 Introduction 明确写了三种失效模式，目前只有两种有数据。**缺的那一种正好是论文最想强调的那一种。**

### 论文主张

`conference_101719.tex:40` 原话（这是论文的问题陈述核心）：

> A translated training script may run successfully while producing **different logits or losses**. It may **match the forward computation but propagate incorrect gradients**, or **compute plausible gradients while updating a different parameter set**.

三种失效模式，对照现有数据：

| 论文说的失效模式 | 现有故障类型 | 有数据吗 |
|---|---|---|
| 跑得通但 logits/loss 不对 | `numeric` | ✅ 有 |
| **前向对得上但梯度算错** | **无** | ❌ **完全没有** |
| 梯度看着合理但更新了错的参数 | `training`（部分对应） | ⚠️ 只是"不更新"，不是"更新错的" |

### 现在缺什么

逐步发散实验只支持四种故障（`run_section66_realdata_training_consistency.py:56`）：

```python
DIVERGENCE_FAULTS = ("none", "execution", "numeric", "training")
```

而 `training` 故障的定义是**跳过 backward**（`:198-213`）：

```python
if fault == "training":
    # forward is valid, but backward/update is absent and gradients are not measurable
    after = clone_named_params(model)
    steps.append({..., "grad_norm": None, ...})
    continue          # <-- loss.backward() 从来没执行
```

所以在这类故障下**梯度不是"没测到"，而是被设计成不存在**（CSV 里 1200 行梯度列全空）。它永远给不出"前向对得上、梯度算出来是错的"这个证据——那是论文问题陈述的第二条，也是三条里最能体现"分层检查必要性"的一条。

**请求方之前那份 `DATA_REQUEST_per_step_divergence.md` 要错了故障类型**，这不是执行方的问题。

### 怎么跑

在 `DIVERGENCE_FAULTS` 里新增两种故障，都注入在候选侧：

**`grad_wrong`（对应论文第二条失效模式）**：backward 照跑，梯度算完后、`optimizer.step()` 之前，把梯度按一个固定系数缩放（例如 ×1.5），或对某一层的梯度取反。

```python
# 位置：run_section66_realdata_training_consistency.py:214 附近
loss.backward(module=model)
if fault == "grad_wrong":
    for p in model.parameters():
        if p.grad is not None:
            p.grad.mul_(GRAD_WRONG_SCALE)     # 建议 1.5，见下方量级要求
grad_norm = grad_global_norm(model)           # 注意：要在缩放【之后】测，才能记录到错误的梯度
optimizer.step()
```

**关键**：`grad_global_norm` 必须在缩放**之后**调用，这样 `torch4ms_grad_norm` 记录的是错误的梯度值，才有数可比。这是这个故障与 `training` 的本质区别——**梯度存在且可测，只是不对**。

**`param_wrong`（对应论文第三条失效模式）**：梯度完全正确，但 `optimizer.step()` 更新到错的参数子集上（例如只更新一半参数，或把两个参数的更新对调）。这直接对应论文说的 "compute plausible gradients while updating a different parameter set"。

### 量级要求

| 量 | 阈值 | `grad_wrong` 期望 | `param_wrong` 期望 |
|---|---|---|---|
| `loss_abs_diff` | 0.02 | teacher-forced 下 **< 1e-5**（前向必须对得上） | **< 1e-5** |
| `grad_norm_abs_diff` | 0.05 | **稳定 > 0.05**（这是关键，必须有数且越阈） | **< 1e-6**（梯度是对的） |
| `param_update_rel_l2` | 0.03 | > 0.03 | **稳定 > 0.03** |

`grad_wrong` 的缩放系数请先小规模试，目标是 `grad_norm_abs_diff` 稳定落在 0.05～0.5 之间——太小越不过阈值，太大则 loss 也会被带偏、破坏"前向对得上"。建议从 1.5 起试。

### 网格

与现有逐步发散实验一致，便于合并：

```
coupling: teacher-forced, free-running   (2)
fault:    none, grad_wrong, param_wrong  (3)
model:    cnn, nlp, transformer, tiny_causal_lm  (4)
seed:     300, 301, 302                  (3)
step:     1..50                          (50)
```

= 1800 行。CSV 列格式与现有 `section65_per_step_divergence_steps50.csv` 完全一致（17 列）。

### 验证跑对了

**`grad_wrong` + `teacher-forced` 是这个实验的核心，三条必须同时成立**：

1. `loss_abs_diff` 全程 < 1e-5 —— 前向对得上
2. `grad_norm_abs_diff` **全程有值且 > 0.05** —— 梯度可测且是错的（**不能是空值**，这是与 `training` 故障的关键区别）
3. `param_update_rel_l2` > 0.03 —— 更新层也受影响

**`param_wrong` + `teacher-forced`**：`loss_abs_diff` < 1e-5 且 `grad_norm_abs_diff` < 1e-6 且 `param_update_rel_l2` > 0.03。这一条最难注对，因为要保证梯度完全正确而只有更新错。

### 为什么这项最重要

它是论文问题陈述里唯一没有数据支撑的失效模式，而且恰好是最能说明"为什么需要分层检查"的一种——前向和梯度**都能测到数**，但一个对一个错。相比之下 `training` 故障给的是"梯度测不到"，说服力弱得多。

---

## 实验 D：真实学习动力学下的特异性（原「加 batch、加步数」，目标已换）

### 论文主张

`:152` 用干净候选的一致性论证「所有报告的差异都来自迁移而非测量」：max Δloss = 3.815e-6、Δgrad < 4e-8、Δparam < 3.9e-6。离线重算确认了这三个数字，而且余量极大（见文末附录）。

**但这个证据有一个漏洞**：四个模型里三个在 50 步内几乎没有学习（参考 loss 只移动 0.0025–0.0188）。在一个近乎静止的系统上测出 3.8e-6 的干净漂移是可预期的，所以「阈值体系是在静态轨迹上校准的」这个质疑站得住。这项实验就是去堵这个漏洞。

### 现在缺什么

两个统计问题，都指向同一件事——现有配置下系统没真的在训练：

**问题 1：batch=4 的采样噪声超过了检测阈值。**

在 `free-running` + `training` 故障下候选参数被冻结，其 loss 变化全部来自 minibatch 抽样。实测噪声地板：

| 模型 | 候选 loss 标准差 | 峰谷差 | 相对阈值 0.02 |
|---|---|---|---|
| cnn | 0.00705 | 0.03332 | **1.7 倍** |
| nlp | 0.00788 | 0.04008 | **2.0 倍** |
| transformer | 0.00417 | 0.01886 | 0.9 倍 |
| tiny_causal_lm | 0.00233 | 0.01040 | 0.5 倍 |

cnn 和 nlp 的**纯采样噪声就能越过 0.02**。所以现有数据里 cnn（seed 301，1/50 步）和 transformer（seed 302，2/50 步）那两次"越阈"**很可能是噪声而非信号**。

**问题 2：50 步内参考侧自己走得不够远。**

`free-running` 下候选被冻结，所以 `loss_abs_diff` 的上限就是参考侧自己移动的距离：

| 模型 | 参考 step1 → step50 | 50 步总位移 | 能越过 0.02 吗 |
|---|---|---|---|
| cnn | 1.7831 → 1.8018 | +0.0188 | 勉强 |
| nlp | 1.6030 → 1.6003 | **−0.0027** | 不可能 |
| transformer | 1.0930 → 1.0955 | +0.0025 | 不可能 |
| tiny_causal_lm | 4.4038 → 4.1913 | **−0.2125** | 可以 |

三个模型 50 步里参考只走 0.0025–0.0188，其中两个还是往反方向走的。**算术上就不可能产生超过 0.02 的前向差异**，与故障注入是否正确无关。

按后 10 步的速度线性外推，参考侧位移到 0.02 需要：cnn 约 51 步、transformer 约 66 步、nlp 约 140 步。

### 怎么跑

分两步，第二步顺带把原实验 F（真实数据集）一起交付。

**第 1 步：定参数（小规模试探，不要直接上全网格）**

固定 `fault=none`（这次的主角是干净候选，不是故障）、`coupling=free-running`、1 个种子，扫这几组：

| 组 | steps | batch | lr | 目的 |
|---|---|---|---|---|
| 1 | 50 | 4 | 1e-2 | 复现基线，确认与现有数据一致 |
| 2 | 50 | **32** | 1e-2 | 只加 batch，看噪声地板降到多少 |
| 3 | **200** | 32 | 1e-2 | 加 batch + 加步数 |
| 4 | 50 | 32 | **5e-2** | 加 batch + 提 lr（比加步数便宜） |

**判断标准**：选出让「参考侧 loss 位移 > 0.05（阈值的 2.5 倍）」且「候选侧 loss 峰谷差 < 0.005（阈值的 1/4）」的那一组。前者保证模型真的在学，后者保证信噪比。

**第 2 步：在真实学习动力学下重测特异性**

用定下的参数，跑 `fault=none` 的干净候选，**四个模型 × 3 种子 × 两种耦合**，逐步记录三路信号。要回答的是：模型真的在训练时，干净候选的漂移还在阈值内吗。

同时做一次**真实规模 spot-check**（吸收原实验 F）：挑 5–8 个实例搬到 ResNet-18 或小 GPT-2 + 真实数据集（CIFAR-10 / AG News 全量，不是 4×4 的 5 类子集），同样跑干净候选，报漂移和墙钟时间。仓库里 `experiments/resnet_torchax_cifar/` 和 `experiments/mobilenet_torchax_cifar/` 已经有脚本，但**没有任何结果落盘**，可以直接用。

### 验证跑对了

- 四个模型的参考侧位移都 **> 0.05**，否则第 1 步没选对参数，别往下走
- 干净候选的 `loss_abs_diff` / `grad_norm_abs_diff` / `param_update_rel_l2` **仍然全部在阈值内**。这是这项实验的主结论
- **特别关注 `free-running` 下的 Δgrad**：小 batch 的随机梯度噪声是最可能的假阳性来源，现在被 teacher-forcing 屏蔽了。如果 0.05 这个阈值在真实梯度噪声下自己越界，那是必须知道的事，如实报告
- 真实规模那几个实例报墙钟时间，用来说明验证开销可接受

### 备注

现有 4800 行数据**不用废弃**。它的 `teacher-forced` 部分干净可用（前向 3.8e-6、更新层恒为 1.0，四模型三种子五十步全程一致），特异性 2×2 就是从它算出来的（见文末附录）。这项实验是给那个结论补一个「系统真的在学」的版本，不是替换它。

**如果第 2 步发现干净候选在真实动力学下越阈了**，那不是坏消息，是必须知道的事——它说明阈值需要按 batch size 或梯度噪声尺度来定，而不是三个固定常数。如实报告，不要调参数去凑一个不越阈的配置。

---

## 实验 E：Track A 修完 bug 后重跑

### 论文主张

目前论文**没有**翻译工具对比表。Track A 是唯一能提供"与 MSAdapter / X2MindSpore / CodeTransEngine 这些真实迁移工具对比"的数据。这张表能进论文的话，是对"为什么不直接用官方转换工具"的直接回答，比只跟 LLM baseline 比更有分量。

### 现在缺什么

三件事：

1. **Bug 1/2/3 必须先修**，否则四个 baseline 的 `0.0%` 全部是构造出来的
2. **产物缺失**：`experiments/baselines/track_a/*/{raw,candidates,logs}` 全部只有 `.gitkeep`，五个 `summary.json` 一个都不存在，而 `overall_results.md:3` 声称结果来自它们。数字追不回任何模型输出
3. **环境**：需要 MindSpore 2.7.2、MSAdapter、CodeTransEngine（含 `T-CTE/codetransengine_translation_only.patch` 补丁）；T-X2MS 还需要 Windows + WSL + Ascend CANN

### 怎么跑

1. 先修 Bug 1、2、3
2. 五个 baseline 全量重跑，**产物落盘**：候选代码、执行日志、`summary.json`
3. 逐任务、逐 seed 输出，不要只给聚合数

### 验证跑对了

- 五个 `summary.json` 都存在，且 `overall_results.md` 的数字能从它们复算出来
- `candidates/` 和 `logs/` 里有实际内容
- **T-MSA / T-X2MS 不应再是 `0.0%`**。若修完仍是 0，请给出 `errors["strict_metrics"]` 里三个数值各是多少——要能说明是真的不达标，而不是判定链的问题
- 另外核查 `T-HIER/run_t_hier.py:497`：它算出了 strict checker 的结果，却用内部 verifier 报告覆盖了 `strict_success`。这条也要一并确认

### 备注

修完之后 T-MSA / T-X2MS 大概不会还是 `0.0%`，那张表会**变得可信但不再那么好看**（现在是"我们 100% 对手全 0%"）。这是正确的方向：一个可信的 60%-vs-95% 比一个不可信的 0%-vs-100% 对论文更有利。

---

## 实验 F：真实数据集扩充 → **已并入实验 D（真实规模 spot-check）和实验 I**

原来单列一项「真实数据集扩充」，现在拆掉了：干净候选在真实规模模型上的漂移归到实验 D 第 2 步，真实迁移场景归到实验 I。这里只保留两件仍然有用的信息。

**改大模型不是改配置能做到的**，动手前要知道：故障池里的模型是**拼进生成源码的字符串**，不是传进去的 `nn.Module`。`candidate_artifacts.py:40-78` 硬编码四个极小网络（`nn.Linear(4,8)`、`nn.Conv2d(1,4,3)` 等），`model_variants.py:6-12` 还有硬白名单（`MODEL_ID_TO_VARIANT` / `MODEL_VARIANTS`），非 M1–M4 在 `:19` 直接抛 `ValueError`。所以加第五个模型要改 `_feature_model_code` 加分支，再给每个故障族写对应的替换字面量。

**最省事的那条路**：`PocketResNet`（`experiments/paper_section_63_64/section642_heldout_sources/resnet.py:21`）是现成的第五个模型，已被 T-HIER 和 6.4.2 消融用过，不需要新写。

**一份已经跑完、零成本可用的真实数据**：`artifacts/torchvision_backbone_op_coverage.json` 是一次算子覆盖扫描——13 个 torchvision backbone，11 通过 2 失败，437 个注册算子。它不是修复结果，但可以作为「算子映射覆盖了多少真实模型」的补充证据，写进 Threats to Validity 一句话就行，不用跑任何东西。

---

## 实验 G：多故障实例（一个候选 2–3 个故障）

### 论文主张

打破天花板。这是让 Table I 重新具备信息量的前提。

### 现在缺什么

现在 50 个实例每个**只注入一个故障**，LADDER 100%、JAX 6/6。满分的后果不只是「看起来太容易」，而是**所有对比和统计检验都失去了信息量**：LADDER 50/50 vs MatchFixAgent 47/50 只有 3 个不一致对，McNemar 精确检验双侧 p=0.25。

真实迁移里故障是共现的——一个翻译产物同时有 dtype 问题和 reduction 问题很常见。多故障实例既更真实，又立刻打穿天花板。

### 怎么跑

1. 从现有 25 个故障类别里组合，构造 20 个左右的多故障实例，每个含 2–3 个故障
2. **组合要跨层**：例如 execution + numerical、numerical + gradient、三层各一个。同层两个故障不如跨层有意义，因为跨层才考验「第一个失败阶段」这个机制——修完第一层之后第二层才暴露出来
3. 六个方法全跑，预算与主表一致（4 次尝试）
4. 记录**每次尝试后哪一层通过了**，不只记最终结果。多故障场景下这个轨迹才是重点

### 验证跑对了

- 每个实例的故障数、各故障所属层、注入位置都要落盘，能复算
- **LADDER 不应该再是 100%**。如果还是满分，说明故障组合得太容易，加到 3 个或选更难的组合
- 逐次尝试的层通过轨迹要单调（修好的层不应该在下一次尝试后又坏掉）；若不单调，是回归问题，要单独报告

### 预期结果

LADDER 的优势应该在这里**放大**而不是缩小：baseline 只知道「没修好」，多故障时它无法判断该先修哪个；LADDER 每轮报出当前第一个失败阶段，天然是一个逐层剥离的过程。**如果实测不是这样，那是比任何数字都重要的发现**，如实报告。

---

## 实验 H：换 LLM 重跑主表 + 3 seeds

### 论文主张

两件事：机制跨模型成立，以及论文可复现。

### 现在缺什么

**论文从头到尾没有点名用的是哪个 LLM。** 实际是 `deepseek-v4-flash`（`section65_fault_pool_repair_raw.json` 里 75 处 `"model": "deepseek-v4-flash"`，`temperature: 0.1`）。只用过这一个模型，只跑过一次，没有种子、没有置信区间。

已核实六个方法用的是**同一个 backbone、同一个温度、同一个尝试预算**（3 个外部方法的 `metadata` 全是 `deepseek-v4-flash` / 0.1 / 4），所以横向比较是公平的——但这一点论文也没写，不写审稿人会默认你把 baseline 配坏了。

### 怎么跑

1. 至少 **3 个 backbone**：`deepseek-v4-flash`（保持现有结果可比）+ 一个 Qwen + 一个第三方。仓库里已有 Qwen 相关入口（`autofix/examples/run_phase12_qwen_core_faults.py`）
2. 每个 backbone 跑 **{LADDER, execution-only, 直接 LLM 修复} × 50 实例 × 3 seeds**。外部 agent（SWE-agent / MatchFixAgent）成本高，可以只在主 backbone 上跑 3 seeds，换模型那部分不跑它们
3. 报均值 + 95% CI，以及 LADDER vs 最强 baseline 的**配对 McNemar 检验**（同实例配对，不是两组独立比例）

### 验证跑对了

- 每次运行的 `metadata` 都要落盘 backbone、温度、尝试预算、seed
- **同一 backbone 三个 seed 的差异应该小于跨 backbone 的差异**。若某个 backbone 内部方差就很大，说明 4 次尝试的预算下随机性主导，这个要如实说
- 三个 backbone 上「LADDER > unordered > execution-only」这个**序**都成立，才能说机制跨模型成立。数值不必接近，序要一致

### 备注

如果换了 backbone 后 LADDER 的优势明显缩小，最可能的解释是弱模型吃不下结构化反馈。这仍然是可发表的结论（「方法需要 backbone 具备一定的指令跟随能力」），比一个只在单模型上成立的数字诚实得多。

---

## 实验 I：真实翻译产物端到端（不注入任何故障）

### 论文主张

外部效度。这是目前**最硬的那一击**，也是我在上一版清单里漏掉的。

### 现在缺什么

Table I 那 50 个实例，是往一个**已知正确的 torch4ms 实现里注入故障**得到的（raw JSON 里 `candidate_provenance: "oracle_candidate"`）。这是 bug-seeding 研究的范式，不是工具评估的范式。25 个故障类别确实来自真实观察到的迁移失败，但评估实例是构造的。

审稿人一定会问：真实的翻译产物上呢？现在没有任何数据能回答。

（另外已核实一件有利的事：候选源码里**没有泄漏参考实现**，30 个「故障 × 模型」组合的候选源码里 `class Reference` / `expected =` / `def run_probe(` 等标记 0 命中，参考实现只在单独的 verifier artifact 里。所以「LLM 会不会直接抄旁边的正确实现」这个怀疑可以排除。）

### 怎么跑

1. 取 **10–20 个 held-out PyTorch 训练脚本**，不属于现有四个模型族，也不在 25 个故障类别的来源里
2. 跑**真实翻译**（LLM 翻译器或 torch4ms 自动转换），**不注入任何故障**
3. 对翻译产物跑三层检查，记录：
   - 各阶段的**自然失败分布**——真实迁移里执行/数值/梯度三类失败各占多少。这个分布本身就是论文没有的数据
   - LADDER 修到三阶段等价的比例
   - 残余失败的**人工归因**：修不了的是什么原因
4. 至少跟直接 LLM 修复对比一次

### 验证跑对了

- 每个脚本的翻译产物、三层检查输出、每轮修复补丁都落盘
- **不要因为 n 小就补注入故障凑数**。n=10 的真实数据比 n=50 的注入数据更有说服力，混在一起反而两头都不可信
- 自然失败分布若与 25 个类别的分布差别很大，**如实报告**——这正是这项实验的价值所在

### 备注

这项实验会把论文的性质从「种 bug 实验」变成「工具评估」，同时天然解决天花板问题（真实产物不会 100% 修好）。成本比其他几项高，但收益也最大。

---

## 实验 J：反馈粒度消融 + 反序条件

### 论文主张

RQ2 现在只证明了「有这些信号比没有好」，没有拆开**「信号存在」**和**「信号有多具体」**。论文的贡献词是「更好的反馈」，那这两件事必须分开。

### 现在缺什么

Table II 现在只有三个累加前缀（E、E+N、E+N+G），这个设计把「信息更多」和「顺序正确」混在一起了。缺两组条件：

**粒度**（同样的信号，改报告的详细程度）：

| 条件 | 反馈内容 |
|---|---|
| (i) 仅 pass/fail | 只说过没过 |
| (ii) 仅阶段标签 | 只说"数值层失败"，不给数字 |
| (iii) 完整 LADDER | 阶段 + 数值差 + 出错的 step + 张量/参数名 |

**顺序**：加一个**反序条件**（先报梯度层、最后报执行层），用来隔离「顺序」与「信息量」。

### 怎么跑

- 粒度三条件：只改 prompt 模板，同池同预算，不改任何检查逻辑。成本极低
- 反序：**跑在 50 实例池上，不要跑在 n=12 上**。n=12 得不出任何可发表的顺序结论（4 个不一致对，双侧 p=0.125）
- 不要做完整的 3!=6 种顺序析因，那是浪费。一个反序条件足够说明问题

### 验证跑对了

- 三个粒度条件的 prompt 模板全部落盘，能看出差别只在详细程度
- (i) 应该接近 Table III panel (a) 里 pass/fail 那行的结果（当时是全 0），可以作为交叉验证
- 反序条件下，**如果结果与正序没有显著差别**，说明起作用的是信息量而不是顺序——这会削弱论文对"ordered"的强调，但必须如实报告。可以改成强调「分层」而不是「顺序」

---

## 实验 K：补 `predicted_layer` 日志字段后重跑（性价比最高）

### 论文主张

**这是唯一 baseline 结构上产不出来的证据。** LADDER 能说出故障在哪一层，baseline 只能说「没修好」。论文的机制主张是"the first failing stage becomes targeted repair guidance"，但从来没验证过「报出的阶段 == 注入故障的真实阶段」。

### 现在缺什么

一个字段。

- **Track C（JAX，n=6）已经有了**：`experiments/paper_section_67/results_fixer_torchax/section67_fixer_torchax_summary.md` 里有 `Expected layer` / `Predicted layer` / `Layer correct`，六个任务定位准确率 100%，**但论文 Table IV 只报了修复数，把这一列扔了**
- **Track B（主表，n=50）缺**：raw JSON 里只有真实层 `layer`（`'execution'` 等），**没有 predicted 字段**。所以需要补日志再重跑

### 怎么跑

1. 在诊断产出的地方把「第一个失败阶段」记进 episode。**字段名直接照抄 Track C 的**，`section67_fixer_torchax_tasks.csv` 的表头是：

```
bridge,model,fault_id,fault_type,expected_layer,predicted_layer,layer_correct,
diagnosis_complete,repair_success,final_strict_pass,rounds,repair_at_1,repair_at_3
```

Track B 现在有 `layer`（真实层），要加的是 `predicted_layer` 和 `layer_correct`。两条 track 字段名一致，最后就能合成一张跨框架的定位准确性表，不用再做名字映射。

2. 重跑 LADDER 的 50 实例（不需要跑 baseline——它们没有分层诊断，本来就产不出这个字段）
3. 输出**阶段级混淆矩阵**：真实层 × 预测层的 3×3 表
4. 若能拿到补丁落点，再加一个**补丁命中真实故障行的比例**

### 验证跑对了

- 混淆矩阵的行和应等于 20 / 14 / 16（与主表的阶段分母一致）
- 与 Track C 的 100% 对照，看 n=50 上是否仍然这么高
- **误分类的实例要单独列出来**：预测成哪一层、为什么。三个 100% 的表格不如一个 94% 加三个误分类案例分析有说服力

### 备注

这项实验成本最低（只跑一个方法、不需要新故障、不需要新环境），产出的却是论文里唯一能体现「我们的反馈有诊断力而不只是通过率高」的证据。**建议第一个做。**

---

# 第三部分：论文需要的图

论文现在只有两张图：架构图（`:123`）和 cost-quality（`:164`）。三个 RQ 里两个只有表格。

下面七张图按「性价比」排序 = 对论文的帮助 ÷ 需要的新数据。**图 1、图 2、图 4 不需要任何新实验。**

## 图 1：分层反馈的阶梯效应（零成本，建议最先做）

### 要表达什么

论文 RQ2 最核心的一句话（`:203`）：

> execution-only feedback repairs the execution faults, adding the forward check repairs the numerical faults, and the full report repairs the gradient/update faults as well

这是一个**完美的对角线**，但现在埋在 `tab:feedback-ablation` 的表格里，读者要自己在脑子里连线：

| Feedback | Exec. | Num. | Grad./upd. |
|---|---|---|---|
| Execution-only | 4/4 | 0/4 | 0/4 |
| Execution + numerical | 4/4 | 4/4 | 0/4 |
| LADDER | 4/4 | 4/4 | 4/4 |

**每加一层检查，恰好多修好一类故障，不多不少。** 这是全篇最强的因果证据——它排除了"只是因为给了更多信息"这个替代解释。画成图，这个对角线一眼可见。

### 怎么画

3×3 的分组柱状图或热力图。横轴三类故障，纵轴（或颜色）修复数 0–4，三组对应三种反馈条件。对角线以下全 0、对角线及以上全满。

建议在图上直接标出"加了什么检查"→"多修好了哪类"的对应关系（三个箭头）。

### 数据

**已存在，就在论文表格里。** 按 `figures/make_cost_quality.py` 的做法把数字硬编码进脚本并注明来源表，图就不会和表格漂移。

### 依赖

无。今天就能画。

## 图 2：LADDER 的增益集中在哪一层（零成本）

### 要表达什么

把 motivation 和结果直接连起来。论文 `:159` 说：

> The fault-stage columns show where the gain comes from: LADDER repairs all 16 gradient/update faults, compared with 13 for MatchFixAgent and 14 for direct LLM repair.

也就是说：**六个方法在 execution 层几乎打平，差距全在 gradient/update 层**——而那正是单一判定看不见的那一层。这个论证目前只有一句话，读者得自己去 Table I 里横向比对四列。

从 Table I 提取的实际数字：

| 方法 | Exec. | Num. | Grad./upd. |
|---|---|---|---|
| Execution-only | 14/20 | 7/14 | 12/16 |
| All signals, unordered | 14/20 | 8/14 | 12/16 |
| Direct LLM | 18/20 | 8/14 | 14/16 |
| SWE-agent | 20/20 | 11/14 | 15/16 |
| MatchFixAgent | 20/20 | 14/14 | 13/16 |
| **LADDER** | **20/20** | **14/14** | **16/16** |

注意 MatchFixAgent 在 Num. 层已经追平（14/14），**唯一拉开差距的是 Grad./upd. 层**。这个观察对论文很有利，值得单独画出来。

### 怎么画

三组柱状图（按故障层分组），每组六根柱（按方法）。或者更省版面：三条折线，横轴是六个方法按总分排序，纵轴是各层修复率——能看出前两层的线趋于重合、第三层的线分散。

### 数据

**已存在**（Table I）。同样硬编码 + 注明来源表。

### 依赖

无。但**如果做了实验 A（成对阈值重验），这张图要用重验后的数字重画**，因为那才是与论文 `:150` 描述一致的口径。

## 图 3：三种失效模式在单一判定下无法区分（需要实验 C）

### 要表达什么

这是**论文 Introduction 问题陈述的可视化**，也是你要的"前向对得上、梯度算出来是错的"那张图的正确形态。

论文 `:40` 说了三种失效模式，`:44` 接着说：

> Execution failures, forward mismatches, and backward/update errors **collapse onto the same verdict** even though each calls for a different repair.

图要表达的就是这句：**左边看单一判定，三种故障长得一模一样（都是"FAIL"）；右边看分层判定，三种故障有三个完全不同的签名。**

期望的分层签名（这才是有信息量的部分）：

| 故障 | 执行层 | 前向层 | 梯度层 | 更新层 |
|---|---|---|---|---|
| `execution` | **崩** | 无数据 | 无数据 | 无数据 |
| `numeric` | 过 | **越阈** | 越阈 | 越阈 |
| `grad_wrong` | 过 | **对到机器精度** | **越阈** | 越阈 |
| `param_wrong` | 过 | **对到机器精度** | **对到机器精度** | **越阈** |

**四种故障，四个不同的签名，而单一判定全都是 FAIL。** 这是"为什么需要分层"最直接的证据。

关键在最后两行：`grad_wrong` 和 `param_wrong` 的前向层都对得上，但一个梯度错一个梯度对——**只有分层检查能区分它们，而它们需要完全不同的修复**（前者查自动微分，后者查参数注册/优化器）。

### 为什么现在画不出来

现有四种故障只能填出上表的前两行。第三行需要 `grad_wrong`（不存在），第四行需要 `param_wrong`（不存在）。

现有的 `training` 故障填不了第三行：它的梯度是**空值**（backward 没跑），在图上只能画成"不可测"，而不是"测出来是错的"。两者的说服力差很远——"测不到"可以被解释成检查失效，"测出来是错的"才是检查有效的证明。

### 怎么画

左右两栏：左栏"单一判定"，四种故障四个相同的 FAIL 标记；右栏"分层判定"，四种故障 × 四个层的矩阵，每格用「对到机器精度 / 越阈 / 无数据」三种视觉状态。

纵轴用「量 ÷ 自己的阈值」的对数刻度，y=1 就是检测线，三个层共享一根轴。「无数据」不要画在 0 的位置（会读成"没响"，与事实相反），单独放一个区带并明确标注。

### 依赖

**实验 C。** 这张图是实验 C 的主要目的。

## 图 4：token 成本的构成——差距在 prompt，不在生成（零成本，新增）

### 要表达什么

论文现在只报 token 总数（`0.191M` vs `5.205M`），把最有说服力的部分丢掉了。从 `experiments/baselines/full_hier_fixed50/summary.csv` 拆开看：

| 方法 | prompt | 占比 | completion | 合计 |
|---|---|---|---|---|
| R-EXEC | 108.3K | 70.0% | 46.5K | 0.155M |
| R-FLAT | 111.4K | 61.8% | 69.0K | 0.180M |
| **R-HIER（LADDER）** | **147.3K** | **77.3%** | **43.3K** | **0.191M** |
| Direct LLM | 1406.3K | 88.8% | 176.6K | 1.583M |
| MatchFixAgent | 4739.4K | 91.1% | 465.8K | 5.205M |
| SWE-agent | 7512.5K | 98.4% | 122.5K | 7.635M |

**每个 baseline 的 prompt 倍数都远高于它自己的 completion 倍数**（以 LADDER 为 1）：

| 方法 | prompt 倍数 | completion 倍数 |
|---|---|---|
| Direct LLM | 9.6× | 4.1× |
| MatchFixAgent | 32.2× | 10.7× |
| SWE-agent | **51.0×** | 2.8× |

SWE-agent 98.4% 的 token 花在 prompt 上，它的 completion 只有 LADDER 的 2.8 倍——**它并没有写更多代码，它是把上下文读了 51 遍。**

这给了成本优势一个**机制解释**，而不只是一个比值：baseline 必须搜索故障位置，搜索就要把不断增长的上下文反复喂回模型；LADDER 直接拿到第一个失败阶段，不搜索，所以上下文不累积。「省 27 倍 token」变成「不需要搜索，所以不需要把上下文喂 51 遍」——后者才是方法论主张。

### 怎么画

六个方法的水平堆叠柱，每根柱分 prompt / completion 两段，横轴对数刻度（跨度 0.155M–7.635M，线性刻度下前三个方法会挤成一条线）。直接在柱上标 prompt 占比。

也可以并进现有的 cost-quality 图（`:164`）做成两栏，但单独一张更清楚。

### 数据

**已存在**，就在 `summary.csv` 里，逐实例加总与论文 Table I 的 token 列完全一致（5,205,141 / 7,635,016 / 1,582,865 对应 5.205M / 7.635M / 1.583M，已核验）。硬编码进脚本 + 注明来源。

### 依赖

无。今天就能画。

### 顺带要在论文里补一句

已核实六个方法用的是**同一个 backbone、同一个温度、同一个尝试预算**（`deepseek-v4-flash` / `temperature 0.1` / 4 次尝试，三个外部方法的 `metadata` 里都是这个）。**论文没写这一点**，不写审稿人会默认 27 倍差距是把 baseline 配坏了造成的。

## 图 5：定位准确性混淆矩阵（需要实验 K）

### 要表达什么

**这是唯一 baseline 结构上产不出来的图。** 别的方法只能输出「修好了/没修好」，LADDER 能输出「故障在第几层」。

论文的机制主张是「第一个失败阶段构成定向修复指导」，但从来没验证过报出的阶段是不是真的那一层。这张图就是那个验证：3×3 矩阵，行是注入故障的真实层，列是诊断报出的层，对角线就是定位正确。

Track C（JAX，n=6）已经测了，`section67_fixer_torchax_summary.md` 里 `Layer accuracy` 六项全对 = 100%，**但论文 Table IV 只报了修复数，把这一列扔了**。Track B（n=50）缺 `predicted_layer` 字段，需要补日志重跑。

### 怎么画

3×3 热力图，行和标注 20 / 14 / 16（与主表阶段分母一致）。**误分类的格子要标出实例 ID**，别只给个百分比。

如果 n=50 上仍是 100%，那图就退化成一条对角线，此时**改成表格更省版面**——但把误分类案例（如果有）写进正文比一张满分的图有用得多。

### 依赖

**实验 K。** 也是所有实验里成本最低的一项。

## 图 6：多故障场景下的逐层剥离（需要实验 G）

### 要表达什么

这是天花板破了之后最能体现方法优势的图。多故障实例里，修复是一个**逐层剥离**的过程：第一轮修掉执行层，数值层才暴露出来；修掉数值层，梯度层才暴露。

baseline 在这个场景下只知道「还是没过」，无法判断该先修哪个。LADDER 每轮报出当前第一个失败阶段，天然就是这个剥离过程。

### 怎么画

横轴修复轮次（1–4），纵轴累计通过的层数，每个方法一条线。或者更直观：每个实例一行的甘特式条带，颜色表示当轮阻塞在哪一层，能看出 LADDER 逐层推进、baseline 反复卡在同一层。

### 依赖

**实验 G。** 这张图的说服力取决于多故障实例做得够不够难——如果 LADDER 在多故障下仍是 100%，图就没有信息量。

## 图 7：跨框架一致性（数据已存在，但样本太小）

### 要表达什么

RQ3 的主张：同一套检查换个框架仍然有效。目前 `tab:jax-transfer` 只有 6 个故障、4 个方法，是论文最薄的一块（Threats to Validity 自己也承认了）。

### 现在的问题

6 个故障画图没有意义，画出来反而暴露样本小。**建议保持表格形态**，除非 Track C 能扩到 20+ 故障。

如果扩了，可以画 MindSpore 路径和 JAX 路径的并排对比——同一套分层检查在两个完全不同的自动微分系统上的分层修复率。那会是一张有力的图。

---

# 附：优先级建议

**第 0 批：零机器成本，今天就能做**
- 图 1（阶梯效应）、图 2（增益集中在哪层）、图 4（token 构成）—— 数据都已存在
- 离线重分析包：特异性 2×2、阈值敏感性、验证开销 = 1 步（数字已算好，见下一节附录）
- Bug 4 的选择：走 (a) 补验收 还是 (b) 改论文措辞
- 正文改以 Repair@1（84.0%）为头条指标，Repair@4 退居次要——零成本地绕开天花板问题
- 论文补写：用的是 `deepseek-v4-flash`；六个方法同 backbone、同温度、同预算

**第 1 批：性价比最高的四项实验**
- **实验 K**（补 `predicted_layer` 重跑）→ 图 5。只跑一个方法，产出唯一 baseline 产不出的证据
- **实验 G**（多故障实例）→ 图 6。打破天花板
- **实验 I**（真实翻译产物）。挡住「种 bug 实验」这一击，成本最高但收益最大
- **实验 H**（换 LLM + 3 seeds）。解决论文不点名模型这个可复现性缺陷

**第 2 批：补论文现有主张的缺口**
- 实验 A（Table I 成对阈值重验，不需要 LLM）→ 图 2 用重验后数字重画
- 实验 C（梯度算错的故障）→ 图 3。补 Introduction 缺的那类证据
- 实验 J（反馈粒度 + 反序）。把 RQ2 从「有信号比没有好」推进到「信号要多具体」
- 实验 D（真实学习动力学下的特异性 + 真实规模 spot-check）

**第 3 批：需要特殊环境或增量较小**
- 实验 B（50 → 60 实例）。规模增量有限，不如 G 和 I
- 实验 E（Track A 修 bug 后重跑，需 MindSpore + MSAdapter + CANN 环境）

**如果只能做三件事**：实验 K（最便宜、唯一独有的证据）、实验 G（破天花板）、修 Bug 1/2/3（否则 Track A 那张表不能用）。

**一件不占实验资源但需要优先确认的事**：`run_section66_realdata_training_consistency.py:76-79` 的 `_display_model()` 把内部模型名 `mlp` 显示成 `nlp`。请确认论文里写 `nlp` 的那一行对应的到底是哪个模型，这决定正文引用的数据有没有对错位。

# 附：三项离线重分析的结果（已经算好，不用跑）

这三项只用已交付的 4800 行数据，不需要任何机器时间。数字在这里，可以直接用。

**1. 特异性：干净候选完全不误报**

`fault=none` 的 24 个组合（4 模型 × 3 种子 × 2 耦合）、1200 行，三路信号**零次越阈**：

| 信号 | 阈值 | 越阈行数 | 实测最大值 | 余量 |
|---|---|---|---|---|
| `loss_abs_diff` | 0.02 | 0 | 3.815e-6 | 5243× |
| `grad_norm_abs_diff` | 0.05 | 0 | 1.192e-7 | 419430× |
| `param_update_rel_l2` | 0.03 | 0 | 4.852e-6 | 6183× |

论文 Table V 现在只报了灵敏度（36 次注入全部检出 = 1.000），没有干净候选那一半。补上这三行就是完整的 2×2。**但注意**：三个数字全是满分，这在审稿人眼里是防守性证据（挡住「你的检测器在没有 bug 时说什么」这一问），不是得分点。值得占半页，不值得占一个 RQ。

**这个结论有一个弱点**，必须知道：四个模型里三个在 50 步内几乎没学习（参考 loss 只移动 0.0025–0.0188）。在近乎静止的系统上测出 3.8e-6 的漂移是可预期的，所以余量六位数这件事的说服力被掏空了。实验 D 就是去补一个「系统真的在学」的版本。

**2. 验证开销：一步就够**

每个（模型 × 故障 × 种子 × 耦合）第一次越阈的步数：

| 故障 | 耦合 | 组合数 | 最早 | 中位 | 最晚 |
|---|---|---|---|---|---|
| execution | 两种 | 0 | — | — | — |
| numeric | free-running | 12 | 1 | 1 | 1 |
| numeric | teacher-forced | 12 | 1 | 1 | 1 |
| training | free-running | 12 | 1 | 1 | 1 |
| training | teacher-forced | 12 | 1 | 1 | 1 |

**所有非崩溃故障都在第 1 步越阈**，三个种子、两种耦合，全部是 1。`execution` 是 0 行，因为候选直接崩溃，没有可比较的数值——它的「检出」是崩溃这个平凡事实。

配套的一条：**只看末步 vs 逐步检查，检出完全相同**（每种耦合 24 vs 24，漏检 0）。

这两条合起来是一个**成本结论，不是精度结论**：同样的检出率，只看末步必须跑完 50 步，逐步 + 早停在第 1 步就结束，验证开销差 50 倍。

**不要写成「逐步检查更准」**。逐步的检查集合天然包含末步，所以逐步的检出必然是末步检出的超集——「逐步更准」在数学上只可能取等号或大于，永远不可能是一个有信息量的发现。这批数据取的是等号。

逐步作为**接受规则**仍然保留，理由是漏检不可恢复而代价近零。但要在 Threats to Validity 如实写清边界：本故障集全是从第 0 步起持续存在的注入故障，末步法在这类故障上等价；对**瞬态或延迟出现**的偏差（NaN 尖峰后恢复、lr schedule / momentum 累积 / weight decay 后期生效、BN running stats、梯度裁剪触发）我们没有数据。

还有一点别 overclaim：`training` 故障是跳过 backward，梯度**不存在**而非错误，第 1 步就越阈几乎是定义使然。所以「一步就够」最实的证据来自 `numeric`。

**3. 阈值敏感性**

用 4800 行逐步轨迹离线重判各阈值下的裁决，报「裁决翻转率」，回答「阈值是不是调出来讨好自己的」。鉴于干净侧余量是 5243×/419430×/6183×、故障侧第 1 步就越阈，**预期结论是裁决在很宽的阈值范围内完全不变**——这正是想要的结果。

写成附录里的一段话或一张小表即可，**不要为它花任何重跑预算**。

# 附：已交付数据的核验结论

已交付的 `results_section65_per_step_divergence/`（4800 行）**数据本身是干净的**，27 项独立核验全部通过：

- 网格完整（96 组合 × 50 步），列格式符合规格
- 空值约定正确：`execution` 崩溃后 744 行候选侧留空、参考侧仍有值；`training` 的梯度三列全空。没有用 0 或 NaN 冒充"不存在"
- **参考侧在四种故障下逐位相同**（max|Δ|=0），故障没有泄漏进 PyTorch 基线。这条规格里没要求，但它不成立的话整批数据就废了
- `fault=none` 对照落在机器精度（`loss_abs_diff` max 3.8e-6、`param_update_rel_l2` max 4.9e-6）
- `training` + `teacher-forced` 三条同时成立：前向 max 3.8e-6、更新层恒为 1.0、cosine 恒为 0.0
- 与论文 Table V 的检测矩阵一致，包括 `tiny_causal_lm` 的 numeric 梯度不越阈这个已知特性（Table V 写作 `N+U`，其余模型 `N+G+U`）

核验脚本在论文侧仓库 `scripts/verify_per_step_divergence.py`，可直接重跑。

**两处与规格的偏差，都不是执行问题**：

1. 规格第 8 节第 4 条要求 `free-running` 的 loss "单调上升"，实测是带噪声的弱上升（上升步占比 0.49–0.73）。**这是规格的措辞问题**——batch=4 的采样噪声下不可能单调，见实验 D。
2. `numeric` 故障换了注入手段（用现有 6.5 的 `perturb_output` + `logit_bias=2.0`，而非规格建议的权重 ×1.05）。**这个替换比规格的建议好**：它不碰参数，"只作用于前向"是构造保证的；且与现有 6.5 数据同函数，语义一致性由构造保证。

**规格本身的一处错误**：规格第 6 节把 `training` 故障当成了"前向对得上、梯度发散"的证据来源，但该故障的定义是跳过 backward，梯度**不存在**而非**错误**。论文问题陈述要的那一类失效需要新的故障类型，见实验 C。这不是执行方的问题。

---
