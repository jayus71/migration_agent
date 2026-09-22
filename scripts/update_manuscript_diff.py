"""Refresh a self-contained word comparison against the frozen September 21 paper."""
from __future__ import annotations

import argparse
from collections import OrderedDict
from datetime import datetime
from difflib import SequenceMatcher
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / 'data/manuscript_baselines/pre-6pro-20260921'
OUTPUT = ROOT / 'output/manuscript-comparison'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_baseline(root):
    meta = json.loads((root / 'baseline.json').read_text())
    for relative, expected in meta['sha256'].items():
        if sha(root / relative) != expected:
            raise ValueError(f'Frozen baseline changed: {relative}')
    return meta


def flatten(root, relative='conference_101719.tex', stack=()):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or path in stack:
        raise ValueError(f'Invalid manuscript include: {relative}')
    source = path.read_text()
    source = re.sub(r'(?<!\\)%[^\n]*', '', source)

    def include(match):
        name = match.group(1)
        if not Path(name).suffix:
            name += '.tex'
        return '\n' + flatten(root, name, (*stack, path)) + '\n'

    source = re.sub(r'\\(?:input|include)\{([^}]+)\}', include, source)
    source = re.sub(r'\\ificlrfinal\b.*?\\fi\b', '', source, flags=re.S)
    bbl = root / 'conference_101719.bbl'
    if bbl.exists():
        source = re.sub(r'\\bibliography\{[^}]+\}',
                        lambda _: '\n\\section*{References}\n' + bbl.read_text(), source)
    return source


def split_sections(source):
    source = source.split(r'\begin{document}', 1)[-1].split(r'\end{document}', 1)[0]
    abstract = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', source, re.S)
    if not abstract:
        raise ValueError('Abstract missing from manuscript')
    title = re.search(r'\\title\{(.*?)\}\s*\\author', source, re.S)
    result = OrderedDict()
    if title:
        result['Title'] = title.group(1)
    result['Abstract'] = abstract.group(1)
    rest = source[abstract.end():]
    headings = list(re.finditer(r'\\section\*?\{([^}]+)\}', rest))
    appendix = rest.find(r'\appendix')
    for i, heading in enumerate(headings):
        title = heading.group(1)
        key = 'Methods' if title == 'LaDiM' else title
        if appendix >= 0 and heading.start() > appendix:
            key = 'Appendix — ' + key
        end = headings[i + 1].start() if i + 1 < len(headings) else len(rest)
        if key in result:
            raise ValueError(f'Duplicate section: {key}')
        result[key] = rest[heading.start():end].strip()
    return result


def reading_text(source):
    """Remove typesetting commands while preserving mathematical content verbatim."""
    protected = []

    def protect(match):
        protected.append(match.group())
        return f' LATEXMATHPLACEHOLDER{len(protected) - 1}END '

    source = re.sub(r'\\begin\{(align\*?|equation\*?|gather\*?)\}.*?\\end\{\1\}',
                    protect, source, flags=re.S)
    source = re.sub(r'(?<!\\)\$\$.*?(?<!\\)\$\$|(?<!\\)\$[^$]*?(?<!\\)\$',
                    protect, source, flags=re.S)
    source = re.sub(r'\\\[.*?\\\]|\\\(.*?\\\)', protect, source, flags=re.S)
    source = re.sub(r'\\label\{[^}]+\}', '', source)
    source = re.sub(r'\\(?:vspace|hspace)\*?\{[^}]+\}', ' ', source)
    source = re.sub(r'\\setlength\{[^}]+\}\{[^}]+\}', '', source)
    source = re.sub(r'\\(?:bibliographystyle|includegraphics)(?:\[[^]]*\])?\{[^}]+\}', '', source)
    # Bracketed citation/reference keys stay visible and comparable.
    source = re.sub(r'\\(?:cite\w*|ref|eqref)\{([^}]+)\}', r' [\1] ', source)
    source = re.sub(r'\\begin\{thebibliography\}.*?(?=\\bibitem)', '', source, flags=re.S)
    source = strip_layout_arguments(source)
    value = subprocess.run(['detex', '-l', '-n', '-c', '-e', 'verbatim'],
                           input=source, text=True, check=True, capture_output=True).stdout
    value = re.sub(r'LATEXMATHPLACEHOLDER(\d+)END',
                   lambda match: protected[int(match.group(1))], value)
    return re.sub(r'\s+', ' ', value).strip()


def strip_layout_arguments(source):
    """Remove nested table layout arguments without dropping their cell text."""
    commands = re.compile(r'\\begin\{(tabular\*?|minipage|wrapfigure|algorithmic|algorithm)\}'
                          r'|\\(multicolumn|multirow)\b')

    def skip_group(position):
        while position < len(source) and source[position].isspace():
            position += 1
        if position >= len(source) or source[position] != '{':
            return position
        depth = 0
        for i in range(position, len(source)):
            if source[i] in '{}' and (i == 0 or source[i - 1] != '\\'):
                depth += 1 if source[i] == '{' else -1
                if not depth:
                    return i + 1
        raise ValueError('Unbalanced table layout argument')

    result, previous = [], 0
    for match in commands.finditer(source):
        if match.start() < previous:
            continue
        result.append(source[previous:match.start()])
        env, macro = match.groups()
        position = match.end()
        option = re.match(r'\s*\[[^]]*\]', source[position:])
        if option:
            position += option.end()
        count = {'tabular': 1, 'tabular*': 2, 'minipage': 1,
                 'wrapfigure': 2, 'algorithmic': 0, 'algorithm': 0}.get(env, 2)
        for _ in range(count):
            position = skip_group(position)
        # Keep environment markers for detex; macros retain their content group.
        if env:
            result.append(match.group().replace('tabular*', 'tabular'))
        previous = position
    result.append(source[previous:])
    return ''.join(result).replace(r'\end{tabular*}', r'\end{tabular}')


def chunks(left, right):
    before, after = left.split(), right.split()
    operations = []
    matcher = SequenceMatcher(None, before, after, autojunk=False)
    for tag, i, j, x, y in matcher.get_opcodes():
        operations.append({'kind': tag, 'before': before[i:j], 'after': after[x:y]})
    # The visible word streams must reproduce both inputs exactly.
    assert [word for row in operations for word in row['before']] == before
    assert [word for row in operations for word in row['after']] == after
    return operations


def context(words):
    if len(words) <= 70:
        return html.escape(' '.join(words))
    return (html.escape(' '.join(words[:24])) +
            f' <details class="context"><summary>展开 {len(words) - 48} 个未改动词</summary>' +
            html.escape(' '.join(words[24:-24])) + '</details> ' +
            html.escape(' '.join(words[-24:])))


def render_comparison(sections, titles, mode):
    blocks = []
    for index, title in enumerate(titles):
        rows = sections[title][mode]
        added = sum(len(r['after']) for r in rows if r['kind'] != 'equal')
        removed = sum(len(r['before']) for r in rows if r['kind'] != 'equal')
        changed = bool(added or removed)
        blocks.append(f'<section class="section {"changed" if changed else "unchanged"}" '
                      f'id="{mode}-{index}" data-title="{html.escape(title, quote=True)}">'
                      f'<h2>{html.escape(title)}<span class="count">'
                      f'<b class="removed">−{removed}</b> <b class="added">+{added}</b></span></h2>')
        for row in rows:
            tag = row['kind']
            old = context(row['before']) if tag == 'equal' else html.escape(' '.join(row['before']))
            new = context(row['after']) if tag == 'equal' else html.escape(' '.join(row['after']))
            blocks.append(f'<div class="pair {tag}"><div class="old">{old or "&nbsp;"}</div>'
                          f'<div class="new">{new or "&nbsp;"}</div></div>')
        blocks.append('</section>')
    return '\n'.join(blocks)


PAGE = r'''<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>LaDiM · 论文逐词对照</title>
<style>
:root{color-scheme:light;--ink:#20332f;--muted:#64736e;--line:#dce4df;--paper:#fff;--green:#156b4b;--red:#a43737}
*{box-sizing:border-box}html{scroll-behavior:auto}body{margin:0;background:#f4f6f3;color:var(--ink);font:15px/1.7 system-ui,-apple-system,"Segoe UI",sans-serif}
header{padding:32px 5vw 22px;border-bottom:1px solid var(--line);background:#fff}header .eyebrow{font-size:12px;letter-spacing:2px;color:var(--green);font-weight:700}h1{font-size:30px;letter-spacing:-1px;margin:6px 0}header p{margin:5px 0;color:var(--muted)}a{color:var(--green);text-underline-offset:3px}.meta{font-size:12px}.tools{position:sticky;top:0;z-index:5;background:#f4f6f3f5;backdrop-filter:blur(10px);padding:12px 5vw;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:12px;flex-wrap:wrap}
button,select,input[type=search]{font:inherit;color:var(--ink);border:1px solid #c7d4cc;background:white;border-radius:7px;padding:7px 11px}button{cursor:pointer}button:hover{background:#e7efe9}input[type=search]{width:210px}label{font-size:13px}main{max-width:1550px;margin:24px auto;padding:0 4vw 64px}.column-head,.pair{display:grid;grid-template-columns:1fr 1fr}.column-head{position:sticky;top:var(--tools-height,69px);z-index:3;background:#e8eee8;border:1px solid var(--line);border-radius:8px 8px 0 0}.column-head>div{padding:14px 20px;font-weight:650}.column-head small{display:block;font-weight:400;color:var(--muted)}.section{background:var(--paper);border:1px solid var(--line);margin:16px 0 24px;border-radius:8px;overflow:hidden;scroll-margin-top:calc(var(--tools-height,69px) + 95px)}h2{font-size:17px;margin:0;padding:14px 20px;background:#edf2ed;display:flex;justify-content:space-between;gap:12px;align-items:center}.count{font:12px ui-monospace,monospace;white-space:nowrap}.removed{color:var(--red)}.added{color:var(--green)}.pair>div{padding:7px 20px;overflow-wrap:anywhere;min-width:0}.pair>div+div{border-left:1px solid var(--line)}.pair.equal{color:#61706a}.replace .old,.delete .old{background:#fff0ed;color:#922d2d;text-decoration:line-through;text-decoration-color:#cc8880}.replace .new,.insert .new{background:#e8f7ed;color:#155f41}.pair.insert .old,.pair.delete .new{background:repeating-linear-gradient(135deg,#fff,#fff 5px,#fafbf9 5px,#fafbf9 10px)}details.context{display:inline}details.context summary{display:inline;cursor:pointer;color:#6a7b72;background:#eff3ee;border-radius:4px;padding:1px 6px;font-size:12px}details.context[open]{display:block}details.context[open] summary{display:block}.latex .pair{font-family:ui-monospace,Consolas,monospace;font-size:12px}.hidden{display:none!important}.only-changes .section.unchanged{display:none}.legend{margin-left:auto;font-size:12px}.empty{padding:50px;text-align:center}.footer{font-size:12px;color:var(--muted);margin:20px 0}.status{color:var(--green)}
@media(max-width:760px){header{padding:22px}.tools{padding:10px 14px;gap:8px}.pair>div{padding:7px 10px;font-size:13px}main{padding:0 10px}.legend{display:none}h1{font-size:25px}.column-head>div{padding:10px;font-size:12px}}
@media print{.tools{display:none}.column-head{position:static}body{background:white}main{padding:0}header{padding:0}details.context{display:block}.pair{break-inside:avoid}}
</style>
<body class="only-changes"><header><div class="eyebrow">LADIM / REVISION HISTORY</div>
<h1>论文逐词对照</h1><p>固定原稿与当前稿并排显示。红色为删除，绿色为新增；移动或重写的文字会同时显示在两侧。</p>
<p class="meta">基线：2026-09-21，6 Pro 修改前保存的原稿 · 当前稿更新于 <strong>__TIME__</strong> · <span id="live">编译后自动更新</span></p>
<p class="meta"><a href="baseline.pdf" target="_blank">查看原稿 PDF</a>　<a href="current.pdf" target="_blank">查看当前 PDF</a>　<a href="baseline.tex" download>原稿展开源码</a>　<a href="current.tex" download>当前展开源码</a>　<a href="comparison.json" download>下载完整对照记录</a></p></header>
<div class="tools"><select id="mode" aria-label="对照内容"><option value="reading">正文逐词</option><option value="latex">LaTeX 逐词</option></select>
<select id="jump" aria-label="跳转章节"><option value="">跳转章节</option>__OPTIONS__</select>
<input type="search" id="search" placeholder="按章节或文字筛选" aria-label="搜索对照文字">
<label><input id="changes" type="checkbox" checked> 只看有改动的章节</label><button id="context">展开全部上下文</button><button onclick="location.reload()">刷新</button>
<span class="legend"><span class="removed">− 删除 __REMOVED__ 词</span>　<span class="added">+ 新增 __ADDED__ 词</span></span></div>
<main><div class="column-head"><div>修改前<small>2026-09-21 · 固定基线</small></div><div>当前版本<small>__REVISION__ · 本地工作区</small></div></div>
<div id="reading" class="view">__READING__</div><div id="latex" class="view latex hidden">__LATEX__</div>
<p class="footer">正文视图去除排版指令，保留文字、表格内容和公式源码；LaTeX 视图保留展开后的完整指令。图形外观请对照两份 PDF。基线文件逐项校验，后续更新保持基线不变。</p></main>
<script>
const version='__VERSION__',mode=document.getElementById('mode'),search=document.getElementById('search');
new ResizeObserver(([entry])=>document.documentElement.style.setProperty('--tools-height',entry.target.offsetHeight+'px')).observe(document.querySelector('.tools'));
function filter(){const q=search.value.trim().toLowerCase();document.querySelectorAll('.section').forEach(s=>s.classList.toggle('hidden',q&&!s.textContent.toLowerCase().includes(q)))}
mode.onchange=()=>{document.querySelectorAll('.view').forEach(v=>v.classList.toggle('hidden',v.id!==mode.value));filter()};search.oninput=filter;
document.getElementById('changes').onchange=e=>document.body.classList.toggle('only-changes',e.target.checked);
document.getElementById('jump').onchange=e=>{if(e.target.value==='')return;const section=document.getElementById(mode.value+'-'+e.target.value);section.classList.remove('hidden');document.getElementById('changes').checked=false;document.body.classList.remove('only-changes');section.scrollIntoView({behavior:'instant',block:'start'})};
let expanded=false;document.getElementById('context').onclick=e=>{expanded=!expanded;document.querySelectorAll('details.context').forEach(d=>d.open=expanded);e.target.textContent=expanded?'折叠未改动上下文':'展开全部上下文'};
if(location.protocol.startsWith('http')){document.getElementById('live').textContent='自动跟随编译后的最新版本';setInterval(async()=>{try{let x=await(await fetch('version.json?t='+Date.now(),{cache:'no-store'})).json();if(x.version!==version)location.reload()}catch(e){}},5000)}
</script></body></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    out = args.output.resolve()
    meta = verify_baseline(BASELINE)
    old_source, new_source = flatten(BASELINE), flatten(ROOT)
    before, after = split_sections(old_source), split_sections(new_source)
    titles = list(before) + [title for title in after if title not in before]
    sections = OrderedDict()
    removed = added = 0
    for title in titles:
        left, right = before.get(title, ''), after.get(title, '')
        section = {'reading': chunks(reading_text(left), reading_text(right)),
                   'latex': chunks(left, right)}
        removed += sum(len(x['before']) for x in section['reading'] if x['kind'] != 'equal')
        added += sum(len(x['after']) for x in section['reading'] if x['kind'] != 'equal')
        sections[title] = section
    current_pdf = ROOT / 'conference_101719.pdf'
    version = hashlib.sha256((old_source + new_source + sha(current_pdf) +
                              sha(Path(__file__))).encode()).hexdigest()
    revision = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, text=True).strip()
    timestamp = datetime.now().astimezone().isoformat(timespec='seconds')
    data = {'baseline': meta, 'current': {'base_commit': revision, 'pdf_sha256': sha(current_pdf)},
            'updated': timestamp, 'version': version, 'reading_words_added': added,
            'reading_words_removed': removed, 'sections': sections}
    values = {'TIME': timestamp, 'REVISION': revision, 'VERSION': version,
              'ADDED': str(added), 'REMOVED': str(removed)}
    page = PAGE
    for key, value in values.items():
        page = page.replace('__' + key + '__', html.escape(value))
    page = page.replace('__OPTIONS__', ''.join(f'<option value="{i}">{html.escape(t)}</option>'
                                               for i, t in enumerate(titles)))
    page = page.replace('__READING__', render_comparison(sections, titles, 'reading'))
    page = page.replace('__LATEX__', render_comparison(sections, titles, 'latex'))
    out.mkdir(parents=True, exist_ok=True)
    for name, content in [('index.html', page), ('baseline.tex', old_source), ('current.tex', new_source),
                          ('comparison.json', json.dumps(data, ensure_ascii=False, indent=2) + '\n')]:
        temporary = out / (name + '.tmp')
        temporary.write_text(content)
        temporary.replace(out / name)
    shutil.copy2(BASELINE / 'conference_101719.pdf', out / 'baseline.pdf')
    shutil.copy2(current_pdf, out / 'current.pdf')
    marker = out / 'version.json.tmp'
    marker.write_text(json.dumps({'version': version, 'updated': timestamp}) + '\n')
    marker.replace(out / 'version.json')
    print(f'Manuscript comparison updated: {out / "index.html"} ({len(sections)} sections)')


if __name__ == '__main__':
    main()
