"""Build a read-only evidence inventory; never launch or score experiments."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unique_rows(rows, expected):
    indexed = {row['task']: row for row in rows}
    assert len(indexed) == len(rows), 'Duplicate task records'
    assert set(indexed) == expected, 'Unexpected task collection'
    return indexed


def selected_group(groups, **keys):
    matches = [g for g in groups if all(g.get(k) == v for k, v in keys.items())]
    assert len(matches) == 1, keys
    return matches[0]


def retained(row):
    assert row['status'] == 'completed'
    assert isinstance(row['accepted'], bool)
    return {
        'action': 'reuse_in_original_repair_protocol',
        'accepted': row['accepted'],
        'result_path': row['path'],
        'end_to_end_reuse': 'not_established_different_input_and_generation_protocol',
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--public-audit', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    paired_root = root / 'output/paired12-matchfix-20260918-v1'
    files = {
        'public_inputs': args.public_audit.resolve(),
        'original_comparison': root / 'output/autonomous-verifier-20260917/autonomous_recovery_comparison_final.json',
        'selected_method': root / 'output/maintext-ablations-20260918/recovery_final.json',
        'paired_repair': paired_root / 'paper_results.json',
    }
    data = {k: json.loads(p.read_text(encoding='utf-8')) for k, p in files.items()}
    expected = {f'task_{n:03d}' for n in range(1, 51)}
    public = unique_rows(data['public_inputs']['tasks'], expected)
    ours_group = selected_group(data['selected_method']['groups'],
                                study='fixed50_v3', variant='without_edit_format_feedback')
    assert ours_group['complete']
    ours = unique_rows(ours_group['rows'], expected)
    baselines = {}
    for name in ('swe_native_isolated', 'direct_shared_tools'):
        group = selected_group(data['original_comparison']['groups'],
                               benchmark='Fixed50', version='formal_v3', method=name)
        assert group['complete']
        baselines[name] = unique_rows(group['conditions'], expected)

    pair = data['paired_repair']
    assert pair['complete'] and pair['all_initial_inputs_equal']
    paired_tasks = {r['task'] for r in pair['rows']}
    assert len(paired_tasks) == 12 and paired_tasks <= expected
    paired = {}
    for name in ('autonomous_layered', 'matchfix_full_orchestration'):
        paired[name] = unique_rows([r for r in pair['rows'] if r['method'] == name], paired_tasks)

    records = []
    for task in sorted(expected):
        source = {'status': 'needs_authoring', 'sha256': None, 'path': None}
        prior_pairs = {}
        if task in paired_tasks:
            source_path = paired_root / 'private_inputs' / task / 'source.py'
            source_hash = digest(source_path)
            for name, entries in paired.items():
                row = entries[task]
                assert source_hash == row['source_sha256']
                assert row['initial_candidate_sha256'] == public[task]['candidate_sha256']
                result_path = paired_root / 'conditions' / task / name / 'result.json'
                assert digest(result_path) == row['result_sha256']
                prior_pairs[name] = {
                    'action': 'reuse_in_original_paired_repair_protocol',
                    'accepted': row['accepted'],
                    'result_path': str(result_path.relative_to(root)),
                    'result_sha256': row['result_sha256'],
                }
            source = {'status': 'existing_authored_native_source', 'sha256': source_hash,
                      'path': str(source_path.relative_to(root))}
        records.append({
            'task': task,
            'candidate_sha256': public[task]['candidate_sha256'],
            'public_input_form': public[task]['classification'],
            'source': source,
            'original_repair': {
                'LaDiM': retained(ours[task]),
                'SWE-agent': retained(baselines['swe_native_isolated'][task]),
                'Direct': retained(baselines['direct_shared_tools'][task]),
            },
            'paired_repair': prior_pairs,
            'proposed_end_to_end': {
                'action': 'await_source_contract_and_protocol_freeze',
                'compatible_existing_runs_verified': 0,
                'automatic_dispatch': False,
            },
        })

    report = {
        'purpose': 'Discussion inventory, not an experiment manifest or launch authorization',
        'model_calls': 0,
        'candidate_executions': 0,
        'task_count': len(records),
        'source_status_counts': dict(Counter(r['source']['status'] for r in records)),
        'public_input_form_counts': dict(Counter(r['public_input_form'] for r in records)),
        'retained_original_repair_runs': 150,
        'retained_paired_repair_runs': len(pair['rows']),
        'retained_original_acceptance': {
            name: sum(r['original_repair'][name]['accepted'] for r in records)
            for name in ('LaDiM', 'SWE-agent', 'Direct')
        },
        'retained_paired_acceptance': {
            name: sum(r['accepted'] for r in entries.values())
            for name, entries in paired.items()
        },
        'evidence_files': {k: {'path': str(p), 'sha256': digest(p)} for k, p in files.items()},
        'records': records,
    }
    assert report['retained_paired_repair_runs'] == 24
    out = root / 'data/audits/unified-experiment-plan-20260918'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'fixed50_inventory.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    lines = [
        '# 50 个任务的现有结果与复用清单', '',
        '本清单只读取已完成结果并检查已有源程序、候选及配对结果的哈希。'
        '没有调用模型、执行候选或改变评分。', '',
        '任务编号只用于证据追踪。原修复与有源程序的配对修复是两个已完成协议，'
        '分别保留；这里没有将它们拼成一个排名。', '',
        '“复用/通过”和“复用/未通过”均表示保留该次有效运行，不再次调用模型。'
        '“缺少”只表示该协议没有已归档结果，不代表已经安排补跑。', '',
        '| 任务 | PyTorch 源程序 | 原修复：LaDiM | 原修复：SWE-agent | 原修复：Direct | 配对修复：LaDiM | 配对修复：MatchFixAgent |',
        '| --- | --- | --- | --- | --- | --- | --- |',
    ]

    def cell(row):
        if row is None:
            return '缺少'
        return '复用/通过' if row['accepted'] else '复用/未通过'

    for row in records:
        old, paired_rows = row['original_repair'], row['paired_repair']
        cells = [row['task'], '已有，保留' if row['source']['path'] else '待编写',
                 *(cell(old[k]) for k in ('LaDiM', 'SWE-agent', 'Direct')),
                 cell(paired_rows.get('autonomous_layered')),
                 cell(paired_rows.get('matchfix_full_orchestration'))]
        lines.append('| ' + ' | '.join(cells) + ' |')
    lines += [
        '', '合计：已有源程序 12 份，待编写 38 份；原修复有效运行 150 条，'
        '配对修复有效运行 24 条，全部保留。', '',
        '拟议端到端协议尚待冻结，当前没有核实可直接填入新主表的同协议运行。'
        '50 个任务的 LaDiM、SWE-agent、MatchFixAgent、Direct、MSAdapter、'
        'CodeTransEngine 条件均先标为“待协议与产物核对”，不能据此自动启动 300 次实验。'
        'InterTrans 是否参加此迁移方向另做适用性核对。', '',
        '详细路径和输入 SHA-256 见 '
        '[机器可读清单](../data/audits/unified-experiment-plan-20260918/fixed50_inventory.json)。'
        '总体安排见 [统一方案](unified-experiment-plan-20260918.md)。', '',
    ]
    (root / 'docs/unified-fixed50-reuse-20260918.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('records', 'evidence_files')},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
