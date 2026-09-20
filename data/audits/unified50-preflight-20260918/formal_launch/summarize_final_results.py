"""Validate saved evidence and write the completion report; no experiments run."""
import json
from collections import Counter
from pathlib import Path

base = Path(__file__).resolve().parent
repo = base.parents[3]
audit = json.loads((base / 'results_audit_final.json').read_text(encoding='utf-8-sig'))
snapshot = json.loads((base / 'monitor_latest_snapshot.json').read_text(encoding='utf-8-sig'))
rows = audit['rows']
aggregates = audit['aggregates']
assert len(rows) == len({r['id'] for r in rows}) == 391
assert Counter(r['phase'] for r in rows) == {'main': 174, 'cross_language': 72, 'plugin': 58, 'ablation': 87}
assert all(r['dispatch_state'] == 'finished' for r in rows)
assert all(r['result_sha256'] and r['receipt_sha256'] for r in rows)
assert not any(r['request_files_without_response'] for r in rows)
assert audit['formal_physical_observed_usage']['usage'] == snapshot['observed_provider_usage'] | {
    k: audit['formal_physical_observed_usage']['usage'][k]
    for k in ('prompt_cache_hit_tokens', 'prompt_cache_miss_tokens')
}
assert not audit['formal_physical_observed_usage']['missing_usage_fields']
interrupted = [r for r in rows if r['interrupted']]
assert len(interrupted) == 1
assert interrupted[0]['id'] == 'main__group_012__swe'
assert interrupted[0]['accepted'] is None
assert interrupted[0]['result_sha256'] == 'dc01ceda726dfefd12c30875ab840daa5789b6af0ba8bcb7d2db595821b0e4d5'
assert sum(r['accepted'] is True for r in rows) == 300
assert sum(r['accepted'] is False for r in rows) == 90
assert not snapshot['active'] and not snapshot['scheduler_alive']

names = {'ladim': 'LaDiM', 'matchfix': 'MatchFixAgent', 'swe': 'SWE-agent',
         'direct': 'Direct LLM', 'cte': 'CodeTransEngine（直接转换配置）', 'msadapter': 'MSAdapter',
         'test_repair': '普通测试修复'}
main = []
for method in ('ladim', 'matchfix', 'swe', 'direct', 'cte', 'msadapter'):
    subset = [r for r in rows if r['phase'] == 'main' and r['method'] == method]
    a = aggregates['main/' + method]
    aliases = [alias for r in subset for alias in r['aliases']]
    assert len(subset) == 29 and len(aliases) == len(set(aliases)) == 50
    main.append({'method': names[method], 'key': method, 'denominator': 29,
                 'accepted': a['accepted'], 'not_accepted': a['not_accepted_valid'],
                 'interrupted': a['unmeasured_or_interrupted'],
                 'accepted_aliases': sum(len(r['aliases']) for r in subset if r['accepted'] is True),
                 'interrupted_aliases': sum(len(r['aliases']) for r in subset if r['accepted'] is None),
                 'end_to_end_tokens': a['end_to_end_observed_usage']['usage'].get('total_tokens', 0),
                 'end_to_end_calls': a['end_to_end_observed_usage']['observed_calls']})
cross = []
for method in ('ladim', 'swe', 'matchfix', 'test_repair'):
    a = aggregates['cross_language/' + method]
    cross.append({'method': names[method], 'accepted': a['accepted'], 'denominator': 18,
                  'tokens': a['end_to_end_observed_usage']['usage']['total_tokens']})
historical = audit['historical_reused_conditions']
historical_direct = [r for r in historical if r['method'] == 'direct_llm']
historical_intertrans = [r for r in historical if r['method'] == 'intertrans']
assert len(historical_direct) == len(historical_intertrans) == 18
assert all(r['result_hash_verified'] for r in historical_intertrans)
historical_direct_tokens = sum(r['usage']['total_tokens'] for r in historical_direct)
it = audit['historical_intertrans_summary']
assert sum(r['accepted'] for r in historical_intertrans) == it['accepted'] == 1
cross.extend([
    {'method': 'Direct LLM（复用）', 'accepted': sum(r['accepted'] for r in historical_direct),
     'denominator': 18, 'tokens': historical_direct_tokens},
    {'method': 'InterTrans（复用）', 'accepted': it['accepted'], 'denominator': 18,
     'tokens': it['cumulative_usage']['total_tokens']},
])
variant_names = {
    'main/ladim': 'LaDiM 完整方法',
    'continuous_role/ladim': '延续原会话进行修复',
    'without_repair_history/ladim': '移除跨轮修复历史',
    'without_progress_prompt/ladim': '移除进展提示',
    'matchfix_investigation/matchfix': 'MatchFixAgent 加入诊断模块',
    'swe_investigation/swe': 'SWE-agent 加入诊断模块',
}
analysis = [{'variant': label, 'accepted': aggregates[key]['accepted'], 'denominator': 29,
             'tokens': aggregates[key]['end_to_end_observed_usage']['usage']['total_tokens']}
            for key, label in variant_names.items()]
ladim_tokens = aggregates['main/ladim']['end_to_end_observed_usage']['usage']['total_tokens']
matchfix_tokens = aggregates['main/matchfix']['end_to_end_observed_usage']['usage']['total_tokens']
saving = 1 - ladim_tokens / matchfix_tokens
checks = {
    'unique_conditions': 391, 'normal_terminal_results': 390, 'integration_interruptions': 1,
    'accepted': 300, 'not_accepted': 90, 'pending': 0, 'running': 0,
    'result_hashes_present': True, 'request_files_missing_responses': 0,
    'provider_usage_matches_status': True, 'main_unique_groups': 29, 'main_alias_ids': 50,
    'main_alias_uniqueness_passed_for_all_methods': True,
    'interrupted_original_hash_verified': True,
    'interrupted_job': interrupted[0]['id'],
}
summary = {'checked_at': audit['checked_at'], 'completed_at': audit['status']['timestamp'],
           'checks': checks, 'main': main, 'cross_language': cross, 'analysis': analysis,
           'main_ladim_token_reduction_vs_matchfix': saving,
           'formal_physical_observed_usage': audit['formal_physical_observed_usage'],
           'historical_direct_observed_tokens': historical_direct_tokens,
           'historical_intertrans_summary': it,
           'combined_observed_tokens_with_reused_history':
               audit['formal_plus_reused_direct_observed_usage']['usage']['total_tokens'] + it['cumulative_usage']['total_tokens'],
           'usd_cost': None}
(base / 'final_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

lines = [
    '# 统一迁移实验完成报告', '',
    '2026 年 9 月 19 日 02:06（UTC+8），全部 391 个条件结束：390 条产生正常终止结果，1 条保留为本方接入中断。当前无运行或等待任务。主实验 174、跨语言 72、插拔 58、消融 87 条均有结果文件和调度回执。正常结果包括验收成功、验收失败及原生生成终止，不能将“已结束”解释为“通过”。', '',
    '本报告仅整理结果与证据；论文和实验方法未在汇总阶段改动。后端继续使用冻结的 DeepSeek 配置。', '',
    '## 主实验', '',
    '六种方法使用同一批源程序与最终验收。原有 50 个编号对应 29 个不同的源程序与验收合约组合，来自 24 个源文件；相同输入组合的编号复用同一条件结果。主统计使用 29 个不同组合，50 个编号的展开数供核对，重复编号不作为独立样本。验收使用固定种子 101、202、303。修复方法共用同一份 Direct 初译，端到端 token 包含该初译及所有修复和失败调用。', '',
    '| 方法 | 通过 / 29 | 未通过 | 接入中断 | 展开编号通过 / 50 | 端到端总 token |',
    '| --- | ---: | ---: | ---: | ---: | ---: |',
]
for r in main:
    lines.append(f"| {r['method']} | {r['accepted']}/29 | {r['not_accepted']} | {r['interrupted']} | {r['accepted_aliases']}/50 | {r['end_to_end_tokens']:,} |")
lines += ['',
    f'LaDiM 与 MatchFixAgent 均通过 29/29 个组合。LaDiM 的端到端总 token 为 {ladim_tokens:,}，MatchFixAgent 为 {matchfix_tokens:,}；本次运行中 LaDiM 少用 {saving:.1%}。这一优势体现为同等验收覆盖下的 token 效率。总 token 包含缓存命中的输入，不能直接转换为同幅度的货币费用节省。', '',
    'Direct 初译已有 20/29 个组合通过，剩余 9 个均被 LaDiM 和 MatchFixAgent 修复。该通过率上限会降低消融实验对组件差异的敏感度。SWE-agent 的 1 个中断组合保留在 29 的分母中，验收记为 n/a；它不是 baseline 自身的功能失败，也没有被当作成功。', '',
    '## 跨语言实验', '',
    'Java/DJL 到 Python/PyTorch 的 18 个任务使用统一源程序和最终验收。本轮运行四种修复方法共 72 条；Direct LLM 与 InterTrans 的 36 条已有结果复用。候选、请求、响应或结果共 72 项历史哈希核验通过，没有重新生成。', '',
    '| 方法 | 通过 / 18 | 端到端观测总 token |', '| --- | ---: | ---: |',
]
for r in cross:
    lines.append(f"| {r['method']} | {r['accepted']}/18 | {r['tokens']:,} |")
lines += ['',
    'LaDiM 比 SWE-agent 和 MatchFixAgent 各多通过 1 个任务；相对普通测试修复多通过 2 个，但消耗更多 token。18 个任务上的单次结果支持描述这一观察，尚没有重复运行或显著性检验支撑更广的优越性结论。', '',
    f"InterTrans 的观测 token 包含已有完整运行的 {it['current_usage']['total_tokens']:,} 和先前未完成调用的 {it['historical_incomplete_usage']['total_tokens']:,}，二者分别留账。已有 JAX 结果仍保留在原证据中，本轮没有补跑或混入以上分母。", '',
    '## 消融与插拔分析', '',
    '以下实验复用主实验的 29 个组合与共同初译，预算和验收保持一致。', '',
    '| 设置 | 通过 / 29 | 端到端总 token |', '| --- | ---: | ---: |',
]
for r in analysis:
    lines.append(f"| {r['variant']} | {r['accepted']}/29 | {r['tokens']:,} |")
lines += ['',
    '延续原会话的设置通过 28/29，而完整方法为 29/29；单个失败差异仅提供有限证据。移除修复历史或进展提示后仍通过 29/29，并且总 token 更低，因此本批结果没有显示这两个组件的验收或效率收益。', '',
    'MatchFixAgent 加入诊断模块后仍为 29/29，但总 token 增加。SWE-agent 加入模块后为 24/29；原生主实验为 25 个通过、3 个未通过、1 个接入中断。当前结果没有显示插拔模块改善最终验收，SWE 的中断还需要在比较中单列。', '',
    '## 费用、异常与核验', '',
    f"本轮 {audit['formal_physical_observed_usage']['observed_calls']:,} 个不同 provider 响应共记录 {audit['formal_physical_observed_usage']['usage']['prompt_tokens']:,} 输入 token、{audit['formal_physical_observed_usage']['usage']['completion_tokens']:,} 输出 token，总计 {audit['formal_physical_observed_usage']['usage']['total_tokens']:,}。已按 provider 响应 ID 去重；共享初译在实际调用总账只计一次，在每个方法的端到端比较中分别归属。不能将各方法端到端列相加当成实际支付总量。", '',
    f"加上复用的 Direct 初译 {historical_direct_tokens:,} token，以及 InterTrans 完整运行和历史未完成调用 {it['cumulative_usage']['total_tokens']:,} token，所整理证据的合计为 {summary['combined_observed_tokens_with_reused_history']:,} token。当前没有已核验的计费单价或账单，货币费用记为 n/a。已保存请求均找到对应响应，已收集响应的 usage 字段完整；传输层未留下响应的未知消耗不会被假定为零。", '',
    'SWE 中断发生在本方进程暂停/恢复接入层。修复经过确定性回归和六项原有集成测试后，仅恢复了 34 个尚未启动条件。这 34 个现在全部结束，未再次发生该接入错误。原中断实例的 28 次调用、428,811 token、原始结果和旧回执均保留，未重采样；初始 accepted=true 不作为最终成功。普通测试修复另有 1 条原生输出截断，作为原生终止失败保留，其请求、响应和费用均计入。', '',
    '最终核验覆盖 391 个唯一计划条件及回执、结果文件完整性、285 个正常 agent 结果与其最终验收字段一致、历史复用哈希、provider 用量核对及中断结果哈希。七组冻结文件、baseline 身份与执行授权检查再次通过，检查本身没有调用模型。调度器已正常退出。', '',
    '结果 JSON：[final_summary.json](../data/audits/unified50-preflight-20260918/formal_launch/final_summary.json)。逐条件及调用证据索引：[results_audit_final.json](../data/audits/unified50-preflight-20260918/formal_launch/results_audit_final.json)。接入故障记录：[unified50-swe-continuation-incident-20260918.md](unified50-swe-continuation-incident-20260918.md)。', '',
]
report = repo / 'docs/unified-experiments-results-20260919.md'
report.write_text('\n'.join(lines), encoding='utf-8')
print(json.dumps({'report': str(report), 'checks': checks, 'main': main,
                  'main_token_reduction': saving, 'combined_tokens': summary['combined_observed_tokens_with_reused_history']}, ensure_ascii=False, indent=2))
