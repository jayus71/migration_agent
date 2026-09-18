"""Render the selected slim-v4 results from audited offline exports."""
import csv
from pathlib import Path

from paper_plot_style import BLUE, GREEN, GRAY, plt, save_figure

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / 'output/maintext-results-20260918'


def read(name):
    with (EXPORT / name).open(newline='') as stream:
        return list(csv.DictReader(stream))


def build_figure():
    slim = read('slim_main.csv')
    baseline = read('main_comparison.csv')
    ours = next(r for r in slim if r['benchmark'] == 'Fixed50')
    rows = []
    for method, label, color in [('swe_native_isolated', 'SWE-agent', GRAY),
                                  ('direct_shared_tools', 'Direct', GREEN)]:
        row = next(r for r in baseline if r['benchmark'] == 'Fixed50'
                   and r['version'] == 'formal_v3' and r['method'] == method)
        natural = next(r for r in baseline if r['benchmark'] == 'Natural10'
                       and r['version'] == 'formal_v3' and r['method'] == method)
        rows.append((label, color, row, natural))
    rows.append(('LaDiM (slim v4)', BLUE, ours,
                 next(r for r in slim if r['benchmark'] == 'Natural10')))
    tex = []
    fig, axes = plt.subplots(1, 2, figsize=(5.5, 2.8))
    for label, color, row, natural in rows:
        accepted = int(row['accepted'])
        budgets = [int(row[f'accepted_at_{i}']) for i in (1, 2, 4)]
        assert budgets == sorted(budgets) and budgets[-1] == accepted
        cost = int(row['selected_tokens']) / accepted / 1000
        tex.append(f"{label} & {accepted}/50 & {' / '.join(map(str, budgets))} & "
                   f"{cost:,.1f}K & {natural['actual_faults_repaired']}/5 ; "
                   f"{natural['healthy_retained']}/5 " + r'\\')
        axes[0].scatter(cost, budgets[0] * 2, color=color, s=40)
        axes[0].annotate(label, (cost, budgets[0] * 2), xytext=(0, 7),
                         textcoords='offset points', ha='center', fontsize=7)
        axes[1].plot([1, 2, 4], [n * 2 for n in budgets], color=color,
                     marker='o', label=label, linewidth=1.3, markersize=4)
    axes[0].set(xlabel='Tokens per accepted repair (K)',
                ylabel='First-submission acceptance (%)', xlim=(100, 1750), ylim=(42, 68))
    axes[0].set_xticks([400, 800, 1200, 1600])
    axes[1].set(xlabel='Maximum repair submissions', ylabel='Cumulative acceptance (%)',
                xlim=(0.8, 4.2), ylim=(40, 100), xticks=[1, 2, 4])
    axes[1].legend(loc='upper left', fontsize=6, frameon=False)
    matchfix = next(r for r in baseline if r['benchmark'] == 'Natural10'
                    and r['version'] == 'formal_v3' and r['method'] == 'matchfix_full_orchestration')
    tex.append("MatchFixAgent & n/a & n/a & n/a & "
               f"{matchfix['actual_faults_repaired']}/5 ; {matchfix['healthy_retained']}/5 " + r'\\')
    for ax, label in zip(axes, ['(a)', '(b)']):
        ax.text(0.92 if label == '(b)' else 0.03, 0.96, label,
                transform=ax.transAxes, va='top', fontsize=8)
        ax.grid(color='#dddddd', linewidth=0.4)
        ax.set_axisbelow(True)
    fig.subplots_adjust(left=0.10, right=0.99, bottom=0.22, top=0.97, wspace=0.48)
    (ROOT / 'figures/TABLE_slim_main_rows.tex').write_text('\n'.join(tex) + '\n' + r'\bottomrule' + '\n')
    return fig


def main():
    save_figure(build_figure(), 'repair_comparison')


if __name__ == '__main__':
    main()
