"""Complete measured migration costs for the introduction."""
from pathlib import Path
from make_unified_results import load_data
from paper_plot_style import plt, BLUE, ORANGE, GRAY

ROOT = Path(__file__).resolve().parents[1]


def build_figure():
    data = load_data()
    fig, cost = plt.subplots(figsize=(3.0, 1.48))
    for y, method, color in [(0, 'ladim', BLUE), (1, 'matchfix', ORANGE), (2, 'swe', GRAY)]:
        row = data['main'][method]
        cost.barh(y, row['tokens'] / 1e6, height=.46, color=color)
        cost.text(row['tokens'] / 1e6 + .55, y, f"{row['tokens'] / 1e6:.2f}", fontsize=8, va='center')
    cost.set(yticks=range(3), yticklabels=['LaDiM (50/50)', 'MatchFixAgent (50/50)', 'SWE-agent (44/50)'],
             xlim=(0, 27), ylim=(2.6, -.6), xlabel='Total tokens (millions)', xticks=[0, 10, 20])
    cost.tick_params(labelsize=8, length=2)
    cost.xaxis.label.set_fontsize(8)
    cost.grid(axis='x', color='#E9ECEF', linewidth=.45)
    cost.set_axisbelow(True)
    fig.subplots_adjust(left=.47, right=.99, bottom=.28, top=.96)
    return fig


if __name__ == '__main__':
    fig = build_figure()
    with plt.rc_context({'svg.fonttype': 'none'}):
        for extension in ('pdf', 'png', 'svg'):
            fig.savefig(ROOT / f'figures/migration_motivation.{extension}', dpi=300)
    plt.close(fig)
