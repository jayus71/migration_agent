from pathlib import Path
import os, sys, json, hashlib, subprocess
import numpy as np
import pymupdf as fitz
ROOT=Path.cwd(); OUT=ROOT/'output/manuscript-review-20260925-r2'; OUT.mkdir(parents=True,exist_ok=True)
tracked=subprocess.check_output(['git','ls-files','-z']).decode().split(chr(0))
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
protected={p:sha(ROOT/p) for p in tracked if p and (p.startswith(('sections/','figures/','data/')) or p.startswith('conference_101719') or p.endswith(('.sty','.bst')))}
source=ROOT/'figures/架构图0925加粗版.svg'; protected[str(source.relative_to(ROOT))]=sha(source)
(OUT/'protected-before.json').write_text(json.dumps(protected,ensure_ascii=False,indent=2))
sys.path.insert(0,str(ROOT/'figures'))
from make_unified_results import build_figure, load_data
from paper_plot_style import plt
conf=OUT/'fontconfig.conf'; conf.write_text('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig><include ignore_missing="yes">/etc/fonts/fonts.conf</include><dir>/mnt/c/Windows/Fonts</dir></fontconfig>')
env=dict(os.environ,FONTCONFIG_FILE=str(conf))

subprocess.run(['inkscape',str(source),'--export-type=pdf','--export-filename='+str(OUT/'architecture-0925-vector.pdf')],env=env,check=True,capture_output=True)
arch=fitz.open(OUT/'architecture-0925-vector.pdf')
spans=[s for b in arch[0].get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans'] if s['text'].strip()]
review=fitz.open(); p=review.new_page(width=612,height=792)
p.insert_text((108,60),'Revised figure trial: bold architecture and compact task numbers',fontsize=12,fontname='tibo')
scales=[]
for scale,top in [(.9,103),(.95,390)]:
 w=396*scale; h=w*arch[0].rect.height/arch[0].rect.width
 rect=fitz.Rect((612-w)/2,top,(612+w)/2,top+h)
 p.insert_text((108,top-13),f'Architecture: {int(scale*100)}% width, {w*25.4/72:.1f} x {h*25.4/72:.1f} mm',fontsize=10,fontname='tiro')
 p.show_pdf_page(rect,arch,0)
 p.get_pixmap(dpi=120,clip=fitz.Rect(102,top-25,510,top+h+5),alpha=False).save(OUT/f'architecture-{int(scale*100)}percent.png')
 scales.append({'scale':scale,'width_mm':w*25.4/72,'height_mm':h*25.4/72,'min_font_pt':min(s['size'] for s in spans)*w/arch[0].rect.width})
p.get_pixmap(dpi=120,alpha=False).save(OUT/'architecture-comparison.png')
data=load_data(); ordered=[]
for state in (True,False):
 ordered.extend(sorted((v for v in data['paired_costs'] if v['initially_accepted']==state),key=lambda v:v['matchfix_tokens']-v['ladim_tokens']))
expected=np.array([v['matchfix_tokens']-v['ladim_tokens'] for v in ordered]); assert len(expected)==29 and (expected<0).sum()==2 and expected.sum()==6938291
layouts=[]
for variant in ['horizontal','vertical']:
 fig=build_figure(); a,b=fig.axes; fig.set_size_inches(5.5,1.85)
 a.set_position([.145,.24,.245,.59]); b.set_position([.45,.24,.535,.59])
 a.set_ylim(2.55,-1.9); a.set_xlim(0,27)
 legend=a.get_legend(); legend.set_bbox_to_anchor((1.13,1.04))
 for t in legend.get_texts(): t.set_fontsize(6.8)
 a.tick_params(axis='y',labelsize=7)
 a.set_title('(a) Total tokens',loc='left',fontsize=8,pad=5)
 for t in a.texts: t.set_fontsize(7)
 for patch in b.patches: patch.set_height(patch.get_height()/1000)
 assert np.allclose([patch.get_height()*1e6 for patch in b.patches],expected)
 b.set(xlim=(-.6,28.6),ylim=(-.2,1.4),yticks=[0,.5,1],ylabel='',xlabel='')
 b.set_title('(b) Tokens saved (millions)',loc='left',fontsize=8,pad=5)
 b.set_xticks(range(29),[str(i) for i in range(1,30)],rotation=0 if variant=='horizontal' else 90,fontsize=6.5)
 for ax in (a,b):
  ax.xaxis.label.set_fontsize(7); ax.yaxis.label.set_fontsize(7); ax.tick_params(axis='y',pad=2); ax.tick_params(axis='x',pad=2)
 for t in b.get_legend().get_texts(): t.set_fontsize(7)
 b.text(-.035,-.05,'Task',transform=b.transAxes,ha='right',va='top',fontsize=7)
 fig.canvas.draw(); renderer=fig.canvas.get_renderer()
 boxes=[t.get_window_extent(renderer) for t in b.get_xticklabels()]
 overlaps=[(i+1,j+1) for i,x in enumerate(boxes) for j,y in enumerate(boxes) if j>i and x.overlaps(y)]
 clipped=[i+1 for i,x in enumerate(boxes) if not fig.bbox.contains(x.x0,x.y0) or not fig.bbox.contains(x.x1,x.y1)]
 assert not overlaps and not clipped,(overlaps,clipped)
 fig.savefig(OUT/f'figure3-{variant}.pdf')
 fig.savefig(OUT/f'figure3-{variant}.png',dpi=160)
 layouts.append({'variant':variant,'overlap_pairs':overlaps,'clipped_labels':clipped,'height_mm':1.85*.96*25.4,'width_mm':5.5*.96*25.4,'number_font_pt':6.5*.96,'minimum_tick_gap_pt':min(boxes[i+1].x0-boxes[i].x1 for i in range(28))*72/fig.dpi*.96})
 plt.close(fig)
page=review.new_page(width=612,height=792)
page.insert_text((108,62),'Figure 3: one Task label and all 29 numbers, side by side',fontsize=12,fontname='tibo')
for variant,top in [('horizontal',120),('vertical',330)]:
 d=fitz.open(OUT/f'figure3-{variant}.pdf'); w=380.16; h=d[0].rect.height*w/d[0].rect.width
 page.insert_text((108,top-15),variant+' numbers',fontsize=10,fontname='tiro')
 page.show_pdf_page(fitz.Rect((612-w)/2,top,(612+w)/2,top+h),d,0)
review.save(OUT/'figure-review-r2.pdf',deflate=True,garbage=4)
page.get_pixmap(dpi=120,alpha=False).save(OUT/'figure3-comparison.png')
summary={'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'fonts':sorted(set(s['font'] for s in spans)),'nonbold_spans':[(s['text'],s['font']) for s in spans if 'Bold' not in s['font']],'architecture_scales':scales,'figure3':layouts}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False,indent=2))

selected=fitz.open(); q=selected.new_page(width=612,height=650)
q.insert_text((108,48),'Selected review layouts: September 25 revision',fontsize=13,fontname='tibo')
w=396*.9; h=w*arch[0].rect.height/arch[0].rect.width
q.insert_text((108,75),'Bold architecture: 90% text width (125.7 x 76.2 mm)',fontsize=10,fontname='tiro')
q.show_pdf_page(fitz.Rect((612-w)/2,87,(612+w)/2,87+h),arch,0)
chart=fitz.open(OUT/'figure3-horizontal.pdf'); w=380.16; h=chart[0].rect.height*w/chart[0].rect.width
q.insert_text((108,340),'Figure 3: side-by-side panels, one Task label, numbers 1-29',fontsize=10,fontname='tiro')
q.show_pdf_page(fitz.Rect((612-w)/2,355,(612+w)/2,355+h),chart,0)
q.insert_text((108,510),'Figure 3 height: 45.1 mm; currently included figure: 44.2 mm.',fontsize=9,fontname='tiro')
q.insert_text((108,525),'Review assets only. The formal manuscript has not been changed.',fontsize=9,fontname='tiro')
selected.save(OUT/'selected-layouts.pdf',garbage=4,deflate=True)
q.get_pixmap(dpi=120,alpha=False).save(OUT/'selected-layouts.png')
assert not [p for p,h in protected.items() if sha(ROOT/p)!=h]
