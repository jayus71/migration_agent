# 方法图设计审阅与下一轮生成建议

日期：2026-09-23。
核对版本：`85e5945`。
本轮用户要求暂停 PPT 转换，多看本地顶会主图库，分析最新图片并提供下一轮生成意见。
以下版式与措辞均为建议，尚未应用到论文或图形。

审阅图片为本任务最新附件 `codex-clipboard-02d8b4e1-3db1-4aee-a697-ca760227a657.png`，SHA-256 为 `a83985c7ae8cdd2f9be4153903c780fcd724406587ff4876b9be4a7d53a43a27`。
前一轮已按仓库规则将原有作者方法图及其生成器保存为检查点 `85e5945`；PPT 重建尚未开始，未生成新 PPT。

## 判断

最新图片的外框已经较整齐，主要问题转为信息层级和机制表达。
它完整罗列了系统组成，但两侧品牌标识、通用功能说明和仓库组件与核心诊断争夺注意力。
下一版应让读者首先看到：训练行为在哪里出现差异，这个差异怎样引导代码调查，以及修复结果如何经过验证。

建议保留现有角色、证据交接、修复历史和仓库机制，重新分配面积并把机制画成可追踪的对象关系。
这属于图形组织建议，不更改论文的贡献定位或已批准论述。

## 参考图及可借鉴内容

本轮在前一轮六张图的基础上又检查八张，共十四张本地图片。
只借鉴视觉组织，没有重新审查这些论文的方法或复用其图形素材。
图库根目录为 `../topconf-paper-figure-gallery/`，元数据来自 `data/figures.json`。

| 图库条目 | 可借鉴内容 |
| --- | --- |
| `images/neurips/final/neurips2024-27.jpg`，SWE-agent | 用明确标注的命令和反馈连接代理、接口与环境；接口占据视觉中心。 |
| `images/icml/final/icml2025-1070.jpg`，PatchPilot | 阶段之间传递测试、根因和补丁，验证有明确的输出和返回路径。 |
| `images/icml/final/icml2025-0978.jpg`，Nemotron-CORTEXA | 代码库、文件、实体、补丁、测试之间保持对象连续性；相同阶段共享颜色。 |
| `images/icml/final/icml2025-0703.jpg`，Improving Parallel Program Performance with LLM Optimizers via Agent-System Interfaces | 执行图及其变化直接表达优化发生在哪里。 |
| `images/acl/final/acl2025-2025.acl-long.881.jpg`，Revisit Self-Debugging with Self-Generated Tests for Code Generation | 中间状态和最终输出用不同结构表达，观测对象清楚。 |
| `images/iclr/final/iclr2025-0166.jpg`，Automated Design of Agentic Systems | 顶层循环简洁，归档内容通过局部展开解释，细节不与主流程争夺同一空间。 |
| `images/iclr/final/iclr2025-41.jpg`，Agent S | 用具体内容说明不同记忆和规划对象，边上明确标注信息传递。 |
| `images/aaai/final/aaai2023-25642.jpg`，Repair Is Nearly Generation | 同一代码错误、错误消息与编辑结果构成连续例子。 |
| `images/iclr/final/iclr2024-28.jpg`，MetaGPT | 角色与其产物建立对应。 |
| `images/neurips/final/neurips2023-05.jpg`，HuggingGPT | 按任务规划、模型选择和执行组织内容。 |
| `images/neurips/final/neurips2023-11.jpg`，Self-Refine | 反馈与修订的循环方向和对象直接可读。 |
| `images/aaai/final/aaai2025-32007.jpg`，VerilogCoder | 用信号与代码位置表达定位，而不只写定位模块名。 |
| `images/aaai/final/aaai2025-34505.jpg`，WebPilot | 规划结构与局部交互展开分层。 |
| `images/neurips/final/neurips2023-1177.jpg`，SwiftSage | 用具体历史、子目标和动作说明机制；其高文字密度不适合直接套用到本图。 |

## 具体调整

### 1. 收窄输入输出，放大诊断与修复

两侧改为紧凑的 `Source program / repository` 与 `Accepted target program / repository`，只保留小文件树及源、目标环境标记。
删去两侧重复出现的三组框架 logo，以及 `Arbitrary framework`、`Generalizable` 等无助于说明流程的能力标签。
Translator 缩成一个紧凑模块；把释放的面积给分层诊断、调查证据和验证反馈。
保留机器人时统一为同尺寸的小线稿图标。

主图采用上下两层，上层展示迁移、诊断、修复和验证，下层展示仓库共享支持机制。
Orchestrator 用较薄的共享控制条承接验证与反馈，不再占据与核心诊断同样强的视觉层级。
下层三个仓库模块保持同一顶线、同一标题高度和一致的内部留白，面积服从内容，不为外观整齐强迫所有顶层模块等宽。

### 2. 让 Layered Diagnosis 显示推理依据

保留源与目标两列，增加训练计算依赖的明确方向：`Execution → Forward values → Gradients → Parameter updates → Next forward`。
这条链表示计算依赖，不表示每一行都必须调用一次 LLM 或每个训练 step 重启诊断。

Execution 用执行结果符号；前向值用相近的观测；梯度处突出源与目标之间的差异。
异常强调应落在目标观测及差异位置，源侧仍作为稳定参照。
后续更新和下一次前向用中性灰表示待进一步调查或潜在传播，不以蓝色相同波形暗示其已验证通过。

从异常位置引出小的代码调查示意，展示 `Inspect code / Test hypothesis`，再形成 Evidence handoff。
这样读者能看见观测差异怎样影响调查，而不只是看到五行波形。

### 3. 用一个连续的小例子连接证据与修复

Evidence handoff 保留代码观察、测量、位置和假设，但采用一张紧凑的证据记录，并与被高亮的代码位置对应。
Repair Agent 使用同一位置的编辑示意，修复历史用“上一轮编辑及其检查结果”表达。
避免三条完全相同的 `Attempt ... ×`，它们占用空间却没有呈现历史怎样影响下一步修复。

当前 `model(x)` 改为 `model.forward(x)` 没有解释梯度差异的来源或修复依据，应移除。
可以从核实的现有案例选取代码；若只画概念例子，应明确标为 `Illustrative example`，不把示意补丁当作已测实验结果。

### 4. 改准控制流

按 `sections/methods.tex` 及既有诊断时机核对记录，初译先由 Orchestrator 验证，通过即可输出，失败才进入 Verifier 调查。
Verifier 交接证据后，Repair Agent 在持续会话中依据验证反馈继续修复。
不画成每轮必然在两个独立代理之间往返。

主线为初译候选、验证及接受；失败分支为诊断、证据交接、修复，再提交验证。
成功箭头从验证位置通向 Accepted target，失败反馈返回 Repair Agent 及其历史。
源程序与目标候选均应有明确的观测来源关系，避免 Source/Target 两列悬空。
所有连线连接实际对象，使用短标签说明 `Candidate`、`Evidence`、`Submission` 或 `Measurements`。
删除只指向大虚线框或空白处的双向箭头。

### 5. 仓库层展示实际作用

`Repository Structural Analysis` 保留小文件树，突出被调查的相关文件及其导入关系。
`Repair Dependency Graph Planning` 用带工作单元含义的节点代替无名圆点，并表现当前可处理单元。
`Evidence Retrieval / Context Reconstruction` 展示归档记录、相关证据取回及当前上下文之间的关系，保留修改后相关检查失效的含义。
三个组件作为共享支持机制；不强行串成每次修复都必须完整执行的三个阶段。

### 6. 统一视觉语法

采用纯白背景、平面浅填充、细描边及深灰正文。
建议主色蓝 `#4C78A8`，修复及接受用绿 `#5B9E8A`，仓库层用低饱和紫 `#8D82B8`，差异用红 `#C95F65`。
对应浅底可用 `#EDF3F9`、`#EDF6F2`、`#F2EFF8`，控制条使用 `#F4F5F7`。
这些颜色是为本图提出的设计值，不是从某张参考图取样的色号。

模块名、机制名与注释形成三个字号层级。
大模块只保留必要边框，内部对象优先通过留白、细分隔线和局部高亮区分。
圆角、箭头头部、描边粗细与图标风格一致，连线尽量正交。
颜色承担固定含义；绿色通过状态同时带勾，红色差异同时有位置或符号，保证灰度下也可辨认。

## 当前图片中的内容一致性

图中 Python→Java 的大标识容易让读者把它理解为论文展示的具体迁移方向。
本稿主比较对应 PyTorch→MindSpore、Java/DJL→Python/PyTorch，另有 PyTorch→JAX 研究。
建议输入输出使用通用源/目标环境；需要举例时只用这些已报告方向，避免在两侧机械复制全部框架 logo。

Orchestrator 执行、调度和返回检查结果，与 Verifier/Repair 的 LLM 调查和编辑角色区分。
训练计算链与候选提交后的修复迭代也应分开表达。
这些核对依据本地当前方法源码和既有记录，本轮没有重跑实验。

## 可直接用于下一轮生成的提示词

请以上传的 LaDiM 架构图为内容参考，重新设计为机器学习论文中的方法总览图。
保留 Translator、Verifier Agent、Repair Agent、Evidence handoff、Repair history、Orchestrator 和 Repository Context Management，但重新组织信息层级，突出训练行为差异如何引导代码调查与修复。

采用横向画布、纯白背景和规整网格。
输入输出压缩为窄小的代码/仓库对象，Translator 紧凑；把上层主要空间交给 Layered Diagnosis、调查证据及 Repair Agent。
下层保留三个仓库支持模块，使用一致的标题基线、间距和图标风格。
Orchestrator 作为薄的共享控制与验证条，清楚标出调度、检查候选和返回测量的职责。

Verifier 中用源/目标两列配合训练计算依赖链：Execution、Forward values、Gradients、Parameter updates、Next forward。
Execution 使用状态符号，不画成波形。
用一个明确标为 Illustrative example 的例子表现前向观测接近、梯度观测出现差异，源侧保持蓝色，目标异常及差异位置用红色。
后续阶段用中性灰表示继续调查，不暗示已通过检查。
从差异位置连接到 Inspect code / Test hypothesis，再形成包含代码位置、测试测量和假设的紧凑 Evidence handoff。
Repair Agent 的代码编辑与该例子保持因果一致；不要使用 model(x) 改成 model.forward(x) 作为梯度故障的修复。
Repair history 显示过去编辑与其测试反馈，避免重复三条只有 Attempt 和叉号的列表。

控制流程必须准确：Translator 生成候选，Orchestrator 先验证；通过时得到 Accepted target program，失败时进入 Verifier 调查并交给 Repair Agent。
Repair Agent 提交修改，Orchestrator 返回测量供其下一轮修复。
不要绘制每轮都重新调用独立 Verifier 的双向循环。
源程序和目标候选向验证提供观测，所有箭头有明确端点，需要时用 Candidate、Evidence、Submission、Measurements 等短标签说明所传递的对象。

仓库层保留完整模块名 Repository Structural Analysis 和 Repair Dependency Graph Planning，分别画相关文件/导入关系及有含义的工作单元依赖图。
Evidence Retrieval / Context Reconstruction 画出归档证据、相关记录取回和当前上下文，保留改动后受影响检查需要更新的含义。
这三个模块是共享支持机制，不画成每次都必须依次执行的流水线。

删除两侧重复框架 logo、Arbitrary framework、Generalizable 及重复功能口号。
输入输出使用通用 Source/Target environment；如果展示具体方向，可用 PyTorch→MindSpore、PyTorch→JAX、Java/DJL→Python/PyTorch 的紧凑例子。
使用低饱和蓝、绿、紫和灰，异常位置少量红色；细描边、统一小圆角、正交连线、同尺寸小线稿图标。
文字使用清晰的无衬线字体，模块名、机制名和注释三级字号。
避免渐变、发光、立体数据库、大品牌标识和层层套框；把细节量控制到缩放后仍可读。

## 核验范围

本轮核对了附件、十四张图库图片、当前方法及仓库协调流程，并阅读既有诊断时机和修复案例记录。
未修改论文、图形或生成脚本，未制作 PPT，未运行实验。
其他有效反馈沿用其原有核验日期，本轮不声明完成全文或版面回归检查。
