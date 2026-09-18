补充以下三组实验。我们希望检验分层诊断能否被不同修复系统复用、能否扩展到普通跨语言程序，以及相比现有框架迁移工具有什么收益。实验不预设我们一定更好，需要保留完整结果和失败案例。

1. **验证分层诊断的可插拔性。** 注释 1

  这组实验要回答：分层诊断带来的收益，能否在 SWE-agent、MatchFixAgent 等已有系统中复现。如果接入后这些系统也能更快、更省 token 地完成修复，就能支持“诊断模块可以独立复用”的结论，说明方法具有跨修复系统的扩展性。

  具体做法是保留 SWE-agent 和 MatchFixAgent 各自的代码浏览、编辑、测试和修复流程，只增加诊断报告的接入接口，不用 MARS 的修复 agent 替换它们。每次候选代码变化后重新运行验证，确保反馈对应当前代码。每个系统分别运行以下三种条件：

| 条件          | 提供给修复 agent 的信息                          | 比较目的                |
| ----------- | ---------------------------------------- | ------------------- |
| 原有反馈        | 保留该系统原本获得的测试结果、执行输出和分析报告                 | 确定系统原有的修复能力         |
| 原有反馈＋全部原始测量 | 额外提供执行状态、前向数值、梯度和参数更新差异，但不提供阶段选择和针对性修复指导 | 检查增加训练观测本身能带来多少收益   |
| 原有反馈＋分层诊断   | 使用与上一条件相同的测量，再提供首先失败的阶段、支持证据、可用位置和对应修复指导 | 检查将测量组织成诊断能否进一步帮助修复 |

  三种条件使用同一组原始50个故障实例及相同初始候选，固定 LLM、温度、允许编辑的代码、验收标准和最多四次修复尝试。诊断可以建议检查什么位置，但不能扩大编辑权限，也不能使用隐藏的故障标签或标准补丁。每次提交候选补丁算一次修复尝试，agent 内部的多次 LLM 和工具调用另外完整记录。报告1、2、4次尝试内的接受率、总 token、每个接受修复的 token 和耗时，并分析哪些故障受益。如果最终接受率提升不大，但首次接受率提高或成本下降，同样能体现插件的价值。“全部测量”与“分层诊断”的比较评估阶段选择和修复指导的共同作用。

2. **验证分层诊断思想能否扩展到跨语言深度学习代码翻译。**

**实现深度学习训练代码的跨语言迁移**，同时做“诊断模块接入其他方法”和“我们完整方法与其他方法直接比较”两类实验。这样可以在保留现有训练诊断机制的情况下，检验方法能否扩展到不同源语言。

1. **任务从哪里选、怎样整理。**

  主实验采用 Java/DJL→Python/PyTorch，从 [D2L Java](https://github.com/deepjavalibrary/d2l-java) 和 [DJL 官方训练示例](https://github.com/deepjavalibrary/djl/tree/master/examples/src/main/java/ai/djl/examples/training) 中整理约20个独立训练程序，覆盖 MLP、CNN、序列模型及不同训练操作，最终数量以预检通过的清单为准。每个任务必须包含模型计算、损失、反向传播和参数更新；只有推理、模型加载或权重转换的示例不纳入。Notebook 可以提取为独立程序，保留必要辅助函数和原始来源，去掉绘图等无关部分。可以缩小数据量、训练步数和模型规模，但必须记录修改并保留所研究的训练行为。随机种子重复和仅改变网络宽度的版本，不计为独立任务。

  补充实验从 [PyTorch C++ 示例](https://github.com/pytorch/examples/tree/main/cpp) 的 regression、mnist、dcgan 中整理 C++/LibTorch→Python/PyTorch 任务，结果按语言方向分别报告。任务选择依据源程序能否运行、训练过程能否观测，不依据我们方法能否翻译成功。

java和c++两种语言选一个就行了，感觉c++可能会简单一些，因为有torch的官方示例，不过java可能相关的库要多一些，可以先搞一点点看看难度。

2. **我们的方法具体需要改什么。**

  保留现有三类诊断信号、失败阶段选择和迭代修复机制，主要增加源语言运行与观测适配器：能够编译、执行 Java/C++ 源程序，采集异常、前向输出或损失、反向传播后的梯度，以及更新前后的参数，并转换成统一报告。Python 目标程序使用对应的训练观测接口。诊断报告中的位置需要能指向实际文件和模型模块。

  两端读取同一份输入和初始参数，明确参数名称、张量布局、损失归约方式、优化器设置与状态的对应关系；不能仅设置相同随机种子就假定初始化相同。优先选择确定性的训练配置，对 Dropout 等随机操作另行处理随机性。先用正确对照实现验证采集与比较接口，固定验收阈值后再评估翻译方法。

  翻译和修复提示中增加源语言、目标 PyTorch API、依赖及运行入口说明，同时让源码读取模块支持 `.java`、`.cpp` 文件。现有实现中写死的框架名称、Python 源码分析和文件路径假设需要按语言配置。**核心诊断不增加新的阶段，改动集中在代码读取、执行采集和接口映射。** 请记录实际修改的模块和适配工作量，以便说明扩展成本。

3. **第一类：把我们的诊断模块接到其他方法上。**

  在上述跨语言任务上，使用预先冻结的、由统一初始翻译流程产生的失败译文，分别让 SWE-agent、MatchFixAgent 修复。每个系统比较“原有反馈”“原有反馈＋全部训练测量”“原有反馈＋分层诊断”，固定初始代码、LLM、编辑范围和四次修复预算，保留宿主系统自己的修复流程。

  这类实验检验：我们的诊断进入跨语言训练代码场景后，是否仍能帮助其他系统提高修复接受率、减少尝试和 token。使用同一批失败译文，可以排除初始翻译质量不同造成的影响。自然翻译错误与人为注入故障如同时使用，必须分开统计。

4. **第二类：我们完整方法与其他方法直接比较。**

  让我们的方法从 Java/C++ 源程序开始，完成初始翻译、验证、诊断和修复。完整方法对比包括 Direct LLM 单次翻译、Direct LLM＋测试反馈修复（源程序 → LLM 生成初始译文 → 编译、运行可见测试 → 将当前代码、报错和测试结果交给同一个 LLM → 修改代码，最多修复四轮）、Direct LLM＋SWE-agent 修复、Direct LLM＋MatchFixAgent 修复，以及 InterTrans。资源允许时增加 RepoTransBench 配套 RepoTransAgent 和 Java→Python 方向的 AlphaTrans。

| 对照系统                                 | 在实验中的具体流程                                       |
| ------------------------------------ | ----------------------------------------------- |
| **Direct LLM＋SWE-agent 修复**          | 用统一的初始翻译流程生成候选，再由 SWE-agent 浏览代码、执行测试和修复。       |
| **Direct LLM＋MatchFixAgent 修复**      | 使用同一批初始候选，由 MatchFixAgent 进行分析和修复。              |
| **RepoTransBench 配套 RepoTransAgent** | 使用其自身的仓库翻译流程，从源程序生成目标程序并迭代验证。                   |
| **AlphaTrans**                       | 在 Java→Python 任务上使用其程序分解、翻译和验证流程；先确认能处理 DJL 依赖。 |

前三种迭代修复对照使用统一流程生成的同一批初始候选；具有自身翻译流程的方法按其原有算法运行。所有方法使用统一的最终训练验证标准，端到端成本包含初始翻译及全部分析、测试和修复调用。*RepoTransAgent、AlphaTrans 先检查深度学习依赖的兼容性，再确定是否纳入正式比较。*各方法自行生成初始译文，使用相同源程序、任务说明和评估接口。

  AlphaTrans、RepoTransAgent 可作为候选基线，但需先确认其流程能处理 DJL、LibTorch 等外部库依赖。不能为了让基线运行而删掉关键训练逻辑。对于 InterTrans，应保留其中间语言搜索算法，补充训练任务执行环境；仅运行 CodeTransEngine 的直接翻译模式不能算 InterTrans。

  这类实验检验完整方法的跨语言迁移效果，报告初始翻译正确率、最多四轮修复后的最终正确率及全过程成本。它与上一类插件实验分别统计：前者评价完整系统，后者评价诊断给其他系统带来的增益。

5. **验收与结果记录。**

  正确性验收覆盖执行、前向数值、梯度和参数更新，单步配对检查与短程连续训练分别记录，并在未用于修复反馈的输入和初始化上复验。报告1、2、4轮修复结果、所有调用的 token 和耗时，以及不同错误类型的表现。每个任务建议使用三个种子，按任务汇总并保留逐次结果。记录源码 commit、任务提取修改、依赖版本、初始化与参数映射、候选补丁和诊断日志。新实验单独归档，不与原50实例主实验合并统计。

3. **补充 PyTorch→MindSpore 的实际迁移工具对照。**

  这组实验用于比较我们的方法与现有迁移工具的实际能力，观察差异主要出现在代码转换、程序运行还是训练行为保持。补充 [MindConverter](https://github.com/mindspore-ai/mindinsight/tree/r1.7/ecosystem_tools/mindconverter)、[MSAdapter](https://openi.pcl.ac.cn/OpenI/MSAdapter)，环境具备时加入华为 X2MindSpore。

  在相同源程序、输入、初始化和训练设置下，分别报告转换完成、运行成功、实际产生梯度与参数更新，以及配对数值验证结果。MindConverter 主要转换网络结构和权重，若需要补充训练脚本，必须使用预先固定的统一封装并记录人工修改，避免把额外人工工作算成工具自动完成。工具本身不支持的任务和环境无法运行的任务分别记录。

4. **统一实验记录，保证结果能够解释和复现。**

  先检查环境、参考程序和测试是否可运行，再冻结任务清单与配置，可以适当根据我们方法的表现筛选一下任务。可配置 LLM 的对照统一模型版本与采样设置；ExeCoder、TransCoder-ST 等专用模型如纳入比较，应单列模型和训练条件。保存逐实例结果、每轮候选与补丁、诊断报告、全部调用成本、原始日志、依赖版本、代码 commit 和运行命令。接受率、定位准确率及配对数值验证分别统计；缺失测量记为 `n/a`，没有接受修复时的“每个接受修复成本”也记为 `n/a`。新实验独立归档，保留原50实例主实验及其原有验收口径。







下面可以直接作为实验文档的链接附表。**自建对照没有独立的官方仓库**

| 方法／实验条件                                   | 源码或文档链接                                                                                                                                                        | 使用说明                                     |
| ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| 我们的方法 LaDiM（原称 MARS）                      | [论文与实验索引](https://github.com/jayus71/migration_agent)；[实验实现](https://gitee.com/feixiao13/ascend-torch4ms)                                                      | 完整方法及分层诊断模块                              |
| Direct LLM 单次翻译                           | 自建对照，无独立官方仓库                                                                                                                                                   | 使用统一 LLM，根据源程序和目标框架说明生成一次译文              |
| Direct LLM＋测试反馈修复                         | 自建对照，无独立官方仓库                                                                                                                                                   | 在直接翻译后增加测试反馈与最多四轮修复                      |
| SWE-agent／Direct LLM＋SWE-agent 修复         | [官方仓库](https://github.com/SWE-agent/SWE-agent)                                                                                                                 | 作为修复基线，以及诊断插件的宿主                         |
| MatchFixAgent／Direct LLM＋MatchFixAgent 修复 | [官方仓库](https://github.com/Intelligent-CAT-Lab/MatchFixAgent)                                                                                                   | 作为翻译验证与修复基线，以及诊断插件的宿主                    |
| InterTrans                                | [论文复现仓库](https://github.com/RISElabQueens/InterTrans)；[后续实现 CodeTransEngine](https://github.com/CodeTransEngine/CodeTransEngine)                               | 运行其中间语言搜索算法；CodeTransEngine 的直接翻译模式应另外命名 |
| RepoTransBench 配套 RepoTransAgent          | [项目仓库](https://github.com/DeepSoftwareAnalytics/RepoTransBench)；[Agent 实现目录](https://github.com/DeepSoftwareAnalytics/RepoTransBench/tree/main/RepoTransAgent) | 仓库级翻译基线，使用这个全称以区别同名方法                    |
| AlphaTrans                                | [官方仓库](https://github.com/Intelligent-CAT-Lab/AlphaTrans)                                                                                                      | Java→Python 候选基线，需预检 DJL 依赖兼容性           |
| ExeCoder（可选）                              | [官方仓库](https://github.com/microsoft/ExeCoder)                                                                                                                  | 专用翻译模型，先确认权重和微调成本                        |
| TransCoder-ST／TransCoder-IR（可选）           | [官方 CodeGen 仓库](https://github.com/facebookresearch/CodeGen)                                                                                                   | 专用翻译模型对照，与统一 LLM 的实验分开说明                 |

深度学习跨语言任务的源码与运行参考如下：

| 名称                 | 对应链接                                                                                                                                                                                                                      | 在实验中的用途                           |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| D2L Java           | [源码仓库](https://github.com/deepjavalibrary/d2l-java)                                                                                                                                                                       | Java 训练程序的主要来源                    |
| D2L Python         | [源码仓库](https://github.com/d2l-ai/d2l-en)                                                                                                                                                                                  | 同类算法的 Python 实现参考；需核对具体版本和训练语义    |
| DJL 官方训练示例         | [训练代码目录](https://github.com/deepjavalibrary/djl/tree/master/examples/src/main/java/ai/djl/examples/training)                                                                                                              | 选择 MNIST、LSTM、Seq2Seq、时间序列等训练任务   |
| DJL MNIST 训练示例     | [Java 源码](https://github.com/deepjavalibrary/djl/blob/master/examples/src/main/java/ai/djl/examples/training/TrainMnist.java)；[运行说明](https://github.com/deepjavalibrary/djl/blob/master/examples/docs/train_mnist_mlp.md) | 建议首先用于验证 Java 任务接入流程              |
| DJL PyTorch 后端     | [官方说明](https://github.com/deepjavalibrary/djl/tree/master/engines/pytorch/pytorch-engine)                                                                                                                                 | 配置 Java 端使用的 PyTorch 底层库及版本       |
| DJL 梯度读取接口         | [NDArray 接口源码](https://github.com/deepjavalibrary/djl/blob/master/api/src/main/java/ai/djl/ndarray/NDArray.java)                                                                                                          | `getGradient()` 等观测接口的实现参考        |
| PyTorch C++ 训练示例   | [示例目录](https://github.com/pytorch/examples/tree/main/cpp)                                                                                                                                                                 | C++/LibTorch→Python/PyTorch 的任务来源 |
| C++ 回归、MNIST、DCGAN | [regression](https://github.com/pytorch/examples/tree/main/cpp/regression)；[mnist](https://github.com/pytorch/examples/tree/main/cpp/mnist)；[dcgan](https://github.com/pytorch/examples/tree/main/cpp/dcgan)              | 首批 C++ 训练任务候选                     |

PyTorch→MindSpore 工具对照的入口如下：

| 工具             | 对应链接                                                                                                                                                                                         | 使用说明                                    |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| MindConverter  | [官方源码](https://github.com/mindspore-ai/mindinsight/tree/r1.7/ecosystem_tools/mindconverter)；[迁移文档](https://www.mindspore.cn/mindinsight/docs/en/r1.7/migrate_3rd_scripts_mindconverter.html) | 主要转换网络结构和权重；额外训练封装需记录                   |
| MSAdapter      | [OpenI 仓库](https://openi.pcl.ac.cn/OpenI/MSAdapter)；[源码下载地址](https://gitee.com/mindspore/msadapter)                                                                                          | PyTorch 接口到 MindSpore 后端的适配工具           |
| 华为 X2MindSpore | [官方使用与环境说明](https://www.hiascend.com/document/detail/zh/mindstudio/500/quickstart/migrationtoolms_000002.html)                                                                               | MindStudio 中的脚本迁移工具；本次未确认官方 GitHub 源码入口 |

正式运行时，每个方法和任务源码都应记录实际使用的 **commit／release、依赖版本及本地修改**。原50实例上的插件对照沿用原冻结版本，新增实验另外记录版本。
