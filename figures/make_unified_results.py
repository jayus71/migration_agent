"""Export the complete frozen migration comparison with the 50 task-ID display.

Each source/contract group was executed once. Tokens count real calls, and task
counts expand the declared aliases. An interrupted final result stays missing.
"""
import hashlib
import csv
import json
from pathlib import Path
from matplotlib.patches import Patch
import numpy as np

from paper_plot_style import BLUE, GRAY, GREEN, ORANGE, plt

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'data/audits/unified50-preflight-20260918/formal_launch/results_audit_final.json'
SUMMARY = AUDIT.with_name('final_summary.json')
SIGNALS = ROOT / 'data/paper_figures/autonomous_training_signals.csv'
REPOSITORY_SUMMARY = ROOT / 'output/repository-migration-20260921/final/summary.json'
REPOSITORY_CHECKS = ROOT / 'output/repository-migration-20260921/partial_results.json'
REPOSITORY_AUDIT = ROOT / 'output/repository-migration-20260921/final/final_integrity_audit.json'
NATURAL_METHOD = ROOT / 'output/maintext-results-20260918/slim_main.csv'
NATURAL_BASELINES = ROOT / 'output/maintext-results-20260918/main_comparison.csv'
REPOSITORY_SIGNALS = ROOT / 'data/paper_figures/repository_training_check_details.json'
NATURAL_COMPONENTS = ROOT / 'output/maintext-ablations-20260918/recovery_final.json'
JAX_SUMMARY = ROOT / 'output/maintext-jax-autonomous-20260918/final_analysis/summary.json'
LABELS = {'ladim': 'LaDiM', 'matchfix': 'MatchFixAgent', 'swe': 'SWE-agent',
          'direct': 'Direct LLM', 'cte': 'CodeTransEngine', 'msadapter': 'MSAdapter',
          'test_repair': 'Test-guided repair'}
TABLE_LABELS = {**LABELS, 'ladim': r'\textbf{LaDiM (ours)}', 'intertrans': 'InterTrans'}

ORDER = ['direct', 'cte', 'msadapter', 'swe', 'matchfix', 'ladim']
COLORS = {'direct': GREEN, 'cte': '#a6761d', 'msadapter': '#9467bd',
          'swe': GRAY, 'matchfix': ORANGE, 'ladim': BLUE}


def load_data():
    audit = json.loads(AUDIT.read_text(encoding='utf-8-sig'))
    summary = json.loads(SUMMARY.read_text(encoding='utf-8-sig'))
    rows = audit['rows']
    assert len(rows) == len({r['id'] for r in rows}) == 391
    initial = {r['group']: r['accepted'] for r in rows if r['phase'] == 'main' and r['method'] == 'direct'}
    output = {'main': {}, 'variants': {}, 'cross_language': summary['cross_language'],
              'training_signals': [{k: v if k == 'variant' else int(v) for k, v in row.items()}
                                   for row in csv.DictReader(SIGNALS.read_text().splitlines())]}
    for row, method in zip(output['cross_language'], ['ladim', 'swe', 'matchfix', 'test_repair', 'direct', 'intertrans']):
        row['key'] = method
        if method == 'intertrans':
            usage = audit['historical_intertrans_summary']['cumulative_usage']
        elif method == 'direct':
            shared_keys = set().union(*(set(r['end_to_end_call_keys']) - set(r['incremental_call_keys'])
                for r in rows if r['phase'] == 'cross_language' and r['method'] == 'ladim'))
            assert len(shared_keys) == 18
            usage = {field: sum(audit['provider_calls'][k]['usage'][field] for k in shared_keys)
                     for field in ('prompt_tokens', 'completion_tokens', 'total_tokens')}
        else:
            usage = audit['aggregates']['cross_language/' + method]['end_to_end_observed_usage']['usage']
        row['input_tokens'], row['output_tokens'] = usage['prompt_tokens'], usage['completion_tokens']
        assert row['input_tokens'] + row['output_tokens'] == row['tokens']
        row['calls'] = (audit['aggregates']['cross_language/' + method]['end_to_end_observed_usage']['observed_calls']
                        if method not in ('direct', 'intertrans') else 18 if method == 'direct'
                        else audit['historical_intertrans_summary']['cumulative_usage']['calls'])
    reference_aliases = {a for r in rows if r['phase'] == 'main' and r['method'] == 'direct' for a in r['aliases']}
    for key, aggregate in audit['aggregates'].items():
        if key.startswith('cross_language/'):
            continue
        subset = [r for r in rows if r['variant'] + '/' + r['method'] == key]
        aliases = [alias for r in subset for alias in r['aliases']]
        assert len(aliases) == len(set(aliases)) == 50
        assert set(aliases) == reference_aliases
        assert len(subset) == len({r['group'] for r in subset}) == 29
        at_budget = {}
        for budget in (1, 2, 4):
            passed = 0
            for row in subset:
                checkpoints = [a for a in row['attempts'] if a['attempt'] <= budget]
                accepted = (None if row['interrupted'] else checkpoints[-1]['accepted']
                            if checkpoints else row['accepted'])
                passed += len(row['aliases']) if accepted is True else 0
            at_budget[str(budget)] = passed
        accepted = sum(len(r['aliases']) for r in subset if r['accepted'] is True)
        assert at_budget['4'] == accepted
        values = {'method': subset[0]['method'], 'accepted': accepted, 'denominator': 50,
                  'accepted_groups': aggregate['accepted'], 'groups': 29,
                  'missing': sum(len(r['aliases']) for r in subset if r['accepted'] is None),
                  'tokens': aggregate['end_to_end_observed_usage']['usage'].get('total_tokens', 0),
                  'input_tokens': aggregate['end_to_end_observed_usage']['usage'].get('prompt_tokens', 0),
                  'output_tokens': aggregate['end_to_end_observed_usage']['usage'].get('completion_tokens', 0),
                  'calls': aggregate['end_to_end_observed_usage']['observed_calls'],
                  'at_budget': at_budget,
                  'faults_repaired': sum(len(r['aliases']) for r in subset if not initial[r['group']] and r['accepted'] is True),
                  'healthy_retained': sum(len(r['aliases']) for r in subset if initial[r['group']] and r['accepted'] is True)}
        if subset[0]['method'] in ('direct', 'cte', 'msadapter'):
            values['faults_repaired'] = values['healthy_retained'] = None
        if key.startswith('main/'):
            output['main'][subset[0]['method']] = values
        else:
            output['variants'][key] = values
    paired_rows = {(r['group'], r['method']): r for r in rows if r['variant'] == 'main'}
    provider_calls = audit['provider_calls']
    paired_costs = []
    for group in sorted(initial):
        point = {'group': group, 'initially_accepted': initial[group]}
        for method in ('ladim', 'matchfix'):
            condition = paired_rows[group, method]
            assert condition['accepted'] is True
            point[method + '_tokens'] = sum(provider_calls[key]['usage']['total_tokens']
                                            for key in set(condition['end_to_end_call_keys']))
        paired_costs.append(point)
    for method in ('ladim', 'matchfix'):
        assert sum(p[method + '_tokens'] for p in paired_costs) == output['main'][method]['tokens']
    output['paired_costs'] = paired_costs
    output['cost_stages'] = {}
    for method in ('ladim', 'matchfix', 'swe'):
        conditions = [r for r in rows if r['variant'] == 'main' and r['method'] == method]
        stages = {'initially_accepted': 0, 'initially_faulty': 0}
        for row in conditions:
            state = 'initially_accepted' if initial[row['group']] else 'initially_faulty'
            stages[state] += sum(provider_calls[k]['usage']['total_tokens']
                                  for k in set(row['incremental_call_keys']))
            shared = set(paired_rows[row['group'], 'direct']['end_to_end_call_keys'])
            assert shared.issubset(row['end_to_end_call_keys'])
        stages['translation'] = output['main'][method]['tokens'] - sum(stages.values())
        assert stages['translation'] == output['main']['direct']['tokens']
        output['cost_stages'][method] = stages

    repository = json.loads(REPOSITORY_SUMMARY.read_text())
    checks = json.loads(REPOSITORY_CHECKS.read_text())
    integrity = json.loads(REPOSITORY_AUDIT.read_text())
    repository_signals = json.loads(REPOSITORY_SIGNALS.read_text())['timeseries']
    output['repository'] = []
    for row in repository['rows']:
        repository_name, method = row['repository'], row['method']
        checked = checks[repository_name][method]
        audit_row = integrity['conditions'][repository_name + '/' + method]
        assert not audit_row['source_mismatches'] and audit_row['task_matches']
        assert not audit_row['initial_target_mismatches']
        assert audit_row['response_count_matches'] and all(audit_row['usage_matches'].values())
        assert audit_row['end_to_end_cost_matches']
        assert row['accepted'] == checked['complete_acceptance'] == audit_row['accepted']
        assert row['end_to_end_tokens'] == checked['end_to_end_tokens']
        assert row['calls'] == checked['repair_calls']
        assert row['end_to_end_tokens'] == row['usage']['total_tokens'] + row['translation_usage']['total_tokens']
        paired = checked['all_seed_checks'] if repository_name == 'timeseries' else checked['protocol_checks']
        assert paired['passed'] + len(paired['failed']) + len(paired['not_measured']) == paired['expected']
        if repository_name == 'timeseries':
            counts = repository_signals[method]['counts']
            signals = {'loss': counts['forward_loss'], 'gradient': counts['gradients'],
                       'update': counts['parameter_updates'], 'entry_points': counts['entry_points']}
        else:
            signals = {k: {'passed': checked['training_signals'][k]['passed'], 'expected': 18}
                       for k in ('loss', 'gradient', 'update')}
            signals['entry_points'] = {'passed': checked['original_tests']['passed'], 'expected': 10}
        output['repository'].append({'repository': repository_name, 'method': method,
            'accepted': row['accepted'], 'tokens': row['end_to_end_tokens'],
            'repair_calls': row['calls'], 'submissions': row['submissions'],
            'repair_prompt_tokens': row['usage']['prompt_tokens'],
            'repair_completion_tokens': row['usage']['completion_tokens'],
            'translation_tokens': row['translation_usage']['total_tokens'],
            'paired_checks': paired, 'details': checked, 'main_table_signals': signals})
    natural_rows = list(csv.DictReader(NATURAL_BASELINES.read_text().splitlines()))
    natural_method = next(r for r in csv.DictReader(NATURAL_METHOD.read_text().splitlines())
                          if r['benchmark'] == 'Natural10' and r['version'] == 'slim_v4')
    output['natural_repairs'] = []
    for method, source_name in [('direct', 'direct_shared_tools'), ('swe', 'swe_native_isolated'),
                                ('matchfix', 'matchfix_full_orchestration'), ('ladim', None)]:
        row = natural_method if method == 'ladim' else next(r for r in natural_rows
            if r['benchmark'] == 'Natural10' and r['version'] == 'formal_v3' and r['method'] == source_name)
        output['natural_repairs'].append({'method': method, 'accepted': int(row['accepted']),
            'denominator': int(row['planned']), 'repaired': int(row['actual_faults_repaired']),
            'retained': int(row['healthy_retained']), 'faults': 5, 'initially_accepted': 5,
            'tokens': int(row['selected_tokens']), 'calls': int(row['selected_calls'])})
    groups = [g for g in json.loads(NATURAL_COMPONENTS.read_text())['groups']
              if g['study'] == 'natural10_v3']
    reference = groups[0]['reference_v4']
    output['natural_components'] = []
    for label, row in [('LaDiM', reference)] + [
            ({'continuous_role': 'Continuous conversation',
              'without_repair_history': 'Without repair history',
              'without_progress_prompt': 'Without progress reminders',
              'without_edit_format_feedback': 'Without editing format assistance'}[g['variant']], g)
            for g in groups]:
        assert row['complete'] and row['planned'] == row['recorded'] == 10
        assert row['actual_faults_repaired'] + row['healthy_retained'] == row['accepted']
        output['natural_components'].append({'label': label, 'accepted': row['accepted'],
            'repaired': row['actual_faults_repaired'], 'retained': row['healthy_retained'],
            'tokens': row['known_tokens']})
    output['provenance'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in (AUDIT, SUMMARY, SIGNALS, REPOSITORY_SUMMARY, REPOSITORY_CHECKS,
                                      REPOSITORY_AUDIT, NATURAL_METHOD, NATURAL_BASELINES, NATURAL_COMPONENTS,
                                      REPOSITORY_SIGNALS, JAX_SUMMARY)}
    return output


def export_tables(data):
    header = r'\textbf{Method} & \textbf{Calls} & \textbf{Input} & \textbf{Output} & \textbf{Tokens} & \textbf{Accepted} \\'
    comparison = [r'\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}lrrrrr@{}}', r'\toprule', header]
    citations = {'cte': 'macedo2025codetransengine', 'msadapter': 'openi2025msadapter',
                 'swe': 'yang2024sweagent', 'matchfix': 'ibrahimzada2025matchfixagent',
                 'intertrans': 'macedo2024intertrans'}
    cited = set()
    for source, order, denominator, panel in [
            ('main', ORDER, 50, '(a) PyTorch to MindSpore'),
            ('cross_language', ['direct', 'intertrans', 'test_repair', 'swe', 'matchfix', 'ladim'], 18,
             '(b) Java/DJL to Python/PyTorch')]:
        comparison += [r'\midrule', r'\multicolumn{6}{l}{\textit{' + panel + r'}} \\']
        for method in order:
            row = data['main'][method] if source == 'main' else next(r for r in data[source] if r['key'] == method)
            assert row['input_tokens'] + row['output_tokens'] == row['tokens']
            label = TABLE_LABELS[method]
            if method in citations and method not in cited:
                label += r'~\citep{' + citations[method] + '}'
                cited.add(method)
            accepted = f"{row['accepted']}/{denominator}"
            if (source == 'main' and row['accepted'] == 50) or (source == 'cross_language' and row['accepted'] == 9):
                accepted = r'\textbf{' + accepted + '}'
            usage = ('-- & -- & -- & --' if method == 'msadapter' else
                     f"{row['calls']:,} & {row['input_tokens']/1e6:.3f} & {row['output_tokens']/1e6:.3f} & {row['tokens']/1e6:.3f}")
            comparison.append(f"{label} & {usage} & {accepted}" + r' \\')
    comparison += [r'\bottomrule', r'\end{tabular*}']
    (ROOT / 'figures/TABLE_program_costs.tex').write_text('\n'.join(comparison) + '\n')
    for repository_name, panel in [('timeseries', '(c) Time series repository'),
                                    ('twotower', '(d) Recommendation repository')]:
        entry_label = r'\textbf{Entries}' if repository_name == 'timeseries' else r'\textbf{Tests}'
        comparison += [r'\par\vspace{5pt}', r'\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}lrrrrrr@{}}',
            r'\toprule', r'\multicolumn{7}{l}{\textit{' + panel + r'}} \\', r'\midrule',
            r'\textbf{Method} & \textbf{Checks} & \textbf{Gradients} & \thead{Parameter\\updates} & ' + entry_label + r' & \textbf{Calls} & \textbf{Tokens} \\', r'\midrule']
        for method in ('swe', 'matchfix', 'ladim'):
            row = next(r for r in data['repository'] if r['repository'] == repository_name and r['method'] == method)
            checked = row['paired_checks']
            signals = row['main_table_signals']
            gradient, update, entry = [signals[key] for key in ('gradient', 'update', 'entry_points')]
            ratio = lambda value: 'n/a' if value['passed'] is None else f"{value['passed']}/{value['expected']}"
            passed, calls = f"{checked['passed']}/{checked['expected']}", str(row['repair_calls'])
            if method == 'ladim':
                if repository_name == 'twotower':
                    passed = r'\textbf{' + passed + '}'
                else:
                    calls = r'\textbf{' + calls + '}'
            comparison.append(f"{TABLE_LABELS[method]} & {passed} & {ratio(gradient)} & {ratio(update)} & {ratio(entry)} & {calls} & {row['tokens']/1e6:.3f}" + r' \\')
        comparison += [r'\bottomrule', r'\end{tabular*}']
    (ROOT / 'figures/TABLE_unified_comparison.tex').write_text('\n'.join(comparison) + '\n')
    labels = [('main/ladim', 'LaDiM'), ('continuous_role/ladim', 'Continuous investigation and repair conversation'),
              ('without_repair_history/ladim', 'Without repair history'),
              ('without_progress_prompt/ladim', 'Without progress reminders'),
              ('main/matchfix', 'MatchFixAgent'), ('matchfix_investigation/matchfix', 'MatchFixAgent with independent investigation'),
              ('main/swe', 'SWE-agent'), ('swe_investigation/swe', 'SWE-agent with independent investigation')]
    component_rows = []
    for key, label in labels:
        row = data['main'][key.split('/')[1]] if key.startswith('main/') else data['variants'][key]
        count = f"{row['accepted']}/50" + (r'$^{\dagger}$' if row['missing'] else '')
        component_rows.append(f"{label} & {count} & {row['tokens']/1e6:.3f}" + r' \\')
    components = [r'\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}lrr@{}}',
                  r'\toprule',
                  r'\textbf{Setting} & \textbf{Accepted} & \textbf{Tokens} \\',
                  r'\midrule', *component_rows, r'\bottomrule', r'\end{tabular*}']
    (ROOT / 'figures/TABLE_unified_components.tex').write_text('\n'.join(components) + '\n')
    signal_labels = {'execution': 'Execution and basic checks',
                     'execution_forward': r'\quad + Forward values',
                     'execution_forward_gradient': r'\quad + Gradients',
                     'all_observations': r'\quad + Parameter updates'}
    signal_rows = []
    for row in data['training_signals']:
        count = f"{row['accepted']}/{row['planned']}"
        missed = str(row['initially_accepted_by_visible_checks'])
        if row['variant'] == 'all_observations':
            count, missed = r'\textbf{' + count + '}', r'\textbf{' + missed + '}'
        signal_rows.append(f"{signal_labels[row['variant']]} & {missed} & {row['tokens']/1e6:.3f} & {count}" + r' \\')
    signals = [r'\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}lrrr@{}}',
               r'\toprule',
               r'\multicolumn{4}{l}{\textit{(a) Training signals: 16 faulty candidates}} \\',
               r'\midrule',
               r'\textbf{Available feedback} & \textbf{Undetected} & \textbf{Tokens} & \textbf{Accepted} \\',
               r'\midrule', *signal_rows, r'\bottomrule', r'\end{tabular*}']
    (ROOT / 'figures/TABLE_training_signals.tex').write_text('\n'.join(signals) + '\n')
    natural = [r'\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}lrrrr@{}}', r'\toprule',
        r'\textbf{Method} & \textbf{Repaired} & \textbf{Preserved} & \textbf{Tokens} & \textbf{Accepted} \\', r'\midrule']
    for row in data['natural_repairs']:
        label = 'Direct repair' if row['method'] == 'direct' else LABELS[row['method']]
        repaired = f"{row['repaired']}/5"
        accepted = f"{row['accepted']}/10"
        if row['method'] == 'ladim':
            repaired = r'\textbf{' + repaired + '}'
            accepted = r'\textbf{' + accepted + '}'
        natural.append(f"{label} & {repaired} & {row['retained']}/5 & {row['tokens']/1e6:.3f} & {accepted}" + r' \\')
    natural += [r'\bottomrule', r'\end{tabular*}']
    (ROOT / 'figures/TABLE_natural_repairs.tex').write_text('\n'.join(natural) + '\n')
    jax_data = json.loads(JAX_SUMMARY.read_text())['summaries']
    jax_rows = [next(r for r in jax_data if r['method'] == key)
                for key in ('autonomous_layered', 'direct_shared_tools', 'ivy', 'torch2jax')]
    for row in jax_rows:
        assert row['completed'] == row['recorded'] == row['planned'] == 6
        assert row.get('unknown_usage_calls', 0) == 0
    jax = [r'\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}lrrrr@{}}', r'\toprule',
           r'& \multicolumn{2}{c}{\textbf{LLM repair}} & \multicolumn{2}{c}{\textbf{Single native conversion}} \\',
           r'\cmidrule(lr){2-3}\cmidrule(l){4-5}',
           r'\textbf{Metric} & \textbf{LaDiM} & \textbf{Direct repair} & \textbf{Ivy} & \textbf{\texttt{torch2jax}} \\', r'\midrule']
    jax.append('Accepted & ' + ' & '.join(f"{r['accepted']}/{r['planned']}" for r in jax_rows) + r' \\')
    jax.append('LLM calls & ' + ' & '.join(str(r['calls']) for r in jax_rows) + r' \\')
    jax.append('Total tokens & ' + ' & '.join(f"{r['known_total_tokens']:,}" for r in jax_rows) + r' \\')
    jax += [r'\bottomrule', r'\end{tabular*}']
    (ROOT / 'figures/TABLE_jax_repairs.tex').write_text('\n'.join(jax) + '\n')
    components = [r'\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}>{\raggedright\arraybackslash}p{4.6cm}rrrr@{}}', r'\toprule',
        r'\textbf{Condition} & \textbf{Repaired} & \textbf{Preserved} & \textbf{Tokens} & \textbf{Accepted} \\', r'\midrule']
    for row in data['natural_components']:
        components.append(f"{row['label']} & {row['repaired']}/5 & {row['retained']}/5 & {row['tokens']/1e6:.3f} & {row['accepted']}/10" + r' \\')
    components += [r'\bottomrule', r'\end{tabular*}']
    (ROOT / 'figures/TABLE_natural_components.tex').write_text('\n'.join(components) + '\n')
    program = [r'\textit{(b) Repair history and independent evidence handoff on ten translated programs}\par\smallskip',
        r'\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}>{\raggedright\arraybackslash}p{4.3cm}rrrr@{}}', r'\toprule',
        r'\textbf{Condition} & \textbf{Repaired} & \textbf{Preserved} & \textbf{Accepted} & \textbf{Tokens} \\', r'\midrule']
    for row in data['natural_components'][:3]:
        program.append(f"{row['label']} & {row['repaired']}/5 & {row['retained']}/5 & {row['accepted']}/10 & {row['tokens']:,}" + r' \\')
    program += [r'\bottomrule', r'\end{tabular*}']
    (ROOT / 'figures/TABLE_program_components.tex').write_text('\n'.join(program) + '\n')
    costs = [r'\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}lrrrrrrr@{}}', r'\toprule',
        r'\textbf{Method} & \textbf{Gradients} & \thead{Parameter\\updates} & \textbf{Calls} & \textbf{Submissions} & \textbf{Input} & \textbf{Output} & \textbf{Tokens} \\']
    for repo, label in [('timeseries', 'Time series'), ('twotower', 'Recommendation')]:
        costs += [r'\midrule', r'\multicolumn{8}{l}{\textit{' + label + r'}} \\']
        for row in (r for r in data['repository'] if r['repository'] == repo):
            signals = row['main_table_signals']
            ratios = [f"{signals[k]['passed']}/{signals[k]['expected']}" for k in ('gradient', 'update')]
            costs.append(f"{LABELS[row['method']]} & " + ' & '.join(ratios) +
                         f" & {row['repair_calls']} & {row['submissions']} & {row['repair_prompt_tokens']:,} & {row['repair_completion_tokens']:,} & {row['tokens']:,}" + r' \\')
    costs += [r'\bottomrule', r'\end{tabular*}']
    (ROOT / 'figures/TABLE_repository_costs.tex').write_text('\n'.join(costs) + '\n')
    details = {r['method']: r['details'] for r in data['repository'] if r['repository'] == 'twotower'}
    check_table = [r'\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}lrrr@{}}', r'\toprule',
        r'\textbf{Check} & \textbf{LaDiM} & \textbf{SWE-agent} & \textbf{MatchFixAgent} \\', r'\midrule']
    for label, key in [('Behavior checks passed', 'protocol_checks'), ('Numerical checks', 'numerical_checks'),
                       ('Training checks', 'training_checks'), ('Inference retrieval', 'retrieval_checks')]:
        values = [f"{details[m][key]['passed']}/{details[m][key]['expected']}" for m in ('ladim', 'swe', 'matchfix')]
        check_table.append(label + ' & ' + ' & '.join(values) + r' \\')
    check_table += [r'\midrule']
    for label, key in [('User representations', 'user_embedding'), ('Item representations', 'item_embedding'),
                       ('Forward loss', 'loss'), ('Training return loss', 'epoch_loss'),
                       ('Gradients', 'gradient'), ('Parameter updates', 'update')]:
        values = [f"{details[m]['training_signals'][key]['passed']}/18" for m in ('ladim', 'swe', 'matchfix')]
        check_table.append(label + ' & ' + ' & '.join(values) + r' \\')
    check_table += [r'\midrule']
    for label, key in [('Original tests', 'original_tests'), ('Training command', 'workflow_accepted'),
                       ('File coverage', 'coverage_accepted'), ('Documentation and dependencies', 'documentation_accepted')]:
        values=[]
        for method in ('ladim', 'swe', 'matchfix'):
            value=details[method][key]
            values.append(('n/a' if value['passed'] is None else f"{value['passed']}/10") if key=='original_tests'
                          else ('1/1' if value else '0/1'))
        check_table.append(label + ' & ' + ' & '.join(values) + r' \\')
    check_table += [r'\bottomrule', r'\end{tabular*}']
    (ROOT / 'figures/TABLE_repository_checks.tex').write_text('\n'.join(check_table) + '\n')
    target = ROOT / 'data/paper_figures/unified_results.json'
    target.write_text(json.dumps(data, indent=2) + '\n')


def export_compact_tables(data):
    """Use task columns and adjacent panels while retaining the full cost tables."""
    compact = []
    for index, (source, order, denominator, title) in enumerate([
            ('main', ORDER, 50, '(a) PyTorch to MindSpore'),
            ('cross_language', ['direct', 'intertrans', 'test_repair', 'swe', 'matchfix', 'ladim'], 18,
             '(b) Java/DJL to Python/PyTorch')]):
        if index:
            compact.append(r'\hfill')
        compact += [r'\begin{minipage}[t]{0.485\linewidth}', r'\vspace{0pt}',
                    r'\raggedright\textit{' + title + r'}\par\smallskip',
                    r'\setlength{\tabcolsep}{2pt}',
                    r'\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}>{\raggedright\arraybackslash}p{2.3cm}rrr@{}}',
                    r'\toprule', r'\textbf{Method} & \textbf{Calls} & \textbf{Tokens} & \textbf{Accepted} \\', r'\midrule']
        for method in order:
            row = data['main'][method] if source == 'main' else next(r for r in data[source] if r['key'] == method)
            accepted = f"{row['accepted']}/{denominator}"
            if row['accepted'] == (50 if source == 'main' else 9):
                accepted = r'\textbf{' + accepted + '}'
            usage = '-- & --' if method == 'msadapter' else f"{row['calls']:,} & {row['tokens']/1e6:.3f}"
            compact.append(f"{TABLE_LABELS[method]} & {usage} & {accepted}" + r' \\')
        compact += [r'\bottomrule', r'\end{tabular*}', r'\end{minipage}']
    compact += [r'\par\medskip', r'\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}lrrrrrrrr@{}}', r'\toprule',
                r'& \multicolumn{4}{c}{\textit{(c) Time series repository}} & \multicolumn{4}{c}{\textit{(d) Recommendation repository}} \\',
                r'\cmidrule(lr){2-5}\cmidrule(l){6-9}',
                r'\textbf{Method} & \textbf{Checks} & \textbf{Entries} & \textbf{Calls} & \textbf{Tokens} & \textbf{Checks} & \textbf{Tests} & \textbf{Calls} & \textbf{Tokens} \\', r'\midrule']
    for method in ('swe', 'matchfix', 'ladim'):
        cells = [TABLE_LABELS[method]]
        for repository in ('timeseries', 'twotower'):
            row = next(r for r in data['repository'] if r['repository'] == repository and r['method'] == method)
            checked = row['paired_checks']
            entry = row['main_table_signals']['entry_points']
            count = f"{checked['passed']}/{checked['expected']}"
            if method == 'ladim' and repository == 'twotower':
                count = r'\textbf{' + count + '}'
            calls = str(row['repair_calls'])
            if method == 'ladim' and repository == 'timeseries':
                calls = r'\textbf{' + calls + '}'
            cells += [count, f"{entry['passed']}/{entry['expected']}", calls, f"{row['tokens']/1e6:.3f}"]
        compact.append(' & '.join(cells) + r' \\')
    compact += [r'\bottomrule', r'\end{tabular*}']
    (ROOT / 'figures/TABLE_main_comparison.tex').write_text('\n'.join(compact) + '\n')

    signal_labels = ['Execution and basic checks', r'\quad + Forward values', r'\quad + Gradients', r'\quad + Parameter updates']
    signals = [r'\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}lrr@{}}',
               r'\toprule', r'\textbf{Feedback} & \textbf{Accepted} & \textbf{Tokens} \\', r'\midrule']
    for label, row in zip(signal_labels, data['training_signals']):
        accepted = f"{row['accepted']}/{row['planned']}"
        if row['accepted'] == row['planned']:
            accepted = r'\textbf{' + accepted + '}'
        signals.append(f"{label} & {accepted} & {row['tokens']:,}" + r' \\')
    signals += [r'\bottomrule', r'\end{tabular*}']
    (ROOT / 'figures/TABLE_training_signals_compact.tex').write_text('\n'.join(signals) + '\n')

    program = [r'\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}lrr@{}}',
               r'\toprule', r'\textbf{Condition} & \textbf{Accepted} & \textbf{Tokens} \\', r'\midrule']
    for row in data['natural_components'][:3]:
        accepted = f"{row['accepted']}/10 ({row['repaired']}/5)"
        if row['accepted'] == 9:
            accepted = r'\textbf{' + accepted + '}'
        program.append(f"{row['label']} & {accepted} & {row['tokens']:,}" + r' \\')
    program += [r'\bottomrule', r'\end{tabular*}']
    (ROOT / 'figures/TABLE_program_components_compact.tex').write_text('\n'.join(program) + '\n')


def build_figure():
    """Actual manuscript width, with every paired input shown as signed savings."""
    data = load_data()
    fig, (a, b) = plt.subplots(1, 2, figsize=(5.5, 2.2),
                              gridspec_kw={'width_ratios': [1, 1.25]})
    stage_keys = ['translation', 'initially_accepted', 'initially_faulty']
    stage_colors = ['#E2E6E9', '#7BB2C9', BLUE]
    for y, method in enumerate(('ladim', 'matchfix', 'swe')):
        left = 0
        for key, color in zip(stage_keys, stage_colors):
            value = data['cost_stages'][method][key] / 1e6
            a.barh(y, value, left=left, height=.43, color=color,
                   edgecolor='white', linewidth=.4)
            left += value
        a.text(left + .35, y, f'{left:.2f}', va='center', fontsize=8)
    a.set(yticks=range(3), yticklabels=['LaDiM', 'MatchFixAgent', 'SWE-agent'],
          xlim=(0, 24), ylim=(2.55, -.75), xlabel='Total tokens (millions)')
    a.set_xticks([0, 10, 20])
    a.set_title('(a) Total tokens', loc='left', fontsize=9, pad=8)
    a.legend(handles=[Patch(facecolor=color, label=label) for color, label in zip(
             stage_colors, ['Initial translation', 'Passes before repair', 'Needs repair'])],
             loc='upper right', bbox_to_anchor=(1.16, 1.0),
             frameon=False, fontsize=8, handlelength=.85,
             handletextpad=.35, labelspacing=.2, borderaxespad=.15)
    a.grid(axis='x', color='#E9ECEF', linewidth=.45)
    ordered = []
    for state in (True, False):
        ordered.extend(sorted((p for p in data['paired_costs'] if p['initially_accepted'] == state),
                              key=lambda p: p['matchfix_tokens'] - p['ladim_tokens']))
    savings = np.array([(p['matchfix_tokens'] - p['ladim_tokens']) / 1000 for p in ordered])
    b.bar(np.arange(len(ordered)), savings, width=.76,
          color=['#009E73' if value >= 0 else ORANGE for value in savings], zorder=3)
    b.axhline(0, color=GRAY, linewidth=.7, zorder=4)
    b.axvline(19.5, color=GRAY, linestyle=(0, (2, 3)), linewidth=.55)
    b.set(xlim=(-1, 29), ylim=(-200, 1400), ylabel='Tokens saved by LaDiM\n(thousands)',
          yticks=[0, 250, 500, 750, 1000, 1250], xticks=[9.5, 24],
          xticklabels=['Passes before repair', 'Needs repair'],
          xlabel='Migration inputs')
    b.legend(handles=[Patch(facecolor='#009E73', label='Fewer tokens'),
                      Patch(facecolor=ORANGE, label='More tokens')],
             loc='upper left', frameon=False, fontsize=8, handlelength=.85,
             handletextpad=.35, labelspacing=.2, borderaxespad=.15)
    b.set_title('(b) Savings on each input', loc='left', fontsize=9, pad=8)
    b.grid(axis='y', color='#E9ECEF', linewidth=.45)
    for ax in (a, b):
        ax.set_axisbelow(True)
        ax.tick_params(axis='both', labelsize=8, length=2, color='#92989E')
        for side in ('left', 'bottom'):
            ax.spines[side].set_color('#B3BAC0')
        ax.xaxis.label.set_fontsize(8)
        ax.yaxis.label.set_fontsize(8)
    fig.subplots_adjust(left=.165, right=.985, top=.84, bottom=.30, wspace=.72)
    return fig


def export_figure():
    fig = build_figure()
    with plt.rc_context({'svg.fonttype': 'none'}):
        for suffix in ('pdf', 'png', 'svg'):
            fig.savefig(ROOT / f'figures/repair_comparison.{suffix}', dpi=300,
                        bbox_inches='tight', pad_inches=.02)
    svg_path = ROOT / 'figures/repair_comparison.svg'
    svg_path.write_text('\n'.join(line.rstrip() for line in svg_path.read_text().splitlines()) + '\n')
    plt.close(fig)


def main():
    data = load_data()
    export_tables(data)
    export_compact_tables(data)
    export_figure()
    print(json.dumps({'main': data['main'], 'variants': data['variants']}, indent=2))


if __name__ == '__main__':
    main()
