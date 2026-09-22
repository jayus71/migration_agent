# JAX 扩展开发与自然迁移实验

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

最初的9任务来源池与27项源检查保留为第一版准备记录。用户随后要求新实验彻底替换旧六例，并增加较复杂、初始有问题的程序；正式准备范围因此在任何自然初译前扩展为12个来源任务。新增 GAT（4头、concat、邻接mask）、公开 GPT-nano（3层、3头、48维）、ResNet(BasicBlock,[1,1,1,1],5类)。新来源清单为 `formal_source_pool/manifest_12_tasks.json`，旧 `manifest.json` 保持不变。GAT沿用 examples revision；minGPT 固定为 `37baab71b9abea1b76ab957409a1cc2fbfba8a26`；torchvision固定为 `7b0e250acf82aac5a2389f54c6855da17bfeace9`。合同逐任务记录实际仓库和commit。

12任务×3种子的36项源检查全部通过，见 `formal_source_checks_v2/results.json`。ResNet有4,908,357参数，CPU float64三步约0.44秒/种子；原始完整参考数组量约393MB/种子，采用NPZ压缩保留，不向模型发送数组正文。源检查与目标迁移验收分别记录。

正式候选实现 `forward(parameters, buffers, batch, task)`，迁移前向、可微路径和显式buffer状态。可信外部worker独立执行 `jax.value_and_grad` 和合同指定的Optax优化器，连续三步，与PyTorch同名参数和buffers作逐元素比较。它不测试候选自行实现或修复优化器。浮点精度统一float64；tensor名称、shape、dtype必须一致，初态精确相同，其余量使用预先固定的 `atol=1e-7, rtol=1e-5`。完整outputs、gradients、updates、parameters、buffers保存为NPZ，完整统计留证据，模型反馈报告通过计数和所有失败量。`public`、`paired`是同一个首种子检查的别名，公共合同明确这一点，最终三种子验收保持完整。

独立健康后端控制使用小型线性MSE源/目标，覆盖SGD momentum和Adam各三种子、连续三步，6/6通过。该gate校验可信worker的独立JAX求导、优化器语义、shape/dtype和NPZ比较，不计入自然模型迁移成功率。

四方法原生接入smoke均完成且实际API为零。LaDiM/Direct调用真实诊断/验收生命周期后初态通过，完整修复路径由四条真实开发运行覆盖。MatchFix full orchestration进入原生路径并执行4次假provider调用；SWE启动upstream worker、进入原生episode并执行3次假provider调用。假传输的MatchFix `call_budget_exhausted` 与SWE `exit_format`按原记录保留，未冒充真实模型性能。SWE匿名Git实际追踪三份inputs NPZ；按相同Landlock/seccomp和公共写路径运行探针，输入可读、写入PermissionError。接入只补公共inputs的regular-file验证和匿名Git追踪，保持inputs只读，不修改baseline算法、提示或重试。

## 开发最终结果与自然实验执行

四个开发条件均首提交通过。LaDiM共23调用、339,929输入token、12,695输出token，合计352,624；Direct共20调用、259,776输入token、18,663输出token，合计278,439。LaDiM总token多74,185（26.64%），本开发集没有显示方法优势。额外独立求导/shape审计12/12通过。逐响应usage和原账本完全核对；摘要为 `output/jax-expansion-20260922/development_v2/development_summary.json`。

额外成本主要来自修复阶段：LaDiM修复11调用/241,370 tokens，Direct修复4调用/88,573；LaDiM诊断12调用/111,254 tokens，Direct诊断16调用/189,866。两方法每例均只有一次生产代码编辑。LaDiM编辑后重复调用同义的public/paired，attention还追加scratch复查，角色交接后重复读源/候选，长反馈继续随历史传入。后续可研究检查去重和紧凑证据，但本正式比较保持方法算法冻结，仅对四方法统一使用NPZ与紧凑共同反馈。

开发完整归档已下载并核对SHA-256：`development_complete_20260922.tar.gz`，3,255,326 bytes，`5afe534afdf6bd28941faba06736be1324f9e94e34ae6bb31370a6be3768bd36`。包括v1失败gate、v2真实运行、后验审计、9/12任务源检查。原始证据不覆盖。

正式来源流量固定为12次共同初译，每次最多16,384输出token。取得非空真实候选后，其语法、导入、执行、数值或状态错误均由统一初始验收判定，所有失败进入修复集合。API无返回、空输出或不可取得候选单列生成失败，保留费用，不制造占位代码，不加入修复分母。初译已通过程序单独报告。四方法的修复分母为实际初始失败数，绝不按修复胜负筛选。

`natural12_v1`是首次准备快照，未调用API。`natural12_v2`在首次调用前澄清语法失败仍入组，保留v1全部记录。v2共同初译/初始验收已经完成，原PID为 `3437085`，日志为远端 `natural12_v2/translation_and_initial_check.log`。manifest SHA-256为 `86cd79ff7037a5435b6d5abfe74a87b95730b6859888f8dffdbcfd95a8509f0c`，pretranslation hashes SHA-256为 `556d8ce77d7b800fca71cbee1b78519669c2dbb1e4760b6ff0f8cea3ffb75588`。

用户已明确授权实验子代理独立完成初译、筛选、四方法执行、监测与审计，无需再等主代理批准启动。`formal_dispatch.py prepare`将筛选结果、条件网格、方法hash、预算和CPU组写入可审阅launch manifest；随后`launch`持久运行，最多2个API worker，各有独立workspace和两个CPU核。每条件40调用、4提交、120,000输出token和1,800秒不变；不自动重试失败条件。共享初译实际费用在每方法的对应任务端到端账本计一次，生成失败/初译通过的来源流量及费用另记。全部最终记录完成后据实更新接受数，不沿用旧六例数字。

12次初译均取得API响应，实际返回模型名为 `deepseek-flash`，请求模型名为 `deepseek-v4-flash`。其中10次生成非空候选，8个通过三种子初始验收，2个失败进入全部四方法的条件修复比较。通过者为CNN分类、超分辨、VAE、循环语言模型、Actor-Critic、REINFORCE、GAT和GPT-nano。时间序列候选把二维输入按三维索引，触发IndexError；ResNet候选返回了非空但截断的代码，首行SyntaxError，按既定规则保留在修复集合。GAN生成器和Transformer语言模型两次响应均耗尽16,384输出token额度且没有正文，记为生成失败，其费用留在12来源账本中。没有为这两项制造候选或补发初译。

选择文件SHA-256为 `dd4864873d813c9ebca58e4154c298fb40ab4e80a42980c7daa61df1ce2ea8e0`，翻译后输入hash清单SHA-256为 `df1f2708a4e271d9a7975dc3bb1e208eb2b757c1efbc5670dc9b75a52bb4968a`。2任务×4方法的正式launch manifest SHA-256为 `f78fe078c66e9cd9375c5bbfbca4660b383168c440ce978824a706eb59dcad64`，冻结dispatcher SHA-256为 `f820d3b54ba91e93eeb9a6f3f4d2117b9045c63d0ebec2fcf6edb9cf9f74dd76`。正式调度PID为 `3473891`，两组CPU为 `[0,1]`、`[2,3]`。结束后由 `finalize_formal.py`（PID `3502833`，CPU `[0,1,2,3]`）一次性执行最终复验、原始usage核对和证据清单归档；不触发新的API调用。

## 正式比较完成结果

八个条件均已结束，四方法均通过时间序列任务、未通过ResNet，最终修复接受为1/2。两项来源在任何修复结果产生前即按共同初始验收选入；初始错误分别为输入索引错误与非空截断代码的语法错误。12个来源只产生两个待修任务，尚未达到扩大修复比较规模的目标。本轮保留为自然初译流量和两例修复的证据，是否用于论文及如何处理旧六例由后续整体方案决定。

| 方法 | 修复接受 | 修复调用 | 修复输入token | 修复输出token | 修复总token | 两任务端到端token | 全12来源端到端token |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LaDiM | 1/2 | 35 | 1,710,061 | 130,005 | 1,840,066 | 1,871,493 | 1,979,790 |
| Direct LLM | 1/2 | 28 | 642,831 | 118,104 | 760,935 | 792,362 | 900,659 |
| MatchFixAgent | 1/2 | 23 | 225,734 | 33,180 | 258,914 | 290,341 | 398,638 |
| SWE-agent | 1/2 | 66 | 982,362 | 31,170 | 1,013,532 | 1,044,959 | 1,153,256 |

12次共同初译使用29,455输入token与110,269输出token，合计139,724。其中两项待修任务的初译为31,427 tokens。表中两任务端到端费用为各方法全部修复费加31,427；全来源费用为各方法全部修复费加139,724，包含初始通过和空正文生成失败。共同初译后再执行各方法修复，均有9/12来源最终通过。四方法共享同一初译批次，整轮实际总消耗为164调用、4,013,171 tokens；汇总实际账单时初译只计一次。

时间序列任务中，LaDiM、MatchFixAgent、SWE-agent的首个验收记录通过，Direct LLM的第二个验收记录通过。四方法均修复了每步输入切片与输出拼接形状，随后通过三个种子的三步梯度、更新和参数检查。该修复的代码变化主要恢复了可执行的张量形状；通过训练验收证明修复后轨迹一致，尚未提供定位并纠正独立训练语义错误的成功案例。

ResNet条件保留全部失败费用。LaDiM有3条验收记录，最后耗尽120,000输出token；修复阶段16调用占1,646,642 tokens，诊断6调用占50,200。Direct LLM完成4条验收记录，全部未通过。SWE-agent耗尽40调用，最终候选未通过。MatchFixAgent调用原生完整编排后，控制流与数据流分析器解析共享的截断候选时报告首行SyntaxError；原生异常被现有接入层记为`infrastructure_error`，4次已完成模型调用保留，候选未改动。其具体失败发生在原生语法处理阶段，网络和依赖运行正常；原状态码不改写，数值测量记为n/a。未为任何失败条件增加重试或修复baseline代码。

LaDiM、Direct LLM与SWE-agent均将ResNet的截断候选改成可执行实现并接受三步训练检查，最终仍存在数值差异。这轮因此实际测试了训练行为，但成功修复证据来自时间序列的形状错误。数值记录的`0:`、`1:`、`2:`分别表示第一、第二、第三个优化步；部分智能体诊断把`1:`误称第一步，分析以数组记录为准。

最终复验中，这三个方法的ResNet第一步全部数组均通过。种子8101在第二步的梯度、更新和参数开始超阈值，第三步扩展到loss、输出和buffers；8102到第三步才出现梯度、更新和参数失败；8103第二步先出现梯度失败。LaDiM与Direct LLM在三个种子分别失败173、88、115个数组，SWE-agent为173、90、115。差异由完整数组验收确认，当前证据尚未把它唯一归因于某项候选计算或跨后端的数值传播机制。

## 最终审计与归档

`audit_formal.py`对8个最终候选分别复验3个种子，24项结果全部复现原判定：时间序列12项通过，ResNet的9项可执行结果未通过数值验收，MatchFixAgent的3项因SyntaxError无法取得数值测量。冻结输入、原始usage及生产依赖检查均通过，`backend_flags`为空。完成标志与各项通过标志分别检查，未将`complete=true`直接解释为所有核查通过。

`audit_frozen_evidence.py`另行执行无API独立审计：核对248项冻结hash记录、各workspace的公共只读文件、152次修复的request/metadata/response一一对应和调用总数、全部未知usage计数为零，以及12次初译usage和总账。从公共`source.py`与冻结NPZ重放2任务×3种子的三步PyTorch源轨迹，1,908个数组与冻结参考逐值完全相同；独立NumPy检查重新计算最终目标NPZ中6,042个数组的逐元素阈值，逐数组判定和最终接受均一致。源参考重放排除了公共源导出或参考数组不一致这一具体疑点。无候选修改、额外模型调用或实验条件重跑。

独立审计脚本首次执行因Python导入公共源时产生的两份bytecode缓存进入文件遍历而停止，尚未输出最终审计报告；随后禁用bytecode写入并只按冻结清单确定待核对文件，清除这两份已确认不属于原始清单的缓存后完成审计。该修正仅涉及新增的审计工具，冻结实验程序、输入、候选和结果字节保持原样。

交付文件位于 `output/jax-expansion-20260922/formal/`：`formal_report.json`及`.md`提供紧凑结果，`formal_summary.json`为原始调度摘要，`independent_audit.json`保存独立检查，`formal_launch_manifest.json`保留冻结预算与方法hash，`formal_archive_record.json`与`formal_evidence_inventory.json`记录归档和每份原始文件的hash。完整元数据归档为 `output/jax-expansion-20260922/formal_metadata_complete_20260922.tar.gz`，371,568,164 bytes，SHA-256 `005a21a6640ce24fe28baa692a1ae5eb7eed64d1af7249b218bdf4861bd62485`；本地归档大小、归档hash和清单hash均已核对。226份NPZ共5,202,234,201 bytes仍保留在远端原始运行目录，逐文件hash在清单中；大归档和NPZ不加入Git。

实际验证命令如下。远端独立审计绑定CPU2、3，未占用另一实验的CPU4、5；原正式调度和finalizer已完成退出。

```bash
# 本地：数值比较已有测试，6项通过。
.venv/bin/python -m unittest discover -s experiments/jax_expansion_20260922 -p test_formal_validation.py
.venv/bin/python -m py_compile experiments/jax_expansion_20260922/audit_frozen_evidence.py experiments/jax_expansion_20260922/summarize_formal.py

# 远端：独立审计，全部汇总标志为true；输出已复制为independent_audit.json。
taskset -c 2,3 /media/main/whj/miniconda3/envs/torchax311/bin/python \
  /media/main/whj/projects/torch4ms/experiments/jax_expansion_20260922/audit_frozen_evidence.py \
  /media/main/whj/projects/torch4ms/experiments/jax_expansion_20260922/natural12_v2 \
  /media/main/whj/projects/torch4ms/experiments/jax_expansion_20260922/independent_frozen_audit.json

# 本地：从已核对hash的原始归档与独立审计生成报告。
.venv/bin/python experiments/jax_expansion_20260922/summarize_formal.py \
  output/jax-expansion-20260922/formal_metadata_complete_20260922.tar.gz \
  output/jax-expansion-20260922/formal/independent_audit.json \
  output/jax-expansion-20260922/formal
```

## 结果的用途与后续所缺证据

本轮可以回答：12个公开模型工作负载在一次固定预算自然初译后的生成与初始通过情况，以及四种冻结方法在同样两个自然失败候选上的行为、终止原因和成本。两例修复的接受结果完全相同；MatchFixAgent在ResNet上提前因原生解析失败终止，较低费用包含这种终止行为。方法效率排序需要更多独立、具有代表性的修复任务，且需要把成功、失败原因与费用共同分析。

若后续获准扩大比较，应先固定更大的公开来源池、来源去重规则、覆盖的训练机制和总初译预算，再统一进行初译、记录全部生成失败与初始通过，最后把所有取得非空候选的初始失败交给各方法。准备阶段可预先规定进入正式比较所需的最小独立失败任务数；若固定来源池不足，则报告不足并另行设计下一批。应覆盖可执行但梯度、状态或多步更新错误的自然候选，并在来源层区分普通形状/语法错误与训练行为错误。候选若要承担优化器实现，还需在新协议中明确该职责并先验证验收后端；本轮优化器由可信Optax执行。上述建议未启动新来源、初译或实验。
