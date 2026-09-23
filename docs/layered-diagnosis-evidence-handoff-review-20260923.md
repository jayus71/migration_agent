# 分层诊断时机与证据交接相关工作核对

日期：2026-09-23。核对版本：a9130b5及当前工作树。用户要求解释诊断发生位置，并调研其他方法是否已有证据交接。本轮只交付调研，不修改论文、图形或实验。

## 分层诊断发生位置

训练step是观测的时间单位。前向值在前向执行后可用，梯度在求导后可用，参数更新差异在更新后可用；完整的一步训练证据要等这些计算完成。自动采集和比较这些值，与调用LLM进行故障调查，是两个执行层次。

论文sections/methods.tex的算法1接受已有candidate和measurements，Verifier依据execution → forward → gradient → update → next forward依赖关系选择代码检查与测试。它还使用最早出现差异的step辅助判断故障传播。算法3在初译和外部验证后调用LayeredDiagnosis，再交给Repair。

scripts/run_repository_agent_mode.py:41–55给出具体控制顺序：初始评估失败后调用一次agent.diagnose；随后循环agent.repair和ev.complete_repository，失败结果返回持续的修复会话。冻结实现output/maintext-ablations-20260918/frozen_v4_agent.py:558–570在交接发生后禁止再次以独立Verifier调用diagnose。每个训练step结束后都重新调用一次Verifier，不符合这一控制流程。

完整训练步中可按前向、求导、更新的位置采集观测；异常可能使后续观测不可得。主文附录声明程序和仓库分别检查连续两步与三步，源和目标从对应初始状态开始并各自保留状态。检测研究另有逐步同步条件，不应把同步条件推广到全部主比较。

## 原始文献核对

| 方法 | 已核实的信息传递 | 与本稿定位的关系 |
|---|---|---|
| MatchFixAgent | §2.1、2.3、2.4：六项语义分析报告交给Test Generator & Repair Agent，后者运行测试核实报告并修复；分析报告及测试/修复报告再交给Verdict Agent。 | 直接相关的代码迁移先例，已包含分析到修复的交接及接收方复核。 |
| FixAgent | §IV-A：localizer、repairer、revisitor顺序传递响应；后续prompt包括前序结果、失败用例与程序上下文。修复器可修改定位之外的代码并反馈调整定位。 | 定位与修复角色分离、传递结果及重新判断均有先例。 |
| MASAI | §2：Edit Localizer把定位信息交给Fixer；Fixer输入为问题描述与待修改代码。Issue Reproducer的测试和运行命令交给Ranker用于候选筛选。 | 模块间有明确输入输出，但不能写成Fixer直接接收全部复现测试或完整调查轨迹。 |
| Debug2Fix | §4.1–4.3：Debug Subagent有独立system prompt、context及tools，返回结论和变量值、调用栈、源码位置等支持证据；没有文件编辑工具，由主代理修改代码。 | 独立调查上下文、只读诊断与带支持观测的交接均与本稿接近。 |

来源（本轮在线读取论文全文方法部分）：

- MatchFixAgent：https://arxiv.org/html/2509.16187 ，官方实现：https://github.com/Intelligent-CAT-Lab/MatchFixAgent 。OpenReview访问遇到浏览器验证，方法核对使用作者arXiv全文。
- FixAgent：https://arxiv.org/html/2404.17153v1 。
- MASAI：https://arxiv.org/html/2406.11638v1 。
- Debug2Fix：https://arxiv.org/html/2602.18571 。

## 对本稿的判断与建议

“把诊断证据交给另一个修复代理”以及“独立上下文中的只读诊断”已有直接先例。当前检索支持将交接作为系统组件描述；不支持将这一通用操作单独主张为首次提出的机制。

本稿可具体解释：按训练计算依赖组织执行、前向、梯度与参数更新的差异；利用一致项、异常项和首次异常step提出可测试的故障假设；将代码观察、实测结果与假设作为有来源的记录交给Repair Agent，后续修复继续使用提交评估与历史。冻结_handoff_to_fixer创建新的修复system prompt，把Verifier公开调查记录包装为注明来源的输入证据；它不是单纯传一个最终诊断标签。

推荐把创新论证重点放在训练行为诊断及其与修复闭环的组合。交接的消融回答这一组件在当前任务中是否有用，不回答其是否首创。现有十程序组件表中完整方法为9/10（修复4/5），连续会话为8/10（修复3/5），该差异应按现有实验范围解释。

以上定位和措辞为本轮代理建议，尚未获得论文修改批准。没有重跑实验或改动比较协议。
