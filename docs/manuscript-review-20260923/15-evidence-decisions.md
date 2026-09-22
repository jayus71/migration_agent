# 主代理证据核对与取舍

2026-09-23，基准 `d1d6a53`。本文件用于说明综合方案如何处理章节报告中的疑点，不属于论文正文。本轮只读已有代码和实验记录，没有运行迁移、修复或模型实验。

## 已解决的对应关系

| 检查项 | 已核对的证据 | 对方案的决定 |
|---|---|---|
| Query 是否调用LLM | `output/maintext-ablations-20260918/frozen_v4_agent.py` 中阶段循环和模型请求；方法 §3.1 已定义 M | 模型符号保留，真实调用显式命名 LLMCall，共享步骤命名 LLMToolStep；确定性工具不加LLM。 |
| 交接和历史 | 同文件 `_handoff_to_fixer`、`repair`、`_stage` | 交接提供带Verifier来源的公开调查记录；修复会话持续。伪代码不能把完整证据擅自改为只传一个摘要。 |
| 编辑后测试 | 同文件阶段完成判定及工具结果处理 | 新的生产代码编辑使先前测试不能作为本次编辑后的测试；精简算法仍保留这一条件。 |
| 仓库外部验收 | `scripts/repository_migration_experiment.py:311` 至修复循环结尾 | 首次评估失败后调查一次；每次实际修复阶段之后评估完整仓库，再检查接受、预算和错误停止条件。阶段与所有工作单元共用累计预算。 |
| 仓库结构分析和规划 | `scripts/repository_agent_mode.py` 的 `inventory`、工具分派、计划与工作单元处理 | 结构分析由agent请求触发；规划由agent提出。不能为算法图示新增固定初始扫描或逐单元Verifier循环。 |
| 版本化证据 | 同文件 `record_test`、`evidence_state`、`working_set`、`_rebuild_context` | 新测量替代同一测试的旧测量；按代码版本判定是否仍适用；恢复此前读过、文件仍一致且与当前单元相关的代码。完整结构化发现及工具观测有实现支持。 |
| 局部检查失效 | 同文件计划与编辑操作、依赖传播 | 文件变更使涉及单元及已声明后继的检查失效；计划变化也可使相关检查失效。不新增自动发现所有依赖的主张。 |
| 六例JAX预算 | `scripts/run_maintext_jax_autonomous.py` 的 manifest 构造，`max_repair_attempts=4` | 保留每任务四次提交上限、实际首次通过、6/6、76/57 calls及原token。旧历史三轮记录不替换本研究预算。 |
| 信号表 basic checks | `docs/maintext-training-signal-independent-review-20260918.md` 的最终结果与口径段 | 基础设置还检查输出结构、实际目标框架执行、源程序未变及训练记录，不只看退出码。可在附录解释，主文不列配置键。 |
| 3/12、4/12、31/18 | 检测图生成代码、现有冻结检测数据及该研究协议 | 梯度错误12次中3次、更新错误12次中4次在50步内出现超阈loss差异；均值曲线分别31、18步。与LaDiM在每次运行第1步检测分开陈述。 |
| 两项仓库组件参照 | `data/paper_figures/README.md`、`make_cumulative_components.py` 的输入映射 | 6,047,074→1,936,579与2,651,248→2,126,900来自分别执行的比较，不能合并成本参照或相加68.0%与19.8%。 |
| 程序组件与自然修复主比较 | `slim_main.csv`、`recovery_final.json`及来源说明 | 自然修复主比较13,206,863 tokens，启用编辑格式辅助的组件完整参照15,547,813 tokens。各自配置说明保留，不把二者强行统一。 |

主文当前实现与历史研究的版本名只在来源文档中出现。已核对的共同机制足以支持方案中的抽象过程；实施伪代码时仍以当前冻结实现及其主控映射为准，不将历史配置参数搬进主方法定义。

## Java/DJL 两处文字错误

证据为 `data/audits/unified50-preflight-20260918/formal_launch/results_audit_final.json` 中 cross_language 的最终行，以及 `final_review/cross_language/manifest.json` 的任务映射。

| 方法 | 通过的应用 | 通过的教材例子 | 总计 |
|---|---|---:|---:|
| LaDiM | 水果分类迁移学习应用，内部映射 task_010 | 8 | 9/18 |
| MatchFixAgent | 同一水果分类迁移学习应用 | 7 | 8/18 |
| SWE-agent | MNIST LSTM应用，内部映射 task_002 | 7 | 8/18 |
| Test-guided repair | 无 | 7 | 7/18 |

因此，附录A的 `SWE-agent and MatchFixAgent each accept the same application` 必须改正。可写为：

> LaDiM accepts one application and all eight textbook examples. MatchFixAgent accepts the same application and seven examples, while SWE-agent accepts a different application and seven examples. Test-guided repair accepts seven examples.

审计中首次已通过的程序映射为 task_012，是教材示例。当前 `All repair methods preserve the initially accepted application` 把它误写成应用。该句对结果主线没有独立作用，方案直接删除。内部task编号仅用于本文件定位，不能放入论文。

主文关于LaDiM包含MatchFixAgent全部已通过程序、并新增一个循环网络例子的陈述正确。表中接受数及成本保持不变。

## 尚不新增的细化

部分报告建议补充比原文更细的定义。以下项目未在本轮完成全部原始实现核验，不标记为已经解决，也不因此给正文增加限制句。

| 项目 | 实施时的处理 |
|---|---|
| BF16的相对容差及归一化公式中的epsilon | 如补充具体值，先查对应冻结评价器；当前方案保持既有阈值，不推断。 |
| 单次131,072与累计120,000输出token的具体适用方法及执行边界 | 分方法核对冻结runner后再完善附录措辞，不能只按数值大小推断预算错误。 |
| 原生JAX附录每任务预算、调用数是否包含调查 | 核对formal配置与各condition账本后写成每方法每任务，保留表内现有合计。 |
| 推荐仓库的File coverage、Documentation and dependencies及两种loss的精确定义 | 先映射评价器检查项再定显示名称；不将六条模型执行路径改成六个独立模型。 |
| 附录规划消融的position model及具体退化原因 | 核对模型公开名称与修改记录，保留已报告轨迹，不推断新的因果链。 |
| 首次确认的实际后端及工具设置在不同研究中的对应 | 保留研究分组和既有配置差别；不把Direct repair与LaDiM共享工具写成所有baseline都共享。 |

这些是局部措辞的证据定位要求，已明确的删重复、术语替换、TorchAX移动及算法组织调整可按综合方案推进。

## 不采用的候选

- 不因“完成迁移”有更窄的指标写法，就削弱已经定义评价标准的 `completes all 50`。
- 不为通过逐句审查而改动已确认的摘要8句。
- 不直接复制较长的子agent伪代码候选；其中底层状态和归档操作继续压缩。
- 不把词汇清理变成机械替换。具有实际实验含义的 comparison、independent evidence handoff及正式模块名继续使用。
- 不把正文每个表头延长为完整说明句。统计范围放在紧邻的正文或caption，维持横向信息密度。
- 不把缺测写成零，不用中间最好结果替代最终结果，不合并不同协议的分母或成本。
