#!/usr/bin/env python3
"""Isolated manuscript review trials; never exports official paper assets."""
from pathlib import Path
import hashlib, json, os, subprocess, sys
import numpy as np
import pandas as pd
import pymupdf as fitz
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/manuscript-review-20260925'
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / 'figures'))
from make_unified_results import load_data, build_figure
from paper_data import GRADIENT_STEPS, THRESHOLDS
from paper_plot_style import BLUE, GREEN, GRAY, ORANGE, plt
from matplotlib.patches import Patch
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split(chr(0))
protected = {p: digest(ROOT/p) for p in tracked if p and (p.startswith(('sections/', 'tables/', 'figures/', 'data/', 'literature/')) or p.startswith('conference_101719') or p.endswith(('.sty', '.bst')))}
protected['figures/架构图0924.svg'] = digest(ROOT/'figures/架构图0924.svg')
(OUT/'protected-before.json').write_text(json.dumps(protected, indent=2, ensure_ascii=False)+'\n')
fontconf = OUT/'fontconfig.conf'
fontconf.write_text('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig><include ignore_missing="yes">/etc/fonts/fonts.conf</include><dir>/mnt/c/Windows/Fonts</dir></fontconfig>')
env = dict(os.environ, FONTCONFIG_FILE=str(fontconf))
subprocess.run(['inkscape', str(ROOT/'figures/架构图0924.svg'), '--export-type=pdf', '--export-filename='+str(OUT/'architecture-0924-vector.pdf')], env=env, check=True, capture_output=True)
arch = fitz.open(OUT/'architecture-0924-vector.pdf')
spans = [s for b in arch[0].get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans'] if s['text'].strip()]
fonts = sorted(set(s['font'] for s in spans))
assert all('TimesNewRoman' in f for f in fonts), fonts
assert not arch[0].get_images(full=True)
WIDTH = 396.0
MIN_FONT = min(s['size'] for s in spans)
def text(page, x, y, value, size=10, bold=False):
    page.insert_text((x,y), value, fontsize=size, fontname='tibo' if bold else 'tiro', color=(.12,.14,.18))
def preview(page, name, dpi=144):
    page.get_pixmap(dpi=dpi, alpha=False).save(OUT/name)
def place_arch(page, scale, top):
    w=WIDTH*scale; h=w*arch[0].rect.height/arch[0].rect.width
    text(page,108,top-20,f'{int(scale*100)}% of text width: {w*25.4/72:.1f} x {h*25.4/72:.1f} mm; smallest text {MIN_FONT*w/arch[0].rect.width:.2f} pt',9,True)
    page.show_pdf_page(fitz.Rect((612-w)/2,top,(612+w)/2,top+h), arch, 0)
    return h
review = fitz.open()
p=review.new_page(width=612,height=792)
text(p,108,57,'Architecture scaling trial - source SVG unchanged',13,True)
text(p,108,81,'Reference body text at 10 pt. Text width: 5.5 in (139.7 mm).')
text(p,108,96,'Judge the PDF at 100% zoom; screen image size depends on the viewer.')
place_arch(p,1,135)
place_arch(p,.90,430)
text(p,108,709,'100% height: 84.7 mm. 90% height: 76.2 mm. Height saved: 8.5 mm.',9)
preview(p,'architecture-100-vs-90.png')
for scale in (1,.95,.90):
    doc=fitz.open(); q=doc.new_page(width=612,height=792)
    text(q,108,64,'Architecture trial at manuscript text width',13,True)
    text(q,108,88,'Reference paragraph at the manuscript body size of 10 pt.')
    text(q,108,101,'The full diagram is placed below at its intended physical size.')
    h=place_arch(q,scale,143)
    text(q,108,143+h+24,'Trial only. The formal manuscript and included figure remain unchanged.',10)
    doc.save(OUT/f'architecture-{int(scale*100)}percent.pdf',garbage=4,deflate=True)
    preview(q,f'architecture-{int(scale*100)}percent.png')
    q.get_pixmap(dpi=96,clip=fitz.Rect(100,116,512,143+h+8),alpha=False).save(OUT/f'architecture-{int(scale*100)}percent-96dpi.png')
    doc.close()
data=load_data()
ordered=[]
for state in (True,False):
    ordered.extend(sorted((v for v in data['paired_costs'] if v['initially_accepted']==state),key=lambda v:v['matchfix_tokens']-v['ladim_tokens']))
assert len(ordered)==29 and sum(v['initially_accepted'] for v in ordered)==20
savings=np.array([v['matchfix_tokens']-v['ladim_tokens'] for v in ordered])
assert (savings<0).sum()==2 and savings.sum()==6938291
pd.DataFrame([{'display_label':f'Task {i+1}',**v,'savings_tokens':int(savings[i])} for i,v in enumerate(ordered)]).to_csv(OUT/'figure3-task-label-map.csv',index=False)
def labels(ax):
    ax.set_xticks(range(29),[f'Task {i+1}' for i in range(29)],rotation=90,fontsize=8)
    ax.set_xlabel('')
def axis_b(ax):
    ax.bar(np.arange(29),savings/1e6,width=.76,color=[GREEN if v>=0 else ORANGE for v in savings],zorder=3)
    ax.axhline(0,color=GRAY,linewidth=.7,zorder=4)
    ax.axvline(19.5,color=GRAY,linestyle=(0,(2,3)),linewidth=.55)
    ax.set(xlim=(-1,29),ylim=(-.20,1.4),ylabel='Tokens saved by LaDiM\n(millions)',yticks=[0,.25,.5,.75,1,1.25])
    ax.set_title('(b) Savings on each input',loc='left',fontsize=9,pad=8)
    ax.legend(handles=[Patch(facecolor=GREEN,label='Fewer tokens'),Patch(facecolor=ORANGE,label='More tokens')],loc='upper left',frameon=False,fontsize=8,handlelength=.85,labelspacing=.2)
    ax.grid(axis='y',color='#E9ECEF',linewidth=.45)
    labels(ax)
layout=[]
def save_trial(fig,name,ax):
    fig.canvas.draw(); renderer=fig.canvas.get_renderer()
    boxes=[t.get_window_extent(renderer) for t in ax.get_xticklabels()]
    overlaps=[(i+1,j+1) for i,a in enumerate(boxes) for j,b in enumerate(boxes) if j>i and a.overlaps(b)]
    clip=[i+1 for i,b in enumerate(boxes) if not fig.bbox.contains(b.x0,b.y0) or not fig.bbox.contains(b.x1,b.y1)]
    fig.savefig(OUT/(name+'.pdf'))
    width,height=fig.get_size_inches()*72*.96
    layout.append({'variant':name,'printed_width_pt':width,'printed_height_pt':height,'task_font_pt':8*.96,'label_overlap_pairs':overlaps,'clipped_task_labels':clip,'b_axis_width_pt':ax.get_window_extent(renderer).width/fig.dpi*72*.96})
    plt.close(fig)
fig=build_figure(); b=fig.axes[1]
for patch in b.patches: patch.set_height(patch.get_height()/1000)
b.set(ylim=(-.2,1.4),yticks=[0,.25,.5,.75,1,1.25],ylabel='Tokens saved by LaDiM\n(millions)')
labels(b); fig.subplots_adjust(bottom=.28)
save_trial(fig,'figure3-side-by-side',b)
fig=plt.figure(figsize=(5.5,3.0))
a=fig.add_axes([.185,.68,.77,.23]); b=fig.add_axes([.12,.21,.865,.32])
colors=['#E2E6E9','#7BB2C9',BLUE]
for y,method in enumerate(('ladim','matchfix','swe')):
    left=0
    for key,color in zip(('translation','initially_accepted','initially_faulty'),colors):
        v=data['cost_stages'][method][key]/1e6
        a.barh(y,v,left=left,height=.43,color=color,edgecolor='white',linewidth=.4); left+=v
    a.text(left+.35,y,f'{left:.3f}',va='center',fontsize=8)
a.set(yticks=range(3),yticklabels=['LaDiM','MatchFixAgent','SWE-agent'],xlim=(0,24),ylim=(2.55,-.7),xlabel='Total tokens (millions)',xticks=[0,5,10,15,20])
a.set_title('(a) Total tokens',loc='left',fontsize=9,pad=6)
a.grid(axis='x',color='#E9ECEF',linewidth=.45)
a.legend(handles=[Patch(facecolor=c,label=l) for c,l in zip(colors,['Initial translation','Passes before repair','Needs repair'])],loc='upper right',bbox_to_anchor=(1.05,1.03),fontsize=7,frameon=False,handlelength=.8,labelspacing=.05)
axis_b(b)
for ax in (a,b):
    ax.set_axisbelow(True); ax.tick_params(labelsize=8,length=2,color='#92989E')
    for side in ('left','bottom'): ax.spines[side].set_color('#B3BAC0')
b.text(9.5,-.53,'Passes before repair',ha='center',fontsize=8,transform=b.get_xaxis_transform())
b.text(24,-.53,'Needs repair',ha='center',fontsize=8,transform=b.get_xaxis_transform())
save_trial(fig,'figure3-stacked',b)

from matplotlib.transforms import ScaledTranslation
fig=build_figure(); fig.set_size_inches(5.5,2.7); b=fig.axes[1]
for patch in b.patches: patch.set_height(patch.get_height()/1000)
b.set(ylim=(-.2,1.4),yticks=[0,.25,.5,.75,1,1.25])
b.set_ylabel('Tokens saved by LaDiM'+chr(10)+'(millions)')
labels(b); fig.subplots_adjust(bottom=.40,top=.85)
for i,label in enumerate(b.get_xticklabels()):
    if i%2:
        label.set_transform(label.get_transform()+ScaledTranslation(0,-31/72,fig.dpi_scale_trans))
        height=b.get_position().height*fig.get_size_inches()[1]*72
        b.plot([i,i],[0,-31/height],transform=b.get_xaxis_transform(),clip_on=False,color='#B3BAC0',linewidth=.35,zorder=0)
save_trial(fig,'figure3-staggered',b)

p=review.new_page(width=612,height=792)
text(p,108,57,'Figure 3: all 29 task labels at the manuscript width',13,True)
text(p,108,82,'All trials: 96% of text width (134.1 mm); task labels: 7.68 pt.',10)
y=100
for name,title in [('figure3-side-by-side','A. Current side-by-side layout + all task labels'),('figure3-staggered','B. Current panel widths + two alternating label rows'),('figure3-stacked','C. Wider panel (b), stacked beneath panel (a)')]:
    text(p,108,y,title,10,True); y+=15
    doc=fitz.open(OUT/(name+'.pdf')); w=WIDTH*.96; h=doc[0].rect.height*w/doc[0].rect.width
    p.show_pdf_page(fitz.Rect((612-w)/2,y,(612+w)/2,y+h),doc,0)
    p.get_pixmap(dpi=144,clip=fitz.Rect(100,y-29,512,y+h+6),alpha=False).save(OUT/(name+'-manuscript.png'))
    y+=h+22
text(p,108,y,'Bar order, both negative values, and all costs are unchanged.',10)
text(p,108,y+15,'Tasks 1-20: passes before repair. Tasks 21-29: needs repair.',10)
preview(p,'figure3-label-comparison.png')
frame=pd.read_csv(GRADIENT_STEPS)
free=frame[frame.coupling.eq('free-running')].copy()
assert len(free)==1800 and free[['torch_status','torch4ms_status']].eq('ok').all().all()
assert not free.duplicated(['fault','model','seed','step']).any()
assert free.groupby(['fault','model','seed']).step.apply(lambda s:set(s)==set(range(1,51))).all()
assert np.isfinite(free[list(THRESHOLDS)]).all().all()
healthy=free[free.fault.eq('none')]
thresholds=[.02,.01,.005,.001,.0001,.00001,.000005,.000004,.000003,.000002,.000001,0.]
rows=[]; detections=[]
for threshold in thresholds:
    for fault in ['none','grad_wrong','param_wrong']:
        subset=free[free.fault.eq(fault)]
        first=subset[subset.loss_abs_diff.gt(threshold)].groupby(['model','seed']).step.min()
        mean=subset.groupby('step').loss_abs_diff.mean(); crossings=mean[mean.gt(threshold)]
        rows.append({'threshold':threshold,'fault':fault,'runs':12,'detected_within_50':len(first),'not_detected_within_50':12-len(first),'first_step_min_detected_only':int(first.min()) if len(first) else None,'first_step_median_detected_only':float(first.median()) if len(first) else None,'first_step_max_detected_only':int(first.max()) if len(first) else None,'mean_curve_first_crossing':int(crossings.index.min()) if len(crossings) else None,'step_crossings':int(subset.loss_abs_diff.gt(threshold).sum()),'steps':len(subset)})
        for (model,seed),run in subset.groupby(['model','seed']):
            detected=run[run.loss_abs_diff.gt(threshold)].step
            detections.append({'threshold':threshold,'fault':fault,'model':model,'seed':int(seed),'first_detection_step':int(detected.min()) if len(detected) else None,'censor_step':50})
result=pd.DataFrame(rows); result.to_csv(OUT/'loss-threshold-sensitivity.csv',index=False,na_rep='n/a')
pd.DataFrame(detections).to_csv(OUT/'loss-first-detection-by-run.csv',index=False,na_rep='n/a')
step1=free[free.step.eq(1)].pivot(index=['model','seed'],columns='fault',values='loss_abs_diff')
assert (step1['none']==step1['grad_wrong']).all() and (step1['none']==step1['param_wrong']).all()
step1.to_csv(OUT/'step1-matched-loss-differences.csv')
reference=free.pivot(index=['model','seed','step'],columns='fault',values='torch_loss')
assert (reference['none']==reference['grad_wrong']).all() and (reference['none']==reference['param_wrong']).all()
direct={}
for fault,metric in [('grad_wrong','grad_norm_abs_diff'),('param_wrong','param_update_rel_l2')]:
    subset=free[free.fault.eq(fault)]
    first=subset[subset[metric].gt(THRESHOLDS[metric])].groupby(['model','seed']).step.min()
    assert len(first)==12 and first.eq(1).all()
    direct[fault]={'metric':metric,'threshold':THRESHOLDS[metric],'first_detection_step_all_runs':1,'detected':len(first),'healthy_runs_flagged':int(healthy.groupby(['model','seed'])[metric].max().gt(THRESHOLDS[metric]).sum())}
fig,axes=plt.subplots(1,2,figsize=(7.2,2.5))
for ax in axes:
    ax.set_xscale('log'); ax.set_xlabel('Absolute loss difference threshold'); ax.grid(color='#e8e8e8',linewidth=.5)
for fault,color,label in [('grad_wrong',ORANGE,'Incorrect gradients'),('param_wrong',GREEN,'Incorrect parameter updates')]:
    d=result[(result.fault==fault)&(result.threshold>0)].sort_values('threshold')
    axes[0].plot(d.threshold,d.mean_curve_first_crossing,marker='o',color=color,label=label,markersize=3)
    axes[1].plot(d.threshold,d.detected_within_50,marker='o',color=color,label=label,markersize=3)
d=result[(result.fault=='none')&(result.threshold>0)].sort_values('threshold')
axes[1].plot(d.threshold,d.detected_within_50,marker='x',color=GRAY,label='Healthy runs flagged',markersize=4)
axes[0].set(ylabel='First crossing of mean curve',ylim=(0,33)); axes[1].set(ylabel='Runs flagged within 50 steps',ylim=(-.3,12.7),yticks=[0,3,6,9,12])
axes[0].set_title('(a) Mean loss crossing',loc='left',fontsize=10); axes[1].set_title('(b) Fault detection and healthy controls',loc='left',fontsize=10)
for ax in axes: ax.axvline(.02,color=GRAY,linestyle=':',linewidth=.8)
axes[1].legend(frameon=False,fontsize=7,loc='center right')
fig.subplots_adjust(left=.085,right=.98,bottom=.24,top=.85,wspace=.35)
fig.savefig(OUT/'threshold-sensitivity.pdf'); fig.savefig(OUT/'threshold-sensitivity.png',dpi=160); plt.close(fig)
review.save(OUT/'figure-review-20260925.pdf',garbage=4,deflate=True)
changed=[p for p,h in protected.items() if digest(ROOT/p)!=h]
assert not changed,changed
summary={'checkpoint':subprocess.check_output(['git','rev-parse','--short','HEAD'],cwd=ROOT).decode().strip(),'architecture_fonts':fonts,'architecture_scales':[{'scale':s,'width_mm':WIDTH*s*25.4/72,'height_mm':WIDTH*s*arch[0].rect.height/arch[0].rect.width*25.4/72,'smallest_text_pt':MIN_FONT*WIDTH*s/arch[0].rect.width} for s in (1,.95,.90)],'old_figure_height_mm':WIDTH*375/840*25.4/72,'current_figure3_height_mm':fitz.open(ROOT/'figures/repair_comparison.pdf')[0].rect.height*380.16/fitz.open(ROOT/'figures/repair_comparison.pdf')[0].rect.width*25.4/72,'figure3_layouts':layout,'paired_inputs':len(ordered),'negative_bars':int((savings<0).sum()),'total_savings_tokens':int(savings.sum()),'healthy_max_loss_abs_diff':float(healthy.loss_abs_diff.max()),'same_step1_loss_for_healthy_and_faulty':True,'reference_loss_matched_across_conditions':True,'direct_checks':direct,'protected_files':len(protected),'protected_files_changed':changed,'threshold_source':str(GRADIENT_STEPS.relative_to(ROOT)),'threshold_source_sha256':digest(GRADIENT_STEPS)}
(OUT/'review-summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(summary,indent=2,ensure_ascii=False))
