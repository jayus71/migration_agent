"""Preview a saved code repair and its audited cumulative token trajectories."""

import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle, FancyArrowPatch
from matplotlib.text import Text

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'docs/review-evidence/tanh-case-20260925'
OUT = ROOT / 'figures/tanh-repair-case'
INK, MUTED, RULE = '#24313c', '#58646f', '#cad2d9'
COLORS = {'LaDiM': '#007c61', 'SWE-agent': '#0072b2', 'MatchFixAgent': '#d55e00'}
for font_name in ['times.ttf', 'timesbd.ttf', 'timesi.ttf', 'timesbi.ttf']:
    for directory in [Path('/mnt/c/Windows/Fonts'), Path('C:/Windows/Fonts')]:
        font_path = directory / font_name
        if font_path.exists():
            font_manager.fontManager.addfont(str(font_path))
            break
TNR = font_manager.findfont('Times New Roman', fallback_to_default=False)
plt.rcParams.update({'font.family': 'Times New Roman',
                     'font.size': 8, 'mathtext.fontset': 'custom',
                     'mathtext.rm': 'Times New Roman', 'mathtext.it': 'Times New Roman:italic',
                     'mathtext.bf': 'Times New Roman:bold', 'pdf.fonttype': 42,
                     'svg.fonttype': 'none', 'axes.linewidth': .6,
                     'text.color': INK, 'axes.labelcolor': INK,
                     'xtick.color': MUTED, 'ytick.color': MUTED})


def load_evidence():
    summary = json.loads((DATA / 'summary.json').read_text())
    rows = list(csv.DictReader((DATA / 'calls.csv').open()))
    series = {}
    for method in summary['methods']:
        name = method['method']
        own = [r for r in rows if r['method'] == name]
        calls = [int(r['call']) for r in own]
        tokens = [int(r['cumulative_tokens']) for r in own]
        assert calls == list(range(1, method['calls'] + 1))
        assert sum(int(r['total_tokens']) for r in own) == tokens[-1] == method['usage']['total_tokens']
        assert all(b > a for a, b in zip(tokens, tokens[1:]))
        series[name] = (calls, [t / 1e6 for t in tokens])
    patch = (DATA / 'repair.patch').read_text()
    additions = [line[1:] for line in patch.splitlines() if line.startswith('+') and not line.startswith('+++') and line[1:].strip()]
    expected = ['@register_function(torch.tanh)', '@register_function(torch.nn.functional.tanh)',
                'def functional_tanh(input):', '    return mops.tanh(input)']
    assert additions == expected
    assert summary['all_initial_code_files_identical'] and summary['all_initial_observations_identical']
    for method in summary['methods'][1:]:
        assert not method['accepted'] and not method['changed_production_files']
    return summary, series, additions


WIDTH, HEIGHT = 396, 176.4


def label(ax, x, y, content, size=8.5, **kwargs):
    """Place every non-chart item on one shared point grid, from the top left."""
    return ax.text(x, y, content, fontsize=size, va='top', **kwargs)


def panel_box(ax, x, y, width, height, face='#ffffff', edge=RULE):
    ax.add_patch(Rectangle((x, y), width, height, facecolor=face,
                           edgecolor=edge, linewidth=.6, zorder=0))


def diagnosis_panel(ax, summary):
    observation = summary['methods'][0]['initial']['observation']
    assert observation['execution']['target']['status'] == 'passed'
    assert observation['acceptance']['checks']['loss_abs_diff']
    parameters = observation['gradient_vector_comparison']['parameters']
    assert all(p['candidate_gradient_norm'] == 0 for p in parameters[:2])
    assert max(p['gradient_l2_diff'] for p in parameters[2:]) < 6.16e-7
    probe = json.loads((DATA / 'tool-evidence.json').read_text())[0]['event']['data']
    assert probe['call'] == 17 and probe['result']['returncode'] == 0
    assert "dispatch_tanh: ['sum_abs=0.000000e+00']" in probe['result']['stdout']
    label(ax, 8, 7, '(a) Diagnosis and repair', 9.5, fontweight='bold')
    panel_box(ax, 8, 27, 194, 73, '#f7f9fa')
    label(ax, 105, 32, 'Forward: loss matches source', 8.8, ha='center')
    for x, name in [(16, 'Linear'), (83, 'Tanh'), (150, 'Linear')]:
        suspect = name == 'Tanh'
        panel_box(ax, x, 49, 44, 19, '#fff0e6' if suspect else '#ffffff',
                  '#c25a18' if suspect else RULE)
        label(ax, x + 22, 53, name, 9, ha='center', fontweight='bold' if suspect else 'normal',
              color='#a34511' if suspect else INK)
    for start, end in [(61, 81), (128, 148)]:
        ax.add_patch(FancyArrowPatch((start, 58.5), (end, 58.5), arrowstyle='-|>',
                                     mutation_scale=7, color=MUTED, linewidth=.8))
    label(ax, 38, 73, 'Zero gradients', 8.3, ha='center', color='#a34511')
    label(ax, 172, 73, 'Gradients match', 8.3, ha='center', color=COLORS['LaDiM'])
    ax.add_patch(FancyArrowPatch((105, 83), (105, 69), arrowstyle='-|>',
                                 mutation_scale=7, color='#a34511', linewidth=.8))
    label(ax, 105, 87, 'Probe confirms gradient break at Tanh', 8.3, ha='center')


def code_panel(ax, additions):
    label(ax, 8, 108, 'SWE-agent / MatchFixAgent', 8.5, fontweight='bold')
    label(ax, 202, 108, 'No edit', 8.5, ha='right', color='#a34511')
    panel_box(ax, 8, 123, 194, 45)
    label(ax, 15, 127, 'LaDiM · added Tanh mapping', 8.8, fontweight='bold', color=COLORS['LaDiM'])
    ax.add_patch(Rectangle((11, 138), 188, 27, facecolor='#dcefe2', edgecolor='none', zorder=1))
    ax.add_patch(Rectangle((11, 138), 1.8, 27, facecolor=COLORS['LaDiM'], edgecolor='none', zorder=2))
    # Display the two-line implementation excerpt. The complete, verified patch
    # also registers torch.tanh and torch.nn.functional.tanh; see the caption.
    for i, line in enumerate(additions[2:]):
        label(ax, 16, 141 + 11 * i, '+', 9, color=COLORS['LaDiM'], zorder=3)
        label(ax, 25, 141 + 11 * i, line, 9, color='#16432b', zorder=3)


def trajectory_panel(ax, series):
    styles = {'LaDiM': '-', 'SWE-agent': '--', 'MatchFixAgent': ':'}
    for name, (calls, tokens) in series.items():
        ax.plot([0] + calls, [0] + tokens, color=COLORS[name], lw=1.5, linestyle=styles[name], label=name)
        ax.scatter(calls[-1], tokens[-1], marker='o' if name == 'LaDiM' else 'x',
                   color=COLORS[name], s=24, linewidths=1.1, zorder=5)
    ax.set(xlim=(0, 50), ylim=(0, 2.7), xlabel='LLM calls', ylabel='Cumulative tokens (millions)')
    ax.set_xticks([0, 10, 20, 30, 40])
    ax.set_yticks([0, .5, 1, 1.5, 2, 2.5])
    ax.tick_params(labelsize=8, width=.5, length=2.5, pad=2)
    ax.xaxis.label.set_size(8.5)
    ax.yaxis.label.set_size(8.5)
    ax.spines[['top', 'right']].set_visible(False)
    ax.spines[['left', 'bottom']].set_color(RULE)
    ax.grid(axis='y', color='#e5e9ed', lw=.5)
    ax.set_axisbelow(True)
    tokens = series['LaDiM'][1]
    labels = [(17, '17 Test', (2.0, 1.03)), (22, '22 Patch', (2.0, 1.63)),
              (23, '23 Accepted', (2.0, 2.18))]
    for call, label, where in labels:
        ax.scatter(call, tokens[call - 1], s=18, facecolor='white', edgecolor=COLORS['LaDiM'], linewidth=.9, zorder=6)
        ax.annotate(label, (call, tokens[call - 1]), xytext=where, fontsize=8, color=COLORS['LaDiM'],
                    arrowprops={'arrowstyle': '-', 'color': COLORS['LaDiM'], 'lw': .65},
                    bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': .7})
    ax.text(24.5, 1.77, '1.488', fontsize=8.5, color=COLORS['LaDiM'])
    ax.text(41.8, 2.341, '2.341', va='center', fontsize=8.5, color=COLORS['MatchFixAgent'])
    ax.text(41.8, 1.606, '1.606', va='center', fontsize=8.5, color=COLORS['SWE-agent'])


def build_figure(summary, series, additions):
    fig = plt.figure(figsize=(WIDTH / 72, HEIGHT / 72), dpi=180)
    canvas = fig.add_axes([0, 0, 1, 1], xlim=(0, WIDTH), ylim=(HEIGHT, 0))
    canvas.set_axis_off()
    diagnosis_panel(canvas, summary)
    code_panel(canvas, additions)
    label(canvas, 222, 7, '(b) Repair cost', 9.5, fontweight='bold')
    ax = fig.add_axes([242 / WIDTH, (HEIGHT - 145) / HEIGHT, 144 / WIDTH, 99 / HEIGHT])
    trajectory_panel(ax, series)
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper left', bbox_to_anchor=(222 / WIDTH, 1 - 29 / HEIGHT),
               ncol=3, fontsize=7.5, frameon=False, borderaxespad=0,
               handlelength=1.25, columnspacing=.7, handletextpad=.3)
    return fig


def main():
    summary, series, additions = load_evidence()
    OUT.mkdir(parents=True, exist_ok=True)
    fig = build_figure(summary, series, additions)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bounds = []
    for artist in fig.findobj(Text):
        if not artist.get_visible() or not artist.get_text():
            continue
        bb = Text.get_window_extent(artist, renderer)
        if bb.width == 0 or bb.height == 0:
            continue
        assert artist.get_fontfamily() == ['Times New Roman']
        bounds.append({'text': artist.get_text(), 'font_points': artist.get_fontsize(),
                       'bbox_pixels': list(bb.extents),
                       'inside_canvas': bool(bb.x0 >= -.5 and bb.y0 >= -.5 and bb.x1 <= fig.bbox.width + .5 and bb.y1 <= fig.bbox.height + .5)})
    for suffix in ['pdf', 'svg', 'png']:
        fig.savefig(OUT / ('tanh_repair_case.' + suffix), dpi=300, metadata={'Creator': 'Matplotlib'} if suffix == 'pdf' else None)
    svg_path = OUT / 'tanh_repair_case.svg'
    svg_path.write_text('\n'.join(line.rstrip() for line in svg_path.read_text().splitlines()) + '\n')
    overlaps = []
    for i, a in enumerate(bounds):
        for b in bounds[i + 1:]:
            x0, y0, x1, y1 = a['bbox_pixels']
            u0, v0, u1, v1 = b['bbox_pixels']
            if min(x1, u1) - max(x0, u0) > 1 and min(y1, v1) - max(y0, v0) > 1:
                overlaps.append([a['text'], b['text']])
    curve_overlaps = []
    for ax in fig.axes:
        for annotation in ax.texts:
            bb = Text.get_window_extent(annotation, renderer)
            for line in ax.lines:
                if line.get_transform().transform_path(line.get_path()).intersects_bbox(bb):
                    curve_overlaps.append([annotation.get_text(), line.get_label()])
    record = {'figure_inches': list(fig.get_size_inches()), 'font_family': 'Times New Roman',
              'minimum_font_points': min(b['font_points'] for b in bounds),
              'all_text_inside_canvas': all(b['inside_canvas'] for b in bounds), 'text_bounds': bounds,
              'inputs_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [DATA / 'summary.json', DATA / 'calls.csv', DATA / 'repair.patch', DATA / 'tool-evidence.json']},
              'text_overlaps': overlaps, 'curve_text_overlaps': curve_overlaps, 'all_calls_plotted': {k: len(v[0]) for k, v in series.items()},
              'final_tokens': {k: v[1][-1] * 1e6 for k, v in series.items()}}
    (OUT / 'layout-check.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({k: v for k, v in record.items() if k != 'text_bounds'}))


if __name__ == '__main__':
    main()
