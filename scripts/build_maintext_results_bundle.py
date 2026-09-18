"""Export audited results with the selected slim-v4 configuration explicit."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path


LABELS = {
    'autonomous_layered': '我们：独立证据交接',
    'autonomous_native_history': '我们：原始历史',
    'autonomous_category': '我们：自主分类',
    'swe_native_isolated': 'SWE-agent 1.1.0',
    'direct_shared_tools': 'Direct 共享工具控制',
    'matchfix_full_shared_backend': 'MatchFix 完整编排／共享后端',
}
COMPONENTS = {
    'continuous_role': '连续角色与原始会话',
    'without_repair_history': '去掉跨轮修复会话（修正版）',
    'without_progress_prompt': '去掉进展提示',
    'without_edit_format_feedback': '去掉编辑格式辅助',
}
SIGNALS = {
    'execution': '执行与基础契约',
    'execution_forward': '增加前向值',
    'execution_forward_gradient': '再增加梯度',
    'all_observations': '再增加参数更新',
}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(value, encoding='utf-8')
    temporary.replace(path)


def csv_text(rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def additional_results(root):
    paired_path = root / 'output/paired12-matchfix-20260918-v1/paper_results.json'
    e_path = root / 'output/e-baselines-current-20260918/four_methods/summary.json'
    n_path = root / 'output/intertrans-completion-20260918/paper_results.json'
    paired, end_to_end = read(paired_path), read(e_path)
    assert paired['complete'] and paired['conditions'] == 24 and paired['unknown_usage_calls'] == 0
    assert paired['all_initial_inputs_equal'] and paired['unique_responses'] == 674
    assert end_to_end['complete'] and end_to_end['conditions'] == 60
    lines = ['## 新增配对修复与端到端迁移', '',
        'Paired12 为机械生成公开原生工作负载的独立协议，不并入原 Fixed50。'
        '两方法接收相同完整 source、candidate 和目标库；MatchFix 的健康目标字段为空。', '',
        '| 方法 | 接受 | 第 1/2/4 次累计接受 | 调用 | 总 token | 每接受 token |',
        '| --- | ---: | --- | ---: | ---: | ---: |']
    paired_rows = []
    for method, row in paired['methods'].items():
        name = '精简 v4' if method == 'autonomous_layered' else 'MatchFix 完整编排/共享 DeepSeek 工具后端'
        checkpoint = '/'.join(str(row['accepted_at'][str(n)]) for n in (1, 2, 4))
        lines.append(f"| {name} | {row['accepted']}/{row['planned']} | {checkpoint} | {row['calls']} | {row['total_tokens']:,} | {row['tokens_per_accepted']:,.2f} |")
        paired_rows.append(dict(method=method, accepted=row['accepted'], planned=row['planned'],
            accepted_at_1=row['accepted_at']['1'], accepted_at_2=row['accepted_at']['2'],
            accepted_at_4=row['accepted_at']['4'], calls=row['calls'], total_tokens=row['total_tokens'],
            tokens_per_accepted=row['tokens_per_accepted']))
    lines += ['', '精简 v4 多接受一例，且每接受 token 更低；MatchFix 首次外部提交接受更多。'
        '接受数差异和成本差异分别报告，全部失败与用量保留。', '',
        '实验 E 使用五个源任务，每任务三条重复条件。三个模型方法各有 15 个历史候选，'
        'MSAdapter 为五个候选各测三个种子。此次只离线验收，新增模型调用为零。', '',
        '| 方法 | 严格接受 | 前向完成 | 训练完成 | 原生成 token | 用量来源 |',
        '| --- | ---: | ---: | ---: | ---: | --- |']
    for row in end_to_end['summaries']:
        lines.append(f"| {row['method']} | {row['strict_accepted']}/15 | {row['forward_completed']}/15 | {row['training_completed']}/15 | {row['historical_tokens']:,} | {row['usage_kind']} |")
    lines += ['', 'Frozen Translator 的 15/15 来自全部固定旧初译，修复调用为零。'
        '它测量冻结迁移配置的有效性；精简 v4 的修复收益由有初始故障的修复实验测量。'
        'MSAdapter 的失败来自原版 CPU 交叉熵；CTE 和 Direct 的数值失败主要由参数更新检查发现。'
        'CTE 的文本长度估算不与 provider usage 混合计算成本倍数。', '']
    sources = [paired_path, e_path]
    exports = [('paired12', paired_rows), ('end_to_end_e', end_to_end['summaries'])]
    pending = ['InterTrans']
    if n_path.exists():
        n = read(n_path)
        sources.append(n_path)
        lines += ['## N18 InterTrans', '']
        if n['all_valid']:
            assert n['completed'] == n['valid_outcomes'] == n['expected'] == 18
            pending = []
            usage = n['current_usage']
            lines += [f"18/18 条完整搜索结果已审计，接受 {n['accepted']}/18；"
                      f"当前运行 {usage['calls']} 次调用、{usage['total_tokens']:,} token。",
                '输入为完整 Java/DJL 源程序，保留上游 Java 到 Python 的直接路径与经 JavaScript 的路径。'
                '接受检查两个连续训练步骤，使用 101/202/303 三个种子。环境补库只复验保存输出。'
                '本组尚无精简 v4 的对应 N18 结果，InterTrans 结果单独归档。', '']
            exports.append(('intertrans_n18', [dict(task=r['task'], accepted=r['accepted'],
                attribution=r['attribution'], calls=r['usage']['calls'], tokens=r['usage']['total_tokens'])
                for r in n['rows']]))
        else:
            lines += [f"已完成 {n['completed']}/18，最终接受率待完整结果。", '']
    return lines, sources, exports, pending


def build(root, recovery_path):
    extra_lines, extra_sources, extra_exports, pending = additional_results(root)
    main_path = root / 'output/autonomous-verifier-20260917/autonomous_recovery_comparison_final.json'
    signal_path = root / 'output/maintext-ablations-20260918/training_signal16_final.json'
    call_path = root / 'output/maintext-ablations-20260918/training_signal16_call_count_audit.json'
    main, signal, calls, recovery = [read(p) for p in (main_path, signal_path, call_path, recovery_path)]
    assert sum(g['planned'] for g in main['groups']) == 610
    assert all(g['complete'] for g in main['groups'])
    assert signal['condition_count'] == 64 and not signal['violations']
    assert calls['conditions'] == 64 and not calls['violations'] and calls['unknown_usage_calls'] == 0
    assert all(g['complete'] and not g['ledger_mismatches'] and not g['request_treatment_violations']
               for g in signal['groups'].values())
    if recovery['complete']:
        assert recovery['selected_completed'] == recovery['selected_planned'] == 276
        assert recovery['ledger_mismatches'] == recovery['treatment_violations'] == 0

    main_rows = []
    for g in main['groups']:
        selected, total = g['selected_run_usage'], g['all_attempts_usage']
        main_rows.append(dict(benchmark=g['benchmark'], version=g['version'], method=g['method'],
            accepted=g['accepted'], planned=g['planned'],
            accepted_at_1=g['accepted_by_attempt_within_selected_run']['1'],
            accepted_at_2=g['accepted_by_attempt_within_selected_run']['2'],
            accepted_at_4=g['accepted_by_attempt_within_selected_run']['4'],
            actual_faults_repaired=g['repaired_initially_failed'], initially_failed=g['initially_failed'],
            healthy_retained=g['retained_healthy'], initially_healthy=g['initially_healthy'],
            selected_tokens=selected['total_tokens'], selected_calls=selected['calls'],
            all_attempts_known_tokens=total['known_total_tokens'],
            all_attempts_unknown_usage_calls=total['unknown_usage_calls']))
    component_rows = []
    for g in recovery['groups']:
        component_rows.append(dict(study=g['study'], variant=g['variant'], complete=g['complete'],
            completed=g['statuses'].get('completed', 0), planned=g['planned'],
            accepted=g['accepted'] if g['complete'] else None,
            actual_faults_repaired=g['actual_faults_repaired'] if g['complete'] else None,
            healthy_retained=g['healthy_retained'] if g['complete'] else None,
            selected_known_tokens=g['known_tokens'],
            all_attempts_unknown_usage_calls=g['all_attempts_usage'].get('unknown_usage_calls', 0)))
    slim_rows = []
    overlap = []
    for study, benchmark in [('fixed50_v3', 'Fixed50'), ('natural10_v3', 'Natural10')]:
        g = next(g for g in recovery['groups'] if g['study'] == study
                 and g['variant'] == 'without_edit_format_feedback')
        assert g['complete'] and all(r['status'] == 'completed' for r in g['rows'])
        slim_rows.append(dict(benchmark=benchmark, version='slim_v4', method='LaDiM',
            accepted=g['accepted'], planned=g['planned'],
            accepted_at_1=g['accepted_at']['1'], accepted_at_2=g['accepted_at']['2'],
            accepted_at_4=g['accepted_at']['4'],
            actual_faults_repaired=g['actual_faults_repaired'], healthy_retained=g['healthy_retained'],
            selected_tokens=g['known_tokens'], selected_calls=g['calls'],
            tokens_per_accepted=g['known_tokens'] / g['accepted'],
            selected_seconds=sum(r['wall_time_sec'] for r in g['rows']),
            failed_tasks=','.join(r['task'] for r in g['rows'] if not r['accepted'])))
        outcomes = {r['task']: r['accepted'] for r in g['rows']}
        for method in ['swe_native_isolated', 'direct_shared_tools']:
            baseline = next(x for x in main['groups'] if x['benchmark'] == benchmark
                            and x['version'] == 'formal_v3' and x['method'] == method)
            paired = {r['task']: r['accepted'] for r in baseline['conditions']}
            assert outcomes.keys() == paired.keys()
            overlap.append(dict(benchmark=benchmark, baseline=method,
                both=sum(outcomes[k] and paired[k] for k in outcomes),
                slim_only=sum(outcomes[k] and not paired[k] for k in outcomes),
                baseline_only=sum(not outcomes[k] and paired[k] for k in outcomes),
                neither=sum(not outcomes[k] and not paired[k] for k in outcomes)))
    signal_rows = []
    for variant, g in signal['groups'].items():
        signal_rows.append(dict(variant=variant, accepted=g['accepted'], planned=g['planned'],
            controller_accepted=g['controller_accepted'],
            initially_accepted_by_visible_checks=g['initially_accepted_by_available_checks'],
            calls=g['calls'], tokens=g['total_tokens'], unknown_usage_calls=g['usage'].get('unknown_usage_calls', 0)))

    slim_lines = ['## 主方法 slim v4', '',
        '| 数据集 | 第 1／2／4 次累计接受 | 总 token | 每接受 token | 未接受任务 |',
        '| --- | --- | ---: | ---: | --- |']
    for row in slim_rows:
        slim_lines.append(f"| {row['benchmark']} | {row['accepted_at_1']}／{row['accepted_at_2']}／{row['accepted_at_4']} | {row['selected_tokens']:,} | {row['tokens_per_accepted']:,.1f} | {row['failed_tasks']} |")
    slim_lines += ['', 'Natural10 的累计接受含五个初始健康程序；实际故障修复为 4/5。'
        'Fixed50 第二次提交增加 12 例接受，第三至第四次增加 4 例。'
        '新增 Paired12 与端到端迁移结果按各自协议单列。', '',
        '| 数据集 | 对照 | 共同接受 | 仅 slim 接受 | 仅对照接受 | 共同失败 |',
        '| --- | --- | ---: | ---: | ---: | ---: |']
    for row in overlap:
        slim_lines.append(f"| {row['benchmark']} | {row['baseline']} | {row['both']} | {row['slim_only']} | {row['baseline_only']} | {row['neither']} |")
    timestamp = datetime.now(timezone.utc).isoformat()
    lines = ['# 当前自主框架：实验结果汇总', '',
        f'生成时间：{timestamp}。本文件由已有结果与审计报告生成；不修改论文、图表或实验判定。', '',
        '用户于 2026-09-18 选择 slim v4（without_edit_format_feedback）作为主方法，Fixed50 为 45/50，Natural10 为 9/10，实际故障修复为 4/5。'
        '下文原始 v4 保留为组件参照；JAX 和训练信号实验使用原始 v4。'
        'JAX 六例与 Direct 持平，Direct 成本更低。新增训练信号消融支持同时检查前向值、梯度和参数更新。'
        + ('组件消融已全部完成。' if recovery['complete'] else '组件效果按完整组报告，尚未完成的组不计算接受率。'), '',
        '## 完成状态', '',
        '| 实验 | 状态 |', '| --- | --- |',
        '| 原自主框架与 baseline 比较 | 610/610 条完成，账本核对通过 |',
        f"| 四项组件消融与旧 fixture 信号实验 | {recovery['selected_completed']}/{recovery['selected_planned']} 条有效条件完成 |",
        '| 新增真实模型训练信号消融 | 64/64 条完成，690 次调用核对通过 |',
        '| JAX 自主修复比较 | 12/12 条 LLM 条件完成；原生转换器对照完成 |',
        '| 诊断与检测延迟重跑 | 108 条多步轨迹、5,400 行；单步 36 条记录完成 |', '',
        '这里一条条件是“任务 × 方法配置”的一次运行。恢复批次含 83 次基础设施中断补跑和 60 次修正版历史消融，'
        '合计 143 次；正常完成的成功和失败均保留。旧历史消融整组被独立的修正版替代，旧记录与成本仍在归档中。', '',
        '## 50 例受控故障与自然迁移的区别', '',
        '| 项目 | Fixed50 | Natural10 |', '| --- | --- | --- |',
        '| 来源 | 50 个预设注入故障 | 10 份已有首轮迁移代码中的自然问题 |',
        '| 初始状态 | 50 个故障 | 5 个故障、5 个健康程序 |',
        '| 验收 | 每例原有故障探针，最多四次外部提交 | 相同初态和输入下的源／目标前向值、梯度、参数更新比较，三 seed 确认 |',
        '| 主指标 | 原单元检查接受数／50 | 总接受数／10，并列实际故障修复数／5、健康保留数／5 |', '',
        '两组均移除了评估方提供的故障类别、位置和修复答案。自然迁移公开合法的 PyTorch 源程序，健康目标实现保持私有。'
        'MindSpore 路径执行实际目标前向和求导，torch4ms 随后调用 PyTorch 优化器完成参数更新；当前结果按这一执行范围解释。', '',
        '## 原始 v4 参照配置与 baseline', '',
        '| 方法 | 受控故障通过／50 | 第 1／2／4 次累计通过 | 自然迁移总通过／10 | 原有故障修好／5 |',
        '| --- | ---: | --- | ---: | ---: |']
    selected_methods = [('progress_v4', 'autonomous_layered'), ('formal_v3', 'swe_native_isolated'),
                        ('formal_v3', 'direct_shared_tools')]
    for version, method in selected_methods:
        f = next(g for g in main_rows if g['benchmark'] == 'Fixed50' and g['version'] == version and g['method'] == method)
        n = next(g for g in main_rows if g['benchmark'] == 'Natural10' and g['version'] == version and g['method'] == method)
        name = '我们 v4：独立证据交接' if method == 'autonomous_layered' else LABELS.get(method, method)
        lines.append(f"| {name} | {f['accepted']}/50 | {f['accepted_at_1']}／{f['accepted_at_2']}／{f['accepted_at_4']} | {n['accepted']}/10 | {n['actual_faults_repaired']}/5 |")
    match = next(g for g in main_rows if g['benchmark'] == 'Natural10' and 'matchfix' in g['method'])
    lines += [f"| MatchFix 完整编排／共享后端 | n/a | n/a | {match['accepted']}/10 | {match['actual_faults_repaired']}/5 |", '',
        '以上方法均保留全部 5 个健康程序。MatchFix 需要真实源／目标程序对，Fixed50 不满足其输入定义，标为 n/a。'
        'SWE-agent 保留上游 1.1.0 的算法与原生工具行为；MatchFix 保留完整上游编排并使用已记录的 DeepSeek 编码后端适配。'
        'Direct 是当前共享工具直接修复控制，与旧论文中的单调用 Direct 不同。', '',
        'v4 的 Fixed50 接受率为 82%，比 SWE-agent 和 Direct 分别高 24、12 个百分点；首轮接受率为 60%。'
        '自然迁移 9/10 中包括 4 个实际修复和 5 个健康保留。', '',
        '完整选定运行的 Fixed50 总 token：v4 为 38,028,388，SWE-agent 为 42,579,064，Direct 为 12,459,013。'
        '按每次接受修复计，v4 成本分别是 SWE-agent 的 0.632 倍、Direct 的 2.606 倍。'
        '这些比值计入选定运行中的全部调用；被中断的旧运行另计，其中有未知 usage，因此包含全部重启成本的比值为 n/a。', '',
        '## 所有开发配置', '',
        '| 版本 | 方法实现标识 | Fixed50 | Natural10 | 自然故障修复 |', '| --- | --- | ---: | ---: | ---: |']
    for f in main_rows:
        if f['benchmark'] != 'Fixed50' or f['method'] in ('swe_native_isolated', 'direct_shared_tools'):
            continue
        n = next(g for g in main_rows if g['benchmark'] == 'Natural10' and g['version'] == f['version'] and g['method'] == f['method'])
        lines.append(f"| {f['version']} | {f['method']} | {f['accepted']}/50 | {n['accepted']}/10 | {n['actual_faults_repaired']}/5 |")
    lines += ['',
        'v4 独立证据交接是新增组件消融预先冻结的参照。v3 自主分类比同版不强制分类多修好 4 例，未损失已有成功例，'
        '因此当前数据支持继续分析自主分类的作用。v6 有末次调用提示冲突，v7 修正该句；两版均作为开发结果保留。'
        '各版在同一任务池上开发与比较，不拼接逐例最优结果。', '',
        '## 组件消融', '',
        '| 组件设置 | 受控故障完成／计划 | 受控故障通过／50 | 自然迁移总通过／10 | 原有故障修好／5 | 十例完整运行总 token |',
        '| --- | ---: | ---: | ---: | ---: | ---: |',
        '| v4 参照配置 | 50/50 | 41/50 | 9/10 | 4/5 | 15,547,813 |']
    for variant, label in COMPONENTS.items():
        f = next(g for g in component_rows if g['study'] == 'fixed50_v3' and g['variant'] == variant)
        n = next(g for g in component_rows if g['study'] == 'natural10_v3' and g['variant'] == variant)
        fs = f"{f['accepted']}/50" if f['complete'] else '待完成'
        ns = f"{n['accepted']}/10" if n['complete'] else '待完成'
        faults = f"{n['actual_faults_repaired']}/5" if n['complete'] else '待完成'
        tokens = f"{n['selected_known_tokens']:,}" if n['complete'] else '待完成'
        lines.append(f"| {label} | {f['completed']}/50 | {fs} | {ns} | {faults} | {tokens} |")
    lines += ['',
        '“自然迁移总通过”由修好的故障和保持正确的健康程序组成；“原有故障修好”只统计初始失败的五例。'
        '十份输入直接复用 Experiment I 的首次翻译，此轮未重新翻译或注入故障。'
        '“十例完整运行总 token”包括全部十例的输入、输出、诊断、工具对话和失败修复尝试；'
        '不是仅成功案例的成本，也不是人民币费用。接口中断旧 episode 的额外成本单列在 CSV 的 all_attempts 字段中。', '',
        '自然迁移四组均保留 5/5 健康程序。去掉跨轮修复会话后，实际修复由 4/5 降为 0/5；'
        '去掉进展提示降为 2/5。去掉编辑格式辅助仍为 4/5，且选定运行 token 更少。'
        + ('在 Fixed50 上，连续角色、去掉修复历史、去掉进展提示、去掉格式辅助分别为 44、37、46、45 例。'
           '修复历史在两组都有正向结果；角色交接与进展提示表现随任务组变化，格式辅助未显示接受数收益。'
           '各条件只运行一组模型轨迹，这些差异描述本次完整结果，不是重复运行后的稳定因果效应。'
           if recovery['complete'] else '') +
        '“连续角色”同时改变独立角色交接和推理历史的保留；“编辑格式辅助”包括事前格式示例与事后纠错反馈。'
        '历史消融保留初诊交接、最新观测和当前文件，只清除先前修复会话；总预算保持累计。', '',
        '## 真实模型训练信号消融', '',
        'CNN、图像 MLP、Transformer 分类器和小型因果语言模型，各含执行、前向值、梯度、更新四种程序故障。'
        '四种可见反馈设置各运行 16 例，最终均用完整检查在三个 seed 上评分。', '',
        '| 默认可见反馈 | 完整验收接受 | 可见检查通过 | 初始未触发修复 | API 调用 | 总 token |',
        '| --- | ---: | ---: | ---: | ---: | ---: |']
    for g in signal_rows:
        lines.append(f"| {SIGNALS[g['variant']]} | {g['accepted']}/16 | {g['controller_accepted']}/16 | {g['initially_accepted_by_visible_checks']} | {g['calls']} | {g['tokens']:,} |")
    lines += ['',
        '该实验测量默认验证信号如何触发、指导和停止修复。增加数值信号后，初始漏检逐级减少，'
        '完整反馈组修好全部 16 个故障。四组都可主动编写 scratch tests；结果不作为“强制进入同一修复任务后，提示内容单独带来多少增益”的测量。'
        '独立审查覆盖 40 个接受补丁、120 次最终后端检查和全部 690 次请求；未知 usage 为 0。', '',
        '旧 fixture 信号实验另行完成：执行反馈 8/12，执行加前向 12/12，全部观测 12/12。'
        '它实际为三个 fixture 各重复四次，梯度 fixture 在初始执行阶段就抛异常，不能作为四模型梯度／更新作用的依据。'
        '新旧实验分别保存，不合并分母。', '',
        '## JAX 与诊断实验', '',
        '| JAX 方法 | 接受／首轮接受 | 调用 | 总 token | 每接受秒数 |',
        '| --- | ---: | ---: | ---: | ---: |',
        '| 我们 v4 | 6/6 | 76 | 674,009 | 302.7 |',
        '| Direct 共享工具控制 | 6/6 | 57 | 353,311 | 137.2 |',
        '| Ivy 原生转换 | 0/6 | 0 | 0 | n/a |',
        '| torch2jax 原生转换 | 0/6 | 0 | 0 | n/a |', '',
        'JAX 支持当前流程跨框架修复的可行性；六例中与 Direct 接受结果相同，Direct 成本更低。'
        '两种转换器接收已经有故障的候选，0/6 测量其是否消除已有故障；健康输入 gate 均通过。'
        '该对照不能写成健康源程序迁移正确率为零。', '',
        '诊断轨迹重跑保留全部阈值判定和缺失位置。两类直接训练信号各 12/12 在第 1 步检出；'
        '均值损失曲线分别在第 31、18 步越界，对应个体运行在观察窗口内检出 3/12、4/12。'
        '共核对 5,400 行，最大数值变化约 1.50e-6。', '',
        '编辑前诊断的 500 条评分记录已处理，其中 332 条通过两阶段评分及证据校验。'
        '其余为格式、长度或截断问题；各方法覆盖率不同。当前为 DeepSeek 探索性判断，尚有语义复核问题，'
        '不能直接填作人工确认的定位准确率。', '',
        '## 写作时需要替换的旧结论', '',
        '| 旧说法 | 当前可用依据 |', '| --- | --- |',
        '| 50/50、首轮 84% | 当前主方法 slim v4 为 45/50，首轮 29/50；原始 v4 单独列出 |',
        '| token 成本约低 29 倍 | slim v4 每接受 token 为 888,508；SWE 为 1,468,244；Direct 为 355,972 |',
        '| 工具证据压缩带来收益 | 610 条、13,519 次调用中压缩触发为 0；实际变化是交接与历史表示 |',
        '| 预设分类与定向修复指导 | 当前 agent 从公开代码与观测自主调查；类别真值、位置答案和健康目标实现保持私有 |',
        '| 48/50 定位准确率 | 旧值是确定性阶段一致性；当前独立诊断评分须并列覆盖率和复核状态 |',
        '| JAX 对所有对照均有成本优势 | 当前与 Direct 均 6/6，Direct token 和时间更低 |',
        '| 旧 GQA 案例中 baseline 均失败 | 当前 v4、SWE 首次提交通过，Direct 第二次通过；可改用经审查的自然迁移修复例 |', '',
        '## 数据与证据文件', '',
        '- [原 610 条完整报告](autonomous-repair-completed-20260918.md)',
        '- [组件消融恢复规则](maintext-ablation-recovery-20260918.md)',
        '- [训练信号独立审查](maintext-training-signal-independent-review-20260918.md)',
        '- [JAX 完整报告](maintext-jax-autonomous-rerun-20260918.md)',
        '- [诊断轨迹报告](maintext-diagnostic-rerun-20260918.md)',
        '- [MatchFix 配对十二例](paired12-matchfix-results-20260918.md)',
        '- [实验 E 四方法](e-baselines-current-20260918.md)',
        '- [InterTrans 完成记录](intertrans-completion-20260918.md)',
        '- [结果 CSV 与来源索引](../output/maintext-results-20260918/evidence_index.json)', '',
        '结果导出目录包含 main_comparison.csv、component_ablations.csv、training_signals.csv。'
        '每个源报告的路径与 SHA-256 均记录在 evidence_index.json；未完成组的接受结果留空。', '']
    sources = [main_path, signal_path, call_path, recovery_path,
        root / 'output/autonomous-verifier-20260917/fixed50-preflight/manifest.json',
        root / 'data/experiments/10_experiment_J_feedback_ablation/formal_run_2d6bd3d/r_stage/results/section65_fault_pool_repair_table.csv',
        root / 'docs/autonomous-repair-completed-20260918.md',
        root / 'docs/maintext-jax-autonomous-rerun-20260918.md',
        root / 'docs/maintext-diagnostic-rerun-20260918.md',
        root / 'docs/maintext-training-signal-independent-review-20260918.md'] + extra_sources
    metadata = dict(generated_at=timestamp, component_recovery_complete=recovery['complete'],
        main_method='slim_v4', main_variant='without_edit_format_feedback',
        auxiliary_method='original_v4', pending_baselines=pending,
        component_selected_completed=recovery['selected_completed'], component_selected_planned=recovery['selected_planned'],
        recovery_snapshot_time=recovery.get('created_at'),
        sources=[dict(path=str(p.relative_to(root)), sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sources])
    output = root / 'output/maintext-results-20260918'
    for name, rows in [('main_comparison', main_rows), ('slim_main', slim_rows),
                       ('slim_baseline_overlap', overlap),
                       ('component_ablations', component_rows), ('training_signals', signal_rows)] + extra_exports:
        write(output / (name + '.csv'), csv_text(rows))
    write(output / 'evidence_index.json', json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
    lines[5:5] = [''] + slim_lines + [''] + extra_lines
    write(root / 'docs/maintext-results-20260918.md', '\n'.join(lines))
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--recovery', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.root.resolve(), args.recovery.resolve()), ensure_ascii=False))


if __name__ == '__main__':
    main()
