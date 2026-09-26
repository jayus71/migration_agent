"""Build a PDF with LaTeX change marks against the fixed manuscript baseline."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess

from update_manuscript_diff import BASELINE, ROOT, flatten, sha, verify_baseline

OUTPUT = ROOT / 'output/manuscript-latexdiff'
REFERENCES = re.compile(
    r'\\section\*\{References\}\s*\\begin\{thebibliography\}\{[^}]*\}'
    r'.*?\\end\{thebibliography\}', re.S)


def use_current_references(old: str, new: str) -> str:
    """Keep citation keys unique in a review copy of the current manuscript."""
    old_refs = REFERENCES.search(old)
    new_refs = REFERENCES.search(new)
    if not old_refs or not new_refs:
        raise ValueError('Expanded bibliography missing from a manuscript version')
    return old[:old_refs.start()] + new_refs.group() + old[old_refs.end():]


def protect_tables(source: str, blocks: dict[str, str]) -> str:
    """Diff structural table changes as complete versions, preserving their cells."""
    def protect(match):
        content = match.group()
        token = 'REVIEWTABLE' + hashlib.sha256(content.encode()).hexdigest().upper()[:24]
        blocks[token] = content
        return '\n\n' + token + '\n\n'
    return re.sub(r'\\begin\{table\}(?:\[[^]]*\])?.*?\\end\{table\}', protect, source, flags=re.S)


def restore_tables(diff: str, blocks: dict[str, str], current_labels: set[str] | None = None) -> str:
    token_pattern = r'REVIEWTABLE[A-F0-9]{24}'
    # Split markup around tables; ulem must never wrap an alignment environment.
    command = re.compile(r'\\(DIFadd(?:FL)?|DIFdel(?:FL)?)\{')
    offset = 0
    while match := command.search(diff, offset):
        depth, end = 1, match.end()
        while depth:
            if diff[end] in '{}' and diff[end-1] != '\\':
                depth += 1 if diff[end] == '{' else -1
            end += 1
        content = diff[match.end():end-1]
        if not re.search(token_pattern, content):
            offset = end
            continue
        parts = re.split('(' + token_pattern + ')', content)
        replacement = ''.join(
            f'REVIEW{match.group(1).upper()}{part}' if re.fullmatch(token_pattern, part)
            else '\\' + match.group(1) + '{' + part + '}' if part.strip() else part
            for part in parts)
        diff = diff[:match.start()] + replacement + diff[end:]
        offset = match.start() + len(replacement)

    def restore(match):
        status, token = match.group(1), match.group(2)
        block = blocks[token]
        if status:
            added = 'ADD' in status
            color, label = ('blue', 'Current version') if added else ('red', 'Previous version')
            block = block.replace(r'\caption{', r'\caption{\textbf{' + label + r'.} ', 1)
            block = re.sub(r'(\\begin\{table\}(?:\[[^]]*\])?)',
                           lambda m: m.group() + '\n\\color{' + color + '}\n', block, count=1)
            if not added:
                # Deleted prose can still cite a table that was merged or removed.
                # Keep its old label when the current paper no longer defines it.
                block = re.sub(r'\\label\{([^}]+)\}',
                               lambda m: m.group() if current_labels is not None
                               and m.group(1) not in current_labels else '', block)
        return '\n\n' + block + '\n\n'
    return re.sub(r'(?:REVIEW(DIF(?:ADD|DEL)(?:FL)?))?(' + token_pattern + ')', restore, diff)


def review_layout(source: str) -> str:
    """Use ordinary figure placement in the review copy to keep marks readable."""
    source = re.sub(r'\\hyphenpenalty\s*=\s*\d+|\\emergencystretch\s*=\s*[\d.]+\w+', '', source)
    # Line-count hints belong to the clean layout. Markup between an assignment
    # and its integer makes TeX read a brace where it expects a number.
    source = re.sub(r'\\looseness\s*=\s*-?\d+', '', source)
    # Wrapped algorithms use a minipage only in the clean manuscript. Present
    # them at full width here so the change marks have room and floats do not
    # become nested after removing the surrounding wrapfigure.
    def unwrap_algorithm(match):
        body = match.group(1).replace(r'\raggedright', '').replace(r'\allowbreak', '')
        return r'\begin{algorithm}[!htb]' + body + r'\end{algorithm}'
    source = re.sub(
        r'\\begin\{wrapfigure\}\{[rlRL]\}\{[^}]+\}\s*'
        r'\\begin\{minipage\}\{\\linewidth\}\s*'
        r'\\setlength\{\\intextsep\}\{0pt\}\s*'
        r'\\begin\{algorithm\}\[H\](.*?)\\end\{algorithm\}\s*'
        r'\\end\{minipage\}\s*\\end\{wrapfigure\}',
        unwrap_algorithm, source, flags=re.S)
    def unwrap(match):
        body = match.group(2).replace(r'width=\linewidth', 'width=' + match.group(1))
        return r'\begin{figure}[htbp]' + body + r'\end{figure}'
    return re.sub(r'\\begin\{wrapfigure\}\{[rlRL]\}\{([^}]+)\}(.*?)\\end\{wrapfigure\}',
                  unwrap, source, flags=re.S)


def main() -> None:
    meta = verify_baseline(BASELINE)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    old_raw, new_raw = flatten(BASELINE), flatten(ROOT)
    old = review_layout(use_current_references(old_raw, new_raw))
    new = review_layout(new_raw)
    blocks: dict[str, str] = {}
    old, new = protect_tables(old, blocks), protect_tables(new, blocks)
    (OUTPUT/'baseline-expanded.tex').write_text(old)
    (OUTPUT/'current-expanded.tex').write_text(new)
    command = ['latexdiff', '--type=UNDERLINE', '--subtype=SAFE', '--floattype=FLOATSAFE',
               '--math-markup=whole', '--graphics-markup=none',
               '--add-to-config=FLOATENV=algorithm',
               '--label=Fixed baseline: 2026-09-21', f'--label=Current manuscript: {revision[:7]}',
               str(OUTPUT/'baseline-expanded.tex'), str(OUTPUT/'current-expanded.tex')]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=True)
    (OUTPUT/'latexdiff-generation.log').write_text(result.stderr)
    legend = r'''
\begin{center}
{\Large\bfseries LaTeX manuscript comparison}\par\medskip
Fixed baseline: 21 September 2026\par
Current manuscript: REVISION\par\bigskip
\DIFadd{Blue underlining marks added text.}\par\medskip
\DIFdel{Red strikethrough marks removed text.}\par\bigskip
\begin{minipage}{0.9\linewidth}
This review copy compares the manuscript, equations, captions, and tables against
the same fixed baseline as the HTML comparison. Figure assets use the current
versions; image changes are not compared. References use the current list,
while citation changes remain marked in the text. Figure placement is adjusted
for readability. The clean manuscript is unchanged.
\end{minipage}
\end{center}
\clearpage
'''.replace('REVISION', revision[:7])
    diff = restore_tables(result.stdout, blocks,
                          set(re.findall(r'\\label\{([^}]+)\}', new_raw)))
    # Deleted headings can reuse counters in a latexdiff document. Give the
    # review copy unique hyperlink targets for both old and current headings.
    diff = diff.replace(r'\begin{document}',
                        r'\ifdefined\hypersetup\hypersetup{hypertexnames=false}\fi' + '\n'
                        + r'\begin{document}' + legend, 1)
    (OUTPUT/'manuscript-diff.tex').write_text(diff)
    build = subprocess.run(['latexmk', '-norc', '-pdf', '-interaction=nonstopmode',
                            '-halt-on-error', f'-outdir={OUTPUT}',
                            str(OUTPUT/'manuscript-diff.tex')], cwd=ROOT, text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (OUTPUT/'build.log').write_text(build.stdout)
    if build.returncode:
        print(build.stdout[-7000:])
        raise SystemExit(build.returncode)
    manifest = {'baseline': meta['name'], 'current_commit': revision,
                'baseline_expanded_sha256': hashlib.sha256(old_raw.encode()).hexdigest(),
                'current_expanded_sha256': hashlib.sha256(new_raw.encode()).hexdigest(),
                'source_sha256': sha(OUTPUT/'manuscript-diff.tex'),
                'pdf_sha256': sha(OUTPUT/'manuscript-diff.pdf'),
                'markup': 'blue underline additions; red strikethrough deletions',
                'figures': 'Current assets; no image comparison.',
                'references': 'Current bibliography; citation changes remain marked.',
                'build_command': 'python3 scripts/build_manuscript_latexdiff.py'}
    (OUTPUT/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    print(f'LaTeX comparison created: {OUTPUT / "manuscript-diff.pdf"}')


if __name__ == '__main__':
    main()
