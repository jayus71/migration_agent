"""Preview a saved code repair and its audited cumulative token trajectories."""

import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, Rectangle
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


def text(ax, x, y, content, size=8, **kwargs):
    return ax.text(x, y, content, fontsize=size, va='top', transform=ax.transAxes, **kwargs)


def box(ax, y, height, face, edge):
    ax.add_patch(FancyBboxPatch((0, y), 1, height, boxstyle='round,pad=0.008,rounding_size=0.015',
                              transform=ax.transAxes, linewidth=.65, facecolor=face, edgecolor=edge, clip_on=False))


def code_panel(ax, additions):
    ax.set_axis_off()
    text(ax, 0, 1, '(a) Code repair', 9, fontweight='bold')
    box(ax, .51, .37, '#f7f8f9', '#cad2d9')
    text(ax, .03, .851, 'SWE-agent / MatchFixAgent', 8.5, fontweight='bold')
    text(ax, .97, .851, 'Tanh missing', 8, ha='right', color='#a34511')
    baseline = ['@register_function(torch.relu)', '@register_function(torch.nn.functional.relu)',
                'def functional_relu(input, inplace=False):', '    return mops.relu(input)']
    for i, line in enumerate(baseline):
        text(ax, .04, .755 - i * .063, line, 8.5)
    box(ax, .055, .37, '#ffffff', '#9abdae')
    text(ax, .03, .396, 'LaDiM', 8.5, fontweight='bold', color=COLORS['LaDiM'])
    text(ax, .97, .396, 'Repaired', 8, ha='right', color=COLORS['LaDiM'])
    ax.add_patch(Rectangle((.02, .075), .96, .241, transform=ax.transAxes,
                           facecolor='#dcefe2', edgecolor='none', zorder=1))
    ax.add_patch(Rectangle((.02, .075), .009, .241, transform=ax.transAxes,
                           facecolor=COLORS['LaDiM'], edgecolor='none', zorder=2))
    for i, line in enumerate(additions):
        text(ax, .055, .300 - i * .063, '+', 8.5, color='#00644e', zorder=3)
        text(ax, .10, .300 - i * .063, line, 8.5, color='#16432b', zorder=3)


def trajectory_panel(ax, series):
    styles = {'LaDiM': '-', 'SWE-agent': '--', 'MatchFixAgent': ':'}
    for name, (calls, tokens) in series.items():
        ax.plot([0] + calls, [0] + tokens, color=COLORS[name], lw=1.5, linestyle=styles[name], label=name)
        ax.scatter(calls[-1], tokens[-1], marker='o' if name == 'LaDiM' else 'x',
                   color=COLORS[name], s=24, linewidths=1.1, zorder=5)
    ax.set(xlim=(0, 47), ylim=(0, 2.7), xlabel='LLM calls', ylabel='Cumulative tokens (millions)')
    ax.set_xticks([0, 10, 20, 30, 40])
    ax.set_yticks([0, .5, 1, 1.5, 2, 2.5])
    ax.tick_params(labelsize=7.3, width=.5, length=2.5, pad=2)
    ax.xaxis.label.set_size(8)
    ax.yaxis.label.set_size(8)
    ax.spines[['top', 'right']].set_visible(False)
    ax.spines[['left', 'bottom']].set_color(RULE)
    ax.grid(axis='y', color='#e5e9ed', lw=.5)
    ax.set_axisbelow(True)
    tokens = series['LaDiM'][1]
    labels = [(17, '17  Test', (2.0, 1.07)), (22, '22  Patch', (7.0, 1.83)),
              (23, '23  Accepted', (28.0, .32))]
    for call, label, where in labels:
        ax.scatter(call, tokens[call - 1], s=18, facecolor='white', edgecolor=COLORS['LaDiM'], linewidth=.9, zorder=6)
        ax.annotate(label, (call, tokens[call - 1]), xytext=where, fontsize=7.2, color=COLORS['LaDiM'],
                    arrowprops={'arrowstyle': '-', 'color': COLORS['LaDiM'], 'lw': .65},
                    bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': .7})
    ax.annotate('24: 1.488', (24, tokens[-1]), xytext=(25, 2.07), fontsize=7.5, color=COLORS['LaDiM'],
                arrowprops={'arrowstyle': '-', 'color': COLORS['LaDiM'], 'lw': .65})
    ax.text(41, 2.341, '2.341', va='center', fontsize=7.5, color=COLORS['MatchFixAgent'])
    ax.text(41, 1.606, '1.606', va='center', fontsize=7.5, color=COLORS['SWE-agent'])


def build_figure(summary, series, additions):
    fig = plt.figure(figsize=(5.5, 2.45), dpi=180)
    left = fig.add_axes([.018, .025, .505, .95])
    code_panel(left, additions)
    fig.text(.588, .975, '(b) Repair cost', fontsize=9, weight='bold', va='top')
    ax = fig.add_axes([.626, .21, .357, .65])
    trajectory_panel(ax, series)
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper left', bbox_to_anchor=(.58, .94), ncol=2, fontsize=7.2,
               frameon=False, borderaxespad=0, handlelength=1.6, columnspacing=.7, handletextpad=.4)
    fig.text(.71, .016, '× Unrepaired', fontsize=7.5, color=MUTED)
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
              'inputs_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [DATA / 'summary.json', DATA / 'calls.csv', DATA / 'repair.patch']},
              'text_overlaps': overlaps, 'curve_text_overlaps': curve_overlaps, 'all_calls_plotted': {k: len(v[0]) for k, v in series.items()},
              'final_tokens': {k: v[1][-1] * 1e6 for k, v in series.items()}}
    (OUT / 'layout-check.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({k: v for k, v in record.items() if k != 'text_bounds'}))


if __name__ == '__main__':
    main()
