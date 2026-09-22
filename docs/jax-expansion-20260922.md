# JAX 扩展开发与自然迁移准备

本轮由用户授权扩展 JAX 实例、验证方法后再作原生基线比较。论文和方法图未修改。历史六例及所有旧结果保持原样。新目录为 `experiments/jax_expansion_20260922/`，远端工作目录为 `/media/main/whj/projects/torch4ms/experiments/jax_expansion_20260922/`。

## 两任务受控开发

本开发集用独立编写的公开 PyTorch 源程序定义训练语义，目标候选为原生 JAX/Optax。它测量受控修复，与旧 TorchAX 六例、未来自然迁移集合分别计数。两个任务在 API 调用前确定：残差 MLP 连续三步 momentum SGD、attention 连续三步 Adam；初始候选分别重置优化器状态、截断 query 梯度。健康目标、故障类别、参考输出不进入智能体 workspace。

每个 workspace 仅提供 `source.py`、`candidate.py`、`task.json`、初始参数和三批输入的 NPZ，以及 scratch tests 目录。源与合同、输入文件在每次外部验收时检查不可变 hash。参考执行在外部，目标运行经 Landlock/seccomp 隔离，禁止访问其他实验结果和凭据。JAX 仅用 CPU，两核 affinity，OMP/BLAS 各一线程。

三种子固定为 7101、7102、7103。每个种子连续执行三步，对齐每个参数的完整梯度、更新和最终参数；另比较 loss 与 logits，要求初始参数完全一致。阈值为 loss 绝对差 `2e-5`，各向量相对 L2 差 `2e-4`，分母下限 `1e-7`。缺失值、非有限值、参数名不匹配或长度不匹配均失败。7 个验收测试覆盖方向不同但范数相同的梯度、第三步更新错误、初态变化、缺失参数和非有限数。

### 启动前数值检查

`development_v1` 保存完整失败的健康 gate，未调用 API。attention 的 key bias 对 softmax 只有统一平移，理论梯度为零；FP32 舍入产生约 `1e-9` 的梯度差，经 Adam epsilon `1e-8` 放大为约 `1e-3` 的更新。种子 7101 第一步 PyTorch/JAX 的 key-bias 梯度 L2 分别为 `2.4701e-9`、`2.5153e-9`，梯度差 L2 为 `4.0961e-9`；更新差 L2 为 `0.00359575`。逐元素梯度、更新和公式复核保存在 `near_zero_bias_diagnostic.json`。两实现第一步更新都与 `-0.01*g/(abs(g)+1e-8)` 一致，三种子最大绝对误差低于 `1.8e-8`；初态、参数映射一致。该证据排除了 epsilon 位置差异。

在任何 API 调用前，开发模型去除这项冗余 bias，并同步更新源和目标，另建 `development_v2`；原阈值不变。v1 文件与记录全部保留。此处理仅用于本开发模型，正式公开源程序中的参数须保留。

v2 的 12 项 gate 全部满足预期：两任务×三种子健康均通过，两任务×三种子故障均被拒绝，均能执行。`preflight_passed.json` 是启动门禁。

### 方法与预算

方法代码逐文件复制自 `ascend-torch4ms-repository-20260921/autofix/`，Git HEAD `694f6920ac89de66492d556e00dacb42fcd47154`；实际工作树含 slim-v4，故以 `frozen_hashes.json` 的逐文件 hash 为准，不能仅用 HEAD 标识。保留 LaDiM 与当前 Direct shared-tools 的原有方法流程，只在既有提示常量中将运行时名称替换为 native JAX/Optax，并接入新的 evaluator。

四条件固定为两任务×LaDiM/Direct。每条件最多 40 调用、120,000 输出 token、1,800 秒、4 提交，每次调用最多 16,384 输出 token。单 API worker 顺序运行，不增加失败重试预算。总硬上限 160 调用、480,000 输出 token；所有实际调用与失败计费。

v2 于本轮启动，PID `3373399`；日志为 `development_v2/development.log`，启动记录为 `launch.json`。manifest SHA-256 为 `b7cff430cb5110181d395b23d569f590862ddc1ed4d0f17b1200a994d920c329`。`launch_development.py` 只读取远端现有指定凭据文件，拒绝重复启动；不打印凭据。若中断，必须先检查已存在条件；runner 默认拒绝覆盖，不自动重跑。

开发批次的冻结 worker 检查返回对象为 JAX arrays，逐参数仅保存 flatten 向量。主代理审阅发现类型检查不足以独立证明求导后端，flatten 也未验证原始 tensor shape，另有 `before=p` 对合法 dict 原地修改的潜在误判。本批运行中的判定保持不变，新增 `audit_worker.py`、`audit_development.py` 在完结候选上单独复验：独立调用 `jax.value_and_grad(candidate.forward→交叉熵)`，检查完整梯度与 loss、每项 tensor shape，复制参数字典后计算更新。额外审计与原始判定分别报告。正式 worker 必须内置这些检查。

## 正式自然迁移来源池

在开发 API 结果前，已从 PyTorch 官方 examples 仓库冻结 8 个原始文件，选定 9 个模型工作负载，覆盖四族。revision 为 `acc295dc7b90714f1bf47f06004fc19a7fe235c4`；原文件字节、LICENSE、逐文件 SHA-256 与 URL 位于 `experiments/jax_expansion_20260922/formal_source_pool/manifest.json`。这些程序与开发两个源完全分离，没有按方法结果删选。

| 工作负载 | 上游文件/模型 | 公共运行条件 |
| --- | --- | --- |
| CNN 分类 | `mnist/main.py` / Net | 2×1×28×28，eval 模式关闭 dropout，NLL，SGD momentum |
| 超分辨网络 | `super_resolution/model.py` / Net | 放大2倍，2×1×8×8，MSE，Adam |
| 变分自编码器 | `vae/main.py` / VAE | 2×784，共同 epsilon，重构 BCE+KL，Adam |
| 图像生成网络 | `dcgan/main.py` / Generator | nz=8/ngf=4/nc=1，train BN，固定监督目标 MSE，Adam |
| 循环语言模型 | `word_language_model/model.py` / RNNModel | LSTM，词表17/嵌入8/隐藏8/1层，每批零隐态，SGD momentum |
| Transformer语言模型 | 同文件 / TransformerModel | 词表17/维度8/2头/前馈16/1层，eval dropout，SGD momentum |
| 时间序列网络 | `time_sequence_prediction/train.py` / Sequence | 原51维双层LSTMCell，2×6输入，MSE，Adam |
| Actor-Critic网络 | `reinforcement_learning/actor_critic.py` / Policy | 固定状态、动作、return，策略损失+值MSE，Adam |
| REINFORCE网络 | `reinforcement_learning/reinforce.py` / Policy | 固定状态、动作、return，eval dropout，策略损失，SGD momentum |

这些是从公开模型类构建的三步优化工作负载，不测量整应用的下载、数据流水线、环境交互或完整 GAN 对抗训练。`formal_workloads.py` 保留原模型类 AST，排除 top-level 参数解析和外部应用启动。运行精度统一为 float64，完整参数和 buffers 由源初始化后提供给目标；正式目标必须开启 JAX x64。dropout、VAE 公共 epsilon、BN buffers、循环状态重置、优化器状态延续均写入公共合同，见远端 `formal_source_checks_v1/contracts.json`。

`check_formal_sources.py` 实际执行 9×3 种子、每种子三步源训练，记录参数形状、buffers、loss、缺失梯度和耗时。这只是源程序可运行检查；正式目标的健康数值 gate、共享初始自然翻译、完整输入冻结、最终验收阈值和四方法原生接入 smoke 仍须完成后才能启动正式比较。不能把源 gate 称为 JAX 迁移成功。

正式计划为 9×4=36 条件，LaDiM、Direct、原生 MatchFixAgent full orchestration、原生 SWE-agent 共用同一初始自然翻译、输入、种子、初态、合同与验收。每条件40调用/4提交，不改变原生算法、提示或重试。共享翻译建议每任务1次、最多16,384输出 token，其完整实际成本对四方法端到端账本各计一次。修复硬上限1,440调用、4,320,000输出 token；额外9次初始翻译最多147,456输出 token。正式启动前交由主代理审核可运行清单、健康 gate 和冻结方法版本。

现有最新接入已提供 MatchFixAgent/SWE-agent 原生实现；其框架名称读取 `task.json.target_framework`，正式合同须明确 `native JAX/Optax`，并将共同 `inputs/` 纳入隔离容器可读集。接入修复仅涉及传递公共输入和 evaluator，不能修改上游算法。现有 SWE 打包清单尚未包含 `inputs/`，需要在新独立快照上补该项并做无API smoke；开发 LaDiM/Direct 不受影响。
