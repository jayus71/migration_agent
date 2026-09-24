"""Convert supplied logo SVG paths to editable polygon paths (no raster tracing)."""
import json
import math
import re
from pathlib import Path
from lxml import etree as E
from fontTools.pens.basePen import BasePen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform
from fontTools.svgLib.path import parse_path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tmp/method-latest-20260924'
OUT.mkdir(parents=True, exist_ok=True)

class FlatPen(BasePen):
    def __init__(self):
        super().__init__(None)
        self.commands = []
    def _moveTo(self, p): self.commands.append({'moveTo':dict(zip(('x','y'),p))})
    def _lineTo(self, p): self.commands.append({'lineTo':dict(zip(('x','y'),p))})
    def _closePath(self): self.commands.append({'close':{}})
    def _endPath(self): pass
    def _curveToOne(self, p1, p2, p3):
        p0 = self._getCurrentPoint()
        length = sum(math.dist(a,b) for a,b in zip([p0,p1,p2],[p1,p2,p3]))
        n = max(8, min(120, math.ceil(length / .6)))
        for i in range(1,n+1):
            t=i/n; u=1-t
            self._lineTo(tuple(u**3*p0[k]+3*u*u*t*p1[k]+3*u*t*t*p2[k]+t**3*p3[k] for k in (0,1)))

def matrix(value):
    t = Transform()
    for name, raw in re.findall(r'(\w+)\(([^)]+)\)', value or ''):
        vals = list(map(float,re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?',raw)))
        if name == 'matrix': op=Transform(*vals)
        elif name == 'translate': op=Transform().translate(vals[0],vals[1] if len(vals)>1 else 0)
        elif name == 'scale': op=Transform().scale(vals[0],vals[1] if len(vals)>1 else vals[0])
        else: raise ValueError(name)
        t=t.transform(op)
    return t

result={}
for name in ['python','torch','java','mindspore','jax']:
    src=ROOT / 'figures/icons' / f'{name}.svg'
    if not src.exists():
        src=ROOT / 'figures/editable-method-latest-20260924/source-icons' / f'{name}.svg'
    tree=E.parse(str(src)); root=tree.getroot()
    gradients={}
    for grad in root.findall('.//{*}linearGradient'):
        stops=grad.findall('{*}stop')
        gradients[grad.get('id')]=stops[len(stops)//2].get('stop-color')
    paths=[]
    for el in root.findall('.//{*}path'):
        transform=Transform()
        for parent in list(el.iterancestors())[::-1]+[el]:
            transform=transform.transform(matrix(parent.get('transform')))
        pen=FlatPen(); parse_path(el.get('d'),TransformPen(pen,transform))
        fill=el.get('fill','#000000')
        if fill.startswith('url('): fill=gradients[fill[5:-1]]
        paths.append({'commands':pen.commands,'fill':fill})
    coords=[v for p in paths for c in p['commands'] for k,v in c.items() if k!='close']
    x=min(p['x'] for p in coords); y=min(p['y'] for p in coords)
    w=max(p['x'] for p in coords)-x; h=max(p['y'] for p in coords)-y
    for p in paths:
        for c in p['commands']:
            for k,v in c.items():
                if k!='close': v['x']-=x; v['y']-=y
    result[name]={'width':w,'height':h,'paths':paths}
(OUT/'logo-paths.json').write_text(json.dumps(result))
print({name:len(v['paths']) for name,v in result.items()})
