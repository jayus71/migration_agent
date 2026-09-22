# 全文内容与组件证据修改记录

本轮在 `codex/iclr-2027-template` 落实 [已确认方案](paper-clarity-and-ablation-plan-20260922.md)。起点为 `d29e94e`，首轮内容提交为 `04ea2cf`。所有实验数字来自已完成的冻结记录；本轮只进行成文、表格生成、图形标签调整、离线数据核对和 LaTeX 排版，没有重新执行或扩大实验。

## 主要修改

摘要、引言贡献和结论围绕训练行为引导迁移与修复展开，明确保留 MindSpore 50/50、相对 MatchFixAgent 节省 57.4% token，以及保存初译中修复 4/5、三项对照各 0/5 的结论。保留摘要的跨框架结论、`Generalization Across Frameworks` 标题和 `state-of-the-art`。全文连同图注、表注按仓库 humanizer 和写作 DNA 复核，清理控制流复述和重复限定，未将实测优势改写为推测。

方法章先定义独立证据交接与修复历史，再解释仓库上下文管理及其组成。Repository Structural Analysis 和 Repair Dependency Graph Planning 使用统一正式名称。修复历史保留此前修改、观测、假设与验证反馈；允许任务授权范围内的支持库编辑。算法保留显式 LLM 参数和共享 AgentStep，算法 3 的上下文初始化去掉隐含自动扫描的 Map。消融沿用方法中已定义的名称，不机械回指方法小节编号。

主文消融表改为三个面板。保存初译面板完整保留 4/5、3/5、0/5 的修复数量、全部 5/5 的通过保留，以及 15,547,813、14,516,463、10,851,537 修复 token。时间序列面板保留两组独立参照：整体上下文的 6,047,074→1,936,579 token 和结构分析的 2,651,248→2,126,900 token，组内分别减少 68.0% 和 19.8%。全部累计结果、推荐上的相反成本趋势，以及规划消融和最终回退轨迹进入附录。

主文 JAX 保留原六例。LaDiM 和 Direct repair 均为 6/6，分别为 76/674,009 与 57/353,311 次调用/token。Ivy 与 samuela/torch2jax 原生转换单独分组，各 0/6、无 LLM 用量，健康控制通过。TorchAX 定义为修复执行后端。附录解释各类输入故障及转换时间。十二来源、两个修复任务的新 JAX 比较独立放入附录，四方法均为 1/2 修复接受、9/12 来源接受，并保留全部初译失败及成本。

图 3 左侧保留 LaDiM、MatchFixAgent 和 SWE-agent 三项总量，右侧比较 LaDiM 与 MatchFixAgent 的全部 29 个去重输入，分组文字统一为 Passes initial checks 和 Needs repair。图 4 使用 LaDiM detects at step 1 与 Loss check detects at step 31/18，图注明确后两者来自平均损失曲线。图形数值与检测阈值未改变。表格、图形脚本与导出资产同步更新。

## 来源

- 主比较、程序修复与信号：`data/paper_figures/unified_results.json`、`output/maintext-results-20260918/` 和 `output/maintext-ablations-20260918/recovery_final.json`。
- 仓库累计：`output/cumulative-component-ablation-20260922/summary.json`。
- 独立结构分析与规划：`data/audits/repository-map-ablation-20260922/summary.json` 和 `data/audits/work-unit-planning-ablation-20260922/summary.json`。
- 原六例 JAX：`output/maintext-jax-autonomous-20260918/final_analysis/summary.json`；转换器原始记录及调用在完整归档的 `formal_v5/converter_results.json`、`private_backend/track_c_external.py`。
- 新 JAX：`output/jax-expansion-20260922/formal/formal_report.json` 与独立审计。
- 实现核对：`scripts/repository_agent_mode.py`、`scripts/run_maintext_ablations.py` 和冻结自主代理实现。
- Ivy、torch2jax 与 TorchAX 定义已核对官方仓库/文档，并补齐引用。

生成器直接读取这些来源；仓库组件和新 JAX 表的注释记录输入路径与 SHA-256，统一结果 JSON 也记录六例 JAX 摘要的来源哈希。

## 验证与产物

必要检查包括现有 15 项图形数据/布局检查、10 项统一结果检查，全部通过。生成器的完整状态、检查分母、调用、修复/端到端成本恒等式和独立消融共用参照断言通过。数值验收仍采用历史结果，本轮没有声称重跑实验。

内容修改之后，按用户新增要求参照 LoCA 与 AutoIF 的横向信息组织重排表格。主比较的两个程序面板并排，两个仓库采用共享方法行；完整输入/输出费用移入附录，两个仓库的全部梯度与参数更新检查同步保留。主文消融前两面板并排，仓库组件改为逐行 Without/With 配对；JAX 以方法为列，附录仓库消融以任务为列组。正文分析与各项结果保留，表格使用 9 点文字。

`latexmk -pdf -interaction=nonstopmode -halt-on-error conference_101719.tex` 编译成功。横向重排后成稿共 23 页，正文到第 10 页，参考文献从第 11 页开始，附录从第 14 页开始。进一步压缩到投稿页数留待后续；本轮未改变模板字号、行距和页边距。PDF 已渲染检查，主文和附录表格、公式、算法及图 3/4 均无裁切、遮挡或溢出。编译没有未定义引用或 overfull 警告；局部 underfull 间距提示保留在编译日志中。

固定基线 `data/manuscript_baselines/pre-6pro-20260921/` 保持不变。逐词对比由 `scripts/update_manuscript_diff.py` 刷新到 `output/manuscript-comparison/index.html`，其成稿 PDF 与主编译产物一致。

用户方法图的 PDF、PNG、PowerPoint、SVG 和未跟踪的图形脚本保持不变，未进入任务提交。既有比较页在修改前已备份到本地 `tmp/manuscript-revision-parent-20260922-191313/`；其他用户未提交文件继续保留。未 push、创建 PR 或合并分支。
