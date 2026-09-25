"""Complete measured migration costs for the introduction."""
from pathlib import Path
from make_unified_results import load_data
from paper_plot_style import plt, BLUE, ORANGE, GRAY

ROOT = Path(__file__).resolve().parents[1]


def build_figure():
    data = load_data()
    fig, cost = plt.subplots(figsize=(2.365, 1.30))
    for x, method, color in [(0, 'ladim', BLUE), (1, 'matchfix', ORANGE), (2, 'swe', GRAY)]:
        row = data['main'][method]
        cost.bar(x, row['tokens'] / 1e6, width=.32, color=color)
        cost.text(x, row['tokens'] / 1e6 + .6, f"{row['tokens'] / 1e6:.3f}",
                  fontsize=8, ha='center', va='bottom')
    cost.set(xticks=range(3), xticklabels=['', '', ''],
             xlim=(-.5, 2.5), ylim=(0, 25), yticks=[0, 10, 20])
    for x, method, acceptance in [(0, 'Ours', '100%'), (1, 'MatchFixAgent', '100%'), (2, 'SWE-agent', '88%')]:
        cost.text(x, -.055, method, transform=cost.get_xaxis_transform(),
                  fontsize=8, fontweight='bold' if method == 'Ours' else 'normal',
                  ha='center', va='top')
        cost.text(x, -.20, acceptance, transform=cost.get_xaxis_transform(),
                  fontsize=8, ha='center', va='top')
    cost.text(.085, -.20, 'Acc.', transform=cost.transAxes,
              fontsize=8, ha='right', va='top')
    cost.set_title('Total tokens (millions)', loc='left', fontsize=8, pad=3)
    cost.tick_params(labelsize=8, length=2, pad=2)
    cost.tick_params(axis='x', length=0)
    cost.grid(axis='y', color='#E9ECEF', linewidth=.45)
    cost.set_axisbelow(True)
    fig.subplots_adjust(left=.13, right=.985, bottom=.27, top=.84)
    return fig


if __name__ == '__main__':
    fig = build_figure()
    with plt.rc_context({'svg.fonttype': 'none'}):
        for extension in ('pdf', 'png', 'svg'):
            fig.savefig(ROOT / f'figures/migration_motivation.{extension}', dpi=300)
    svg = ROOT / 'figures/migration_motivation.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines()) + '\n')
    plt.close(fig)
