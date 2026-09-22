"""Build compact reported results from the immutable formal evidence archive."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import tarfile


LABELS = {'autonomous_layered': 'LaDiM', 'direct_shared_tools': 'Direct LLM',
          'matchfix_full_orchestration': 'MatchFixAgent', 'swe_native_isolated': 'SWE-agent'}


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('archive', type=Path)
    parser.add_argument('independent_audit', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    audit = json.loads(args.independent_audit.read_text())
    with tarfile.open(args.archive) as tar:
        def read(path):
            return json.load(tar.extractfile('natural12_v2/' + path))
        summary = read('formal_summary.json')
        final = read('final_audit_summary.json')
        conditions = []
        for condition in summary['conditions']:
            key = f"conditions/{condition['task']}/{condition['method']}/result.json"
            result = read(key)
            attempts = []
            for attempt in result['attempts']:
                observation = attempt['evaluation'].get('observation', {})
                attempts.append({'submission': attempt['attempt'], 'accepted': attempt['accepted'],
                                 'stage_status': attempt['stage']['status'],
                                 'execution': observation.get('execution'),
                                 'acceptance': observation.get('acceptance'),
                                 'changed_files': attempt['changed_files']})
            audited = next(r for r in final['conditions'] if
                           r['task'] == condition['task'] and r['method'] == condition['method'])
            independent = next(r for r in audit['conditions'] if
                               r['task'] == condition['task'] and r['method'] == condition['method'])
            seeds = []
            for check in audited['checks']:
                observation = check['observation']
                failed_groups = Counter()
                for item in observation.get('measurements', []):
                    parts = item['quantity'].split(':')
                    failed_groups[':'.join(parts[:2])] += 1
                seeds.append({'seed': check['seed'], 'accepted': check['accepted'],
                              'execution': observation['execution'],
                              'acceptance': observation['acceptance'],
                              'failed_array_groups_zero_based_steps': dict(failed_groups)})
            conditions.append({**condition, 'submissions': attempts, 'final_seeds': seeds,
                               'wall_time_sec': result['wall_time_sec'],
                               'budget_elapsed_seconds': result['budget']['usage']['elapsed_seconds'],
                               'failure_detail': result.get('infrastructure_error'),
                               'final_stage': result['attempts'][-1]['stage']['status'],
                               'usage_by_stage': independent['usage']['usage_by_stage'],
                               'actual_models': result['budget']['usage']['actual_models']})
    method_totals = []
    for method, values in summary['method_totals'].items():
        rows = [r for r in conditions if r['method'] == method]
        method_totals.append({'method': method, 'label': LABELS[method], **values,
                             'repair_calls': sum(r['repair_calls'] for r in rows),
                             'repair_input_tokens': sum(r['repair_usage']['prompt_tokens'] for r in rows),
                             'repair_output_tokens': sum(r['repair_usage']['completion_tokens'] for r in rows),
                             'acceptance_at_submission_budget': {str(n): sum(
                                 next((s['accepted'] for s in reversed(r['submissions']) if s['submission'] <= n), False)
                                 for r in rows) for n in (1, 2, 4)}})
    flag_names = ('frozen_files_match', 'all_source_replays_pass', 'all_acceptances_match',
                  'all_per_array_verdicts_match', 'all_immutable_files_match',
                  'all_usage_matches', 'translation_ledger_matches')
    payload = {'source_pool_tasks': 12, 'generated_candidates': 10,
               'initial_passes': len(summary['selection']['initial_passes']),
               'generation_failures': summary['selection']['generation_failures'],
               'repair_tasks': summary['selection']['repair_tasks'],
               'source_pool_translation_usage': summary['source_pool_translation_usage'],
               'methods': method_totals, 'conditions': conditions,
               'original_final_audit_flags': {k: final[k] for k in
                    ('all_acceptances_reproduced', 'all_immutable', 'all_repair_usage_reconciled', 'backend_flags')},
               'independent_audit_flags': {k: audit[k] for k in flag_names},
               'source_replays': audit['source_replays'],
               'archive_sha256': digest(args.archive),
               'independent_audit_sha256': digest(args.independent_audit)}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'formal_report.json').write_text(json.dumps(payload, indent=2) + '\n')
    lines = ['# JAX 自然迁移正式比较', '',
             '12 个冻结来源各初译一次：10 个返回非空候选，8 个初始通过，2 个进入四方法修复；另外2个空正文生成失败保留在来源流量和费用中。修复接受率的分母为2。', '',
             '| 方法 | 修复接受 | 修复调用 | 输入 tokens | 输出 tokens | 修复总 tokens | 两任务端到端 tokens | 全12来源端到端 tokens |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for row in method_totals:
        lines.append(f"| {row['label']} | {row['repair_accepted']}/2 | {row['repair_calls']} | "
                     f"{row['repair_input_tokens']:,} | {row['repair_output_tokens']:,} | "
                     f"{row['repair_total_tokens']:,} | {row['selected_task_end_to_end_tokens']:,} | "
                     f"{row['shared_translation_then_repair_total_tokens']:,} |")
    lines += ['', '两任务端到端费用将对应的共同初译各计一次；全12来源费用包括8项初始通过与2项空生成的初译。四方法共享同一实际初译批次，跨方法合计实际消耗时只计这12次初译一次。', '',
              '| 任务 | 方法 | 最终接受 | 状态 | 提交数 | 修复 tokens |',
              '| --- | --- | --- | --- | ---: | ---: |']
    for row in conditions:
        lines.append(f"| {row['task']} | {LABELS[row['method']]} | {row['accepted']} | "
                     f"{row['status']} / {row['final_stage']} | {len(row['submissions'])} | "
                     f"{row['repair_usage']['total_tokens']:,} |")
    lines += ['', '三种子最终复验、冻结文件、逐调用原始 usage 及独立数组验收的核查结果见 formal_report.json 与 independent_audit.json。源轨迹复验从公共 source.py 和冻结输入重新执行，没有模型API调用。', '']
    (args.output / 'formal_report.md').write_text('\n'.join(lines))
    print(json.dumps({'methods': method_totals, 'audit_flags': payload['independent_audit_flags']}))


if __name__ == '__main__':
    main()
