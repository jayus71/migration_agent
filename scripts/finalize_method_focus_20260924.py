"""Font measurements and native PowerPoint grouping for the reference rebuild."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import zipfile
from lxml import etree as E

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'tmp/method-flow-focus-20260924'
NS = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}


def prepare_fonts():
    from PIL import ImageFont
    directory = Path(os.environ.get('METHOD_DIAGRAM_FONT_DIR',
                     'C:/Windows/Fonts' if os.name == 'nt' else '/mnt/c/Windows/Fonts'))
    metrics = {}
    for style, filename in [('regular', 'times.ttf'), ('bold', 'timesbd.ttf')]:
        font = ImageFont.truetype(str(directory / filename), 1000)
        metrics[style] = {'units': 1000, 'widths': {
            chr(c): font.getlength(chr(c)) for c in list(range(32, 128)) + [8230]}}
    BUILD.mkdir(parents=True, exist_ok=True)
    (BUILD / 'font-metrics.json').write_text(json.dumps(metrics), encoding='utf8')


def tag(prefix, name):
    return f'{{{NS[prefix]}}}{name}'


def group_pptx():
    manifest = json.loads((BUILD / 'shape-groups.json').read_text(encoding='utf8'))
    groups = {item['name']: item['groups'] for item in manifest['records']}
    candidate = BUILD / 'candidate.pptx'
    with zipfile.ZipFile(candidate) as source:
        root = E.fromstring(source.read('ppt/slides/slide1.xml'))
        tree = root.find('p:cSld/p:spTree', NS)
        shapes = list(tree.findall('p:sp', NS))
        assert len(shapes) == len(groups), (len(shapes), len(groups))
        next_id = max(int(e.get('id')) for e in root.findall('.//p:cNvPr', NS)) + 1
        current = []
        stack = [tree]
        group_count = 0
        for shape in shapes:
            name = shape.find('p:nvSpPr/p:cNvPr', NS).get('name')
            desired = groups[name]
            common = 0
            while common < min(len(current), len(desired)) and current[common] == desired[common]:
                common += 1
            stack = stack[:common+1]
            current = current[:common]
            for name in desired[common:]:
                group = E.SubElement(stack[-1], tag('p', 'grpSp'))
                nv = E.SubElement(group, tag('p', 'nvGrpSpPr'))
                E.SubElement(nv, tag('p', 'cNvPr'), id=str(next_id), name=name)
                next_id += 1
                E.SubElement(nv, tag('p', 'cNvGrpSpPr'))
                E.SubElement(nv, tag('p', 'nvPr'))
                E.SubElement(group, tag('p', 'grpSpPr'))
                stack.append(group)
                current.append(name)
                group_count += 1
            # The authoring runtime emits noGrp on native shapes; remove it so
            # PowerPoint supports regrouping and editing each vector component.
            for locks in shape.findall('.//a:spLocks', NS):
                locks.attrib.pop('noGrp', None)
            tree.remove(shape)
            stack[-1].append(shape)

        def bounds(element):
            if element.tag == tag('p', 'sp'):
                xf = element.find('p:spPr/a:xfrm', NS)
                off, ext = xf.find('a:off', NS), xf.find('a:ext', NS)
                x, y = int(off.get('x')), int(off.get('y'))
                return x, y, x + int(ext.get('cx')), y + int(ext.get('cy'))
            children = [bounds(c) for c in element if c.tag in (tag('p', 'sp'), tag('p', 'grpSp'))]
            x, y = min(c[0] for c in children), min(c[1] for c in children)
            right, bottom = max(c[2] for c in children), max(c[3] for c in children)
            if element.tag == tag('p', 'grpSp'):
                xf = E.SubElement(element.find('p:grpSpPr', NS), tag('a', 'xfrm'))
                E.SubElement(xf, tag('a', 'off'), x=str(x), y=str(y))
                E.SubElement(xf, tag('a', 'ext'), cx=str(right-x), cy=str(bottom-y))
                E.SubElement(xf, tag('a', 'chOff'), x=str(x), y=str(y))
                E.SubElement(xf, tag('a', 'chExt'), cx=str(right-x), cy=str(bottom-y))
            return x, y, right, bottom
        bounds(tree)
        output = BUILD / 'grouped-candidate.pptx'
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as result:
            for item in source.infolist():
                content = E.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True) if item.filename == 'ppt/slides/slide1.xml' else source.read(item.filename)
                result.writestr(item, content)
        fonts = {r.get('typeface') for r in root.findall('.//a:latin', NS)}
        assert fonts == {'Times New Roman'}, fonts
        assert not root.findall('.//p:pic', NS)
        assert not any(n.startswith('ppt/media/') for n in source.namelist())
        assert len(root.findall('.//p:sp', NS)) == len(shapes)
        report = {'native_shapes': len(shapes), 'editable_text_boxes': len(root.findall('.//p:txBody', NS)),
                  'native_groups': group_count, 'raster_images': 0, 'fonts': sorted(fonts)}
        (BUILD / 'editability-check.json').write_text(json.dumps(report, indent=2))
        print(json.dumps(report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare-fonts', action='store_true')
    args = parser.parse_args()
    prepare_fonts() if args.prepare_fonts else group_pptx()

