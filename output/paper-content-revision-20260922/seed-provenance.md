# 实验 seed 来源与控制对象

核对日期：2026-09-22。本次只读现有任务配置、运行脚本、归档代码和汇总；未运行实验，未修改论文。下表的 seed 是程序评估用随机种子，并非 LLM 采样 seed。确认种子在公共检查通过后使用；各实验的最终专项审计另按其既定协议执行。

| 实验 | 公共评估 / 确认或重复运行 seed | 实际控制对象 |
|---|---|---|
| 主 MindSpore 50 | 101 / 202、303 | `measure()` 的 NumPy RNG 生成随机输入和训练目标。模型初始参数由参数名的 SHA-256 派生独立的固定 RNG，然后在对应两端显式赋值；参数初始化不随 101/202/303 改变。部分离散输入、掩码、梯度或优化器测试值为固定常量。 |
| Java/DJL 18 | 101 / 202、303 | seed 传入既有跨语言配对评估器，选择相应评估。任务接口明确：评估器提供原程序的初始参数及两个真实预处理批次，复制参数后连续执行两步。当前本地材料未包含该评估器内部 fixture 生成代码，因此未进一步确认这些 seed 在原始 Java 采集端分别影响哪些初始化或批次抽样操作。 |
| 自然翻译故障 10 | 42 / 1042、2042 | Python、NumPy、PyTorch RNG 在源模型构造前设为 seed；源模型的初始状态复制至两端。输入及标签由单独的 CPU `torch.Generator` 以 `seed + 101` 生成。十个任务全部使用公共 seed 42，确认采用公共 seed 加 1000、2000。 |
| 训练信号消融 16 | 4101 / 5101、6101 | 与自然故障相同的配对 harness：seed 控制源模型初始化，显式共享初始状态；`seed + 101` 控制输入和标签，包括文本任务的 token/label 生成。四种反馈条件的任务公共 seed 均为 4101，最终完整信号检查使用三个指定 seed。 |
| JAX 6 | 6701 / 6702、6703 | `torch.manual_seed(seed)` 在源模型或候选模型构造前设置随机状态；CPU 批次生成器使用 `seed + 101` 产生正态输入和类别标签。候选构造后移至 JAX，自动微分和 Optax 更新使用所得状态。 |
| 检测轨迹 | 300、301、302，三次平行重复运行 | `init_model()` 以 seed 初始化浮点参数为均匀分布，源状态复制到相应目标运行。CIFAR 图像批次顺序使用 `seed + 5000`；AG News 分类批次顺序使用 `seed + 6000`；语言模型窗口起点使用 `seed + 7000`。同一模型和 seed 的各故障/同步条件共享生成的初始状态与批次。这里没有公共/确认 seed 的角色划分。 |

## 具体来源

### 主 MindSpore 50

- 逐一读取 `data/benchmarks/unified50_20260918/public/task_001/task.json` 至 `task_050/task.json`：50 项的 `seed` 均为 101，`evaluation.final_seeds` 均为 `[101, 202, 303]`。
- `experiments/unified_migration50_20260918/evaluator.py:24` 默认使用任务 seed；`:73` 的 `confirm()` 使用剩余两个最终 seed。
- `experiments/unified_migration50_20260918/measure.py:94` 的 `Runtime.align()` 根据参数名 SHA-256 的前八位生成 RNG，赋值为 `standard_normal * .08 + .02`；`:169` 的 `measure()` 创建 `default_rng(seed)`，后续 `tensor()` 和训练目标使用该 RNG。

### Java/DJL 18

- 逐一读取 `data/audits/unified50-preflight-20260918/final_review/cross_language/private_inputs/task_001/task.json` 至 `task_018/task.json`：18 项公共 seed 都是 101，最终 seed 都是 `[101, 202, 303]`。各配置的 `interface` 字段描述显式初始参数和两个真实预处理批次的传入与复制。
- `experiments/unified_migration50_20260918/extensions.py:34` 将 seed 传给 worker；`:66` 的 `confirm()` 调用 202、303；`:92` 和 `:96` 写入相同的任务协议。
- `experiments/unified_migration50_20260918/extension_worker.py:17` 将 seed 原样交给外部 `verify_candidate.evaluate()`。该模块位于脚本声明的原始 N18 运行目录，当前本地副本未包含其内部实现。附录可准确写“使用 101 公共评估和 202、303 确认，在每个配对评估中共享原始参数和预处理批次”；勿据当前证据进一步写三者具体控制 Java 初始化/数据 shuffle。

### 自然故障 10 与训练信号 16

- 自然故障归档：`output/maintext-ablations-20260918/archives/original_natural10_v3.tar.gz`。归档内 `original_natural10_v3/without_edit_format_feedback/private_inputs/task_001..010/task.json` 全部为 seed 42；其余三个组件条件的对应配置也全部为 42（共核对 40 个配置）。
- 同一归档下 `code_snapshot/autofix/autonomous/evaluation.py:142` 的 `confirm()` 返回 `base + 1000` 和 `base + 2000`。
- 同一归档下 `code_snapshot/autofix/verifiers/paired_code_report.py:78` 设置 Python/NumPy/PyTorch seed；`:99` 用 `seed + 101` 生成批次；`:457` 在构造源模型前设置 seed；`:461–467` 保存并加载共享源模型初始状态。
- 信号归档：`output/maintext-ablations-20260918/archives/training_signal16_v2_complete.tar.gz`。归档内 `training_signal16_v2_complete/all_observations/private_inputs/task_001..016/task.json` 全部为 seed 4101；其归档 harness 上述操作与行号一致。
- `scripts/run_training_signal_ablations.py:153` 设置公共 seed 4101；`:158` 和 `:170` 使用 4101、5101、6101 进行健康输入及故障构造核对；`:246` 使用这三者完成最终完整信号检查。`scripts/finalize_training_signals.py:44` 检查最终记录恰有这三个 seed。

### JAX 6

- `scripts/run_maintext_jax_autonomous.py:23` 定义 `(6701, 6702, 6703)`；`:159` 的 `paired()` 默认使用第一个；`:195` 的 `confirm()` 使用后两个；`:224` 为每个模型和 seed 准备源参考。
- `output/maintext-jax-autonomous-20260918/maintext_jax_complete_20260918.tar.gz` 内 `maintext_jax_autonomous_20260918/formal_v5/private_backend/torchax_backend.py:71–78`：输入、标签生成器使用 `seed + 101`；`:154–161`：以 seed 初始化 PyTorch RNG 后构造源模型或候选模型；`:178–183`：将候选移至 JAX 并读取其参数和缓冲区。
- `output/maintext-jax-autonomous-20260918/final_analysis/final_patch_audit/audit.json` 保存的最终测量涵盖 6701、6702、6703。

### 检测轨迹

- Figure 4 实际读取 `data/experiments/03_experiment_C_gradient_and_parameter_faults/results_per_step/section65_per_step_divergence_steps50.csv`；只扫描其 seed 列，实际值为 300、301、302。读取路径见 `figures/paper_data.py:15`。
- `output/maintext-diagnostics-20260918/provenance.json` 记录四模型、50 步、三次 seed 重复、批大小 4，并记录执行源代码 SHA-256。
- `ascend-torch4ms/experiments/paper_section_65_66/models.py:166` 的 `init_model()` 使用 `torch.manual_seed(seed)` 与参数均匀初始化。该文件 SHA-256 与上述运行 provenance 一致。
- `ascend-torch4ms/experiments/paper_section_65_66/realdata.py:121`、`:145`、`:165` 分别记录 CIFAR 的 `seed + 5000`、分类文本的 `seed + 6000`、语言模型的 `seed + 7000`。该文件 SHA-256 也与运行 provenance 一致。
- 当前本地 `run_section66_realdata_training_consistency.py` 与运行 provenance 的整体哈希不同，因此本记录用实际 CSV 确认 seed 值、用哈希一致的初始化/数据函数确认控制操作；未把当前 runner 的全文件当作已验证运行快照。

仓库主实验的 seed 细节由主代理独立核对，本次未重复查验：时间序列 101/202/303；推荐公共 101，确认 202/303 尚未触发。以上未改变任何结果、分母或执行状态。
