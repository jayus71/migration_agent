"""Export the complete frozen migration comparison with the 50 task-ID display.

Each source/contract group was executed once. Tokens count real calls, and task
counts expand the declared aliases. An interrupted final result stays missing.
"""
import hashlib
import csv
import json
from pathlib import Path
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator

from paper_plot_style import BLUE, GRAY, GREEN, ORANGE, plt, save_figure

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'data/audits/unified50-preflight-20260918/formal_launch/results_audit_final.json'
SUMMARY = AUDIT.with_name('final_summary.json')
SIGNALS = ROOT / 'data/paper_figures/autonomous_training_signals.csv'
LABELS = {'ladim': 'LaDiM', 'matchfix': 'MatchFixAgent', 'swe': 'SWE-agent',
          'direct': 'Direct LLM', 'cte': 'CodeTransEngine (direct)', 'msadapter': 'MSAdapter',
          'test_repair': 'Test-guided repair'}
TABLE_LABELS = {
    'ladim': r'\textbf{LaDiM (ours)}',
    'matchfix': r'MatchFixAgent~\citep{ibrahimzada2025matchfixagent}',
    'swe': r'SWE-agent~\citep{yang2024sweagent}',
    'direct': 'Direct LLM',
    'cte': r'CodeTransEngine (direct)~\citep{macedo2025codetransengine}',
    'msadapter': r'MSAdapter~\citep{openi2025msadapter}',
    'test_repair': 'Test-guided repair',
    'intertrans': r'InterTrans~\citep{macedo2024intertrans}',
}
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
    output['provenance'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in (AUDIT, SUMMARY, SIGNALS)}
    return output


def export_tables(data):
    main_rows = []
    for method in ORDER:
        row = data['main'][method]
        name = TABLE_LABELS[method]
        count = f"{row['accepted']}/50"
        if method == 'ladim':
            count = r'\textbf{' + count + '}'
        main_rows.append(f"{name} & {count} & {row['tokens']/1e6:.3f} & {row['calls']:,}" + r' \\')
    cross_rows = []
    for method in ['direct', 'intertrans', 'test_repair', 'swe', 'matchfix', 'ladim']:
        row = next(r for r in data['cross_language'] if r['key'] == method)
        label = TABLE_LABELS[method]
        cross_rows.append(f"{label} & {row['accepted']}/18 & {row['tokens']/1e6:.3f} & {row['calls']:,}" + r' \\')
    comparison = [r'\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}lrrr@{}}',
                  r'\toprule',
                  r'\textbf{Method} & \textbf{Accepted} & \thead{Total tokens\\(millions)} & \thead{Model\\calls} \\',
                  r'\midrule', r'\multicolumn{4}{l}{\textit{(a) PyTorch to MindSpore}} \\',
                  *main_rows, r'\midrule',
                  r'\multicolumn{4}{l}{\textit{(b) Java/DJL to Python/PyTorch}} \\',
                  *cross_rows, r'\bottomrule', r'\end{tabular*}']
    (ROOT / 'figures/TABLE_unified_comparison.tex').write_text('\n'.join(comparison) + '\n')
    labels = [('main/ladim', 'LaDiM'), ('continuous_role/ladim', 'Continuous investigation and repair conversation'),
              ('without_repair_history/ladim', 'Without prior repair conversation'),
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
                  r'\textbf{Setting} & \textbf{Accepted} & \thead{Total tokens\\(millions)} \\',
                  r'\midrule', *component_rows, r'\bottomrule', r'\end{tabular*}']
    (ROOT / 'figures/TABLE_unified_components.tex').write_text('\n'.join(components) + '\n')
    signal_labels = {'execution': 'Execution and basic contract',
                     'execution_forward': r'\quad + Forward values',
                     'execution_forward_gradient': r'\quad + Gradients',
                     'all_observations': r'\quad + Parameter updates'}
    signal_rows = []
    for row in data['training_signals']:
        count = f"{row['accepted']}/{row['planned']}"
        missed = str(row['initially_accepted_by_visible_checks'])
        if row['variant'] == 'all_observations':
            count, missed = r'\textbf{' + count + '}', r'\textbf{' + missed + '}'
        signal_rows.append(f"{signal_labels[row['variant']]} & {count} & {missed} & {row['tokens']/1e6:.3f}" + r' \\')
    signals = [r'\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}lrrr@{}}',
               r'\toprule',
               r'\textbf{Available feedback} & \textbf{Accepted} & \thead{Faults passing\\initial checks} & \thead{Total tokens\\(millions)} \\',
               r'\midrule', *signal_rows, r'\bottomrule', r'\end{tabular*}']
    (ROOT / 'figures/TABLE_training_signals.tex').write_text('\n'.join(signals) + '\n')
    target = ROOT / 'data/paper_figures/unified_results.json'
    target.write_text(json.dumps(data, indent=2) + '\n')


def build_figure():
    data = load_data()
    fig, axes = plt.subplots(1, 2, figsize=(5.5, 2.85))
    agents = ['swe', 'matchfix', 'ladim']
    ax = axes[0]
    for y, method in enumerate(agents):
        row = data['main'][method]
        value = row['tokens'] / 1e6
        ax.barh(y, value, color=COLORS[method], height=.55)
        ax.text(value + .4, y, f"{value:.2f}", ha='left', va='center', fontsize=7.5)
    ax.set(yticks=range(3), yticklabels=[LABELS[m] for m in agents],
           xlabel='End-to-end tokens (millions)', xlim=(0, 25), ylim=(-.65, 3.1))
    ax.text(.03, .97, '(a) Agent token use', transform=ax.transAxes, va='top', fontsize=8)
    ax.grid(axis='x', color='#dddddd', linewidth=.4)
    ax = axes[1]
    for initial, marker, color, label in [(True, 'o', GRAY, 'Initially accepted'),
                                          (False, '^', BLUE, 'Initially faulty')]:
        points = [p for p in data['paired_costs'] if p['initially_accepted'] == initial]
        ax.scatter([p['matchfix_tokens'] / 1000 for p in points],
                   [p['ladim_tokens'] / 1000 for p in points],
                   label=label, marker=marker, color=color, s=18, linewidths=.4,
                   edgecolors='white', zorder=3)
    ax.plot([30, 2000], [30, 2000], '--', color='#888888', linewidth=.8, zorder=1)
    ax.set(xscale='log', yscale='log', xlim=(30, 2000), ylim=(30, 2000),
           xlabel='MatchFixAgent tokens\n(thousands)', ylabel='LaDiM tokens (thousands)')
    for axis in (ax.xaxis, ax.yaxis):
        axis.set_major_locator(FixedLocator([50, 200, 1000]))
        axis.set_major_formatter(FuncFormatter(lambda value, _: f'{value:g}'))
        axis.set_minor_locator(NullLocator())
    ax.text(.03, .97, '(b) Tokens per input', transform=ax.transAxes, va='top', fontsize=8)
    cheaper = sum(p['ladim_tokens'] < p['matchfix_tokens'] for p in data['paired_costs'])
    ax.text(.96, .04, f'Lower LaDiM use\non {cheaper}/{len(data["paired_costs"])} inputs',
            transform=ax.transAxes, ha='right', va='bottom', fontsize=7)
    ax.legend(loc='upper left', bbox_to_anchor=(0, .87), frameon=False, fontsize=7,
              borderaxespad=.2, handletextpad=.3)
    ax.grid(color='#dddddd', linewidth=.4)
    for ax in axes:
        ax.set_axisbelow(True)
    fig.subplots_adjust(left=.18, right=.99, bottom=.25, top=.98, wspace=.63)
    return fig


def main():
    data = load_data()
    export_tables(data)
    save_figure(build_figure(), 'repair_comparison')
    print(json.dumps({'main': data['main'], 'variants': data['variants']}, indent=2))


if __name__ == '__main__':
    main()
