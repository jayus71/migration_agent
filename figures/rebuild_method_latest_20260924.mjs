/** Rebuild the user-supplied 2026-09-24 method image as native PPT objects.
 * Both SVG and PPTX are generated from the same geometry. No raster tracing.
 * Requires the bundled @oai/artifact-tool (RUNTIME_NODE_MODULES).
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { spawnSync } from 'node:child_process';
const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const build = path.join(root, 'tmp/method-latest-20260924');
const out = path.join(root, 'figures/editable-method-latest-20260924');
await fs.mkdir(build, { recursive: true });
await fs.mkdir(path.join(out, 'icons'), { recursive: true });
const runtime = path.join(process.env.RUNTIME_NODE_MODULES, '@oai/artifact-tool/dist/artifact_tool.mjs');
const { Presentation, PresentationFile } = await import(pathToFileURL(runtime).href);
const W = 1672, H = 941, FONT = 'Times New Roman';
const preparation=spawnSync(process.env.RUNTIME_PYTHON??'python3',[path.join(root,'scripts/finalize_method_latest_20260924.py'),'--prepare-fonts'],{encoding:'utf8'});
if(preparation.status!==0)throw new Error(preparation.stderr||'Font preparation failed');
const fontMetrics = JSON.parse(await fs.readFile(path.join(build, 'font-metrics.json'), 'utf8'));
const ppt = Presentation.create({slideSize:{width:W,height:H}});
const slide = ppt.slides.add();
slide.background.fill = '#FFFFFF';
const C = { ink:'#071A47', blue:'#003496', line:'#273247', pale:'#F7F9FC', grey:'#71869C', green:'#159F50' };
let svg=[], defs=[], serial=0, group=[], records=[], iconFiles=new Map();
const esc = s => String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
function save(shape, label) { records.push({name:shape.name, groups:[...group], label});return shape; }
function groupWith(name, fn) {group.push(name);svg.push(`<g id="${esc(name)}">`);fn();svg.push('</g>');group.pop();}
function gradient(a,b,angle=90) {return {type:'gradient',gradientKind:'linear',angleDeg:angle,stops:[{offset:0,color:a},{offset:100000,color:b}]};}
function svgFill(fill) {
 if (typeof fill==='string') return fill;
 const id='gradient-'+defs.length;
 const a=(fill.angleDeg??90)*Math.PI/180;
 defs.push(`<linearGradient id="${id}" x1="${50-50*Math.cos(a)}%" y1="${50-50*Math.sin(a)}%" x2="${50+50*Math.cos(a)}%" y2="${50+50*Math.sin(a)}%">${fill.stops.map(s=>`<stop offset="${s.offset/1000}%" stop-color="${s.color}"/>`).join('')}</linearGradient>`);
 return `url(#${id})`;
}
function shape(kind,x,y,w,h,fill='none',stroke='none',sw=0,r=0,label='') {
 const name=`${++serial} ${label||kind}`;
 const s=slide.shapes.add({geometry:kind==='ellipse'?'ellipse':(r?'roundRect':'rect'),name,position:{left:x,top:y,width:w,height:h},fill,line:{fill:stroke,width:sw},...(r?{borderRadius:r}:{})});
 save(s,label);
 svg.push(kind==='ellipse'?`<ellipse cx="${x+w/2}" cy="${y+h/2}" rx="${w/2}" ry="${h/2}" fill="${svgFill(fill)}" stroke="${stroke}" stroke-width="${sw}"/>`:`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${svgFill(fill)}" stroke="${stroke}" stroke-width="${sw}"/>`);
 return s;
}
const box=(x,y,w,h,fill,stroke,sw=1,r=10,label='')=>shape('rect',x,y,w,h,fill,stroke,sw,r,label);
const ellipse=(x,y,w,h,fill,stroke='none',sw=0,label='')=>shape('ellipse',x,y,w,h,fill,stroke,sw,0,label);
function poly(points,stroke=C.ink,sw=2,fill='none',closed=false,label='path') {
 const xs=points.map(p=>p[0]),ys=points.map(p=>p[1]);
 let x=Math.min(...xs),y=Math.min(...ys),w=Math.max(...xs)-x,h=Math.max(...ys)-y;
 if(w<.01)w=.01;if(h<.01)h=.01;
 const commands=points.map((p,i)=>({[i?'lineTo':'moveTo']:{x:p[0]-x,y:p[1]-y}}));
 if(closed)commands.push({close:{}});
 const s=slide.shapes.add({geometry:'custom',name:`${++serial} ${label}`,position:{left:x,top:y,width:w,height:h},fill,line:{fill:stroke,width:sw},customPaths:[{width:w,height:h,commands}]});save(s,label);
 svg.push(`<${closed?'polygon':'polyline'} points="${points.map(p=>p.join(',')).join(' ')}" fill="${svgFill(fill)}" stroke="${stroke}" stroke-width="${sw}" stroke-linejoin="round" stroke-linecap="round"/>`);
 return s;
}
const ln=(x1,y1,x2,y2,color=C.ink,sw=2)=>poly([[x1,y1],[x2,y2]],color,sw);
function text(value,x,y,w,size=21,bold=false,align='left',color=C.ink,h=null) {
 const lines=String(value).split('\n');
 const fm=fontMetrics[bold?'bold':'regular'];
 const measured=Math.max(...lines.map(t=>Array.from(t).reduce((a,c)=>a+(fm.widths[c]??fm.units*.7),0)/fm.units));
 size=Math.min(size,Math.floor(w*.972/Math.max(measured,.001)*10)/10);
 const lh=size*1.1;
 for(let i=0;i<lines.length;i++){
  const top=y+i*lh, hh=h??size*1.24;
  const s=slide.shapes.add({geometry:'textbox',name:`${++serial} ${lines[i]}`,position:{left:x,top,width:w,height:hh},fill:'none',line:{fill:'none',width:0}});
  s.text=lines[i];s.text.style={typeface:FONT,fontSize:size,bold,color,alignment:align,verticalAlignment:'middle',autoFit:'none',wrap:'none',insets:{left:0,right:0,top:0,bottom:0}};save(s,lines[i]);
  const xx=align==='center'?x+w/2:align==='right'?x+w:x;
  svg.push(`<text xml:space="preserve" x="${xx}" y="${top+hh/2+size*.34}" font-family="Times New Roman" font-size="${size}" font-weight="${bold?'bold':'normal'}" text-anchor="${align==='center'?'middle':align==='right'?'end':'start'}" fill="${color}">${esc(lines[i])}</text>`);
 }
}
function arrow(points,color=C.line,sw=3,tip=11,start=false) {
 poly(points,color,sw);
 function head(p,q){const a=Math.atan2(p[1]-q[1],p[0]-q[0]),b=tip*.48;poly([p,[p[0]-tip*Math.cos(a)+b*Math.sin(a),p[1]-tip*Math.sin(a)-b*Math.cos(a)],[p[0]-tip*Math.cos(a)-b*Math.sin(a),p[1]-tip*Math.sin(a)+b*Math.cos(a)]],color,.5,color,true,'arrow head');}
 head(points.at(-1),points.at(-2));if(start)head(points[0],points[1]);
}
function cubic(p0,p1,p2,p3,n=30){return Array.from({length:n+1},(_,i)=>{let t=i/n,u=1-t;return[0,1].map(k=>u*u*u*p0[k]+3*u*u*t*p1[k]+3*u*t*t*p2[k]+t*t*t*p3[k]);});}
function blockArrow(x,y,w,h,fill,stroke,up=false) {
 const p=up?[[x+w*.3,y+h],[x+w*.7,y+h],[x+w*.7,y+h*.45],[x+w,y+h*.45],[x+w*.5,y],[x,y+h*.45],[x+w*.3,y+h*.45]]:[[x,y+h*.25],[x+w*.55,y+h*.25],[x+w*.55,y],[x+w,y+h*.5],[x+w*.55,y+h],[x+w*.55,y+h*.75],[x,y+h*.75]];
 poly(p,stroke,1.3,fill,true,'filled flow arrow');
}
function icon(type,x,y,w,h=w,accent='#6CC9FF') {
 const begin=svg.length;
 groupWith(`icon-${type}-${serial}`,()=>{
 const X=a=>x+w*a/40,Y=a=>y+h*a/40,S=Math.min(w,h)/40;
 const l=(a,b,c,d,col=C.blue,sw=2)=>ln(X(a),Y(b),X(c),Y(d),col,sw*S);
 const p=(pts,col=C.blue,sw=2,fill='none',close=false)=>poly(pts.map(([a,b])=>[X(a),Y(b)]),col,sw*S,fill,close);
 const e=(a,b,c,d,fill,stroke=C.blue,sw=2)=>ellipse(X(a),Y(b),w*c/40,h*d/40,fill,stroke,sw*S);
 const b=(a,bb,c,d,fill,stroke=C.blue,sw=2,r=3)=>box(X(a),Y(bb),w*c/40,h*d/40,fill,stroke,sw*S,r*S);
 if(type==='database'){
  b(5,8,30,26,gradient(accent,'#87ACDF'),C.ink,2.2,0);e(5,25,30,13,'#94B9E8',C.ink,2.2);
  b(6,17,28,14,gradient(accent,'#9DBDE5'),'none',0,0);
  for(const yy of [19,27])p(cubic([5,yy],[12,yy+6],[28,yy+6],[35,yy]).map(z=>z),C.ink,2);
  e(5,2,30,13,accent,C.ink,2.2);
 } else if(type==='folder'){
  p([[3,10],[15,10],[18,14],[37,14],[37,35],[3,35]],C.blue,2,'#D2ECFF',true);
  p([[4,17],[36,17],[36,35],[4,35]],C.blue,1.3,'#F7FCFF',true);
 } else if(type==='document'||type==='config'){
  const c=type==='config'?'#92302D':C.blue;
  p([[8,2],[25,2],[34,11],[34,38],[8,38]],c,2,'#F9FCFF',true);
  p([[25,2],[25,12],[34,12]],c,1.5);
  for(const yy of [18,23,28,33])l(13,yy,27,yy,c,1.5);
 } else if(type==='python'){
  p([[5,6],[22,6],[22,23],[13,23],[13,33],[2,33],[2,15],[5,15]],C.blue,1.8,'#4AAAE6',true);
  p([[19,13],[30,13],[30,3],[37,3],[37,25],[30,25],[30,37],[15,37],[15,22],[19,22]],C.blue,1.6,'#FFD936',true);
  e(9,10,2,2,'#FFFFFF','none',0);e(28,28,2,2,'#FFFFFF','none',0);
 } else if(type==='robot'){
  l(20,5,20,13,C.ink,2.3);e(17.5,1,5,5,'#FFFFFF',C.ink,1.8);
  b(0,20,5,11,accent,C.ink,2,2);b(35,20,5,11,accent,C.ink,2,2);
  b(5,12,30,25,gradient('#FFFFFF',accent),C.ink,2.2,7);
  b(10,18,20,12,'#15154A',C.ink,1,4);
  e(14,21,4,5,'#FFFFFF','none',0);e(23,21,4,5,'#FFFFFF','none',0);
 } else if(type==='check'){
  e(1,1,38,38,gradient('#27B35B','#0C974A'),'#198D48',.6);
  p([[10,20],[17,27],[29,12]],'#FFFFFF',4);
 } else if(type==='tick'){
  p([[6,21],[15,29],[32,9]],accent,4);
 } else if(type==='warning'){
  p([[20,3],[38,36],[2,36]],'#F82127',2.5,'#FFFFFF',true);l(20,13,20,25,'#FA171B',3);e(18.5,29,3,3,'#F71920','none',0);
 } else if(type==='error'){
  e(1,1,38,38,gradient('#FF3346','#E70020'),'#FFFFFF',1.3);l(20,10,20,24,'#FFFFFF',4);e(18,29,4,4,'#FFFFFF','none',0);
 } else if(type==='gear'){
  const pts=[];for(let i=0;i<48;i++){const a=2*Math.PI*i/48,r=[0,1,4,5].includes(i%6)?16:20;pts.push([20+r*Math.cos(a),20+r*Math.sin(a)]);}p(pts,'#4320A3',1,'#5734BE',true);e(13,13,14,14,'#FFFFFF','none',0);
 } else if(type==='flame'){
  p([[22,1],[18,11],[19,18],[12,13],[8,22],[9,29],[15,37],[27,37],[34,29],[33,20],[28,10],[28,20],[24,14]],'#F75709',1,'#FF650B',true);
  p([[20,20],[15,29],[17,35],[23,37],[28,32],[25,25],[24,30]],'#FFFFFF',.5,'#FFFFFF',true);
 } else if(type==='code'){
  p([[12,10],[3,20],[12,30]],C.ink,2.7);p([[28,10],[37,20],[28,30]],C.ink,2.7);l(23,5,17,35,C.ink,2.7);
 } else if(type==='play'){
  p([[9,3],[35,20],[9,37]],'#107437',2,'#42BA6D',true);
 } else if(type==='search'){
  e(2,2,25,25,'#F4FCFF',C.blue,2.5);l(23,24,37,38,C.blue,3.2);
 } else if(type==='bars'){
  b(3,24,7,14,'#6AADF6',C.blue,1.5,0);b(16,15,7,23,'#83C6FF',C.blue,1.5,0);b(29,3,7,35,'#B9E8FE',C.blue,1.5,0);
 } else if(type==='trace'){
  b(5,3,30,34,'#B8CADD',C.ink,1.8,2);p([[11,10],[17,16],[13,20],[23,28],[27,23],[31,31]],C.ink,1.6);
 } else if(type==='clock'){
  e(2,2,36,36,'#FFFFFF',C.blue,2.4);p([[20,7],[20,20],[29,25]],C.blue,2.3);
 } else if(type==='globe'){
  e(2,2,36,36,'#D5EEFC',C.blue,2);e(11,2,18,36,'none',C.blue,1.7);l(20,2,20,38,C.blue,1.5);l(2,20,38,20,C.blue,1.6);
  for(const yy of [10,30])p(cubic([6,yy],[15,yy+4],[25,yy+4],[34,yy]),C.blue,1.5);
 } else if(type==='code-page'){
  b(2,1,36,38,'#FFFFFF',C.ink,2,3);p([[13,12],[6,20],[13,28]],C.ink,2.6);p([[27,12],[34,20],[27,28]],C.ink,2.6);l(23,9,17,32,C.ink,2.4);
 } else if(type==='lightning'){
  p([[27,0],[5,24],[19,24],[13,40],[35,16],[22,16]],C.ink,2,'#DBEAFF',true);
 }
 });
 if(!iconFiles.has(type))iconFiles.set(type,{x,y,w,h,parts:svg.slice(begin).join('\n')});
}

// Preserve supplied SVG contours as native, individually editable vector paths.
const logos=JSON.parse(await fs.readFile(path.join(build,'logo-paths.json'),'utf8'));
function logo(type,x,y,w,h){
 const d=logos[type],scale=Math.min(w/d.width,h/d.height);
 const xx=x+(w-d.width*scale)/2,yy=y+(h-d.height*scale)/2,begin=svg.length;
 groupWith(`icon-${type}-${serial}`,()=>{
  for(const p of d.paths){
   const commands=p.commands.map(c=>Object.fromEntries(Object.entries(c).map(([k,v])=>[k,k==='close'?{}:{x:v.x*scale,y:v.y*scale}])));
   const s=slide.shapes.add({geometry:'custom',name:`${++serial} ${type} vector path`,position:{left:xx,top:yy,width:d.width*scale,height:d.height*scale},fill:p.fill,line:{fill:'none',width:0},customPaths:[{width:d.width*scale,height:d.height*scale,commands}]});save(s,type);
   const dd=commands.map(c=>c.moveTo?`M${c.moveTo.x+xx},${c.moveTo.y+yy}`:c.lineTo?`L${c.lineTo.x+xx},${c.lineTo.y+yy}`:'Z').join(' ');
   svg.push(`<path d="${dd}" fill="${p.fill}"/>`);
  }
 });
 iconFiles.set(type,{x,y,w,h,parts:svg.slice(begin).join('\n')});
}
function semantic(type,x,y,w,h=w){
 const begin=svg.length;
 groupWith(`icon-${type}-${serial}`,()=>{
  const X=a=>x+w*a/40,Y=a=>y+h*a/40,S=Math.min(w,h)/40;
  const p=(pts,col=C.ink,sw=2,fill='none',close=false)=>poly(pts.map(([a,b])=>[X(a),Y(b)]),col,sw*S,fill,close);
  const e=(a,b,c,d,fill,stroke=C.ink,sw=2)=>ellipse(X(a),Y(b),w*c/40,h*d/40,fill,stroke,sw*S);
  const l=(a,b,c,d,col=C.ink,sw=2)=>ln(X(a),Y(b),X(c),Y(d),col,sw*S);
  if(type==='location'){
   p([...cubic([20,3],[2,3],[6,24],[20,37]),...cubic([20,37],[34,24],[38,3],[20,3])],C.ink,1.5,C.ink,true);e(14,10,12,12,'#FFFFFF','none',0);
  }else if(type==='hypothesis'){
   p([...cubic([11,22],[-1,1],[41,1],[29,22]),[25,28],[15,28],[11,22]],C.ink,2.5);
   l(14,32,26,32);l(17,36,23,36);p([[18,24],[18,18],[24,13],[19,10],[15,13]],'#1773C3',2);
  }else if(type==='clipboard'){
   box(X(7),Y(5),w*.65,h*.85,'#F8FCFF',C.ink,2*S,2*S);box(X(15),Y(1),w*.25,h*.15,'#DBEAF9',C.ink,1.7*S,1*S);
   for(const yy of [15,22,29]){l(18,yy,28,yy,C.blue,1.5);p([[11,yy],[13,yy+2],[15,yy-2]],C.blue,1.2);}
  }else if(type==='orchestrator'){
   p([[20,8],[20,19],[6,19],[6,31]],C.blue,2.5);p([[20,19],[34,19],[34,31]],C.blue,2.5);l(20,19,20,31,C.blue,2.5);
   for(const [a,b] of [[20,6],[6,33],[20,33],[34,33]])e(a-4,b-4,8,8,'#77C8FF',C.blue,2.5);
  }
 });
 if(!iconFiles.has(type))iconFiles.set(type,{x,y,w,h,parts:svg.slice(begin).join('\n')});
}
function folder(x,y,w=24,color='#B5E4FF'){
 const h=w*.76;
 groupWith(`folder-${serial}`,()=>{
  poly([[x,y+h*.15],[x+w*.4,y+h*.15],[x+w*.52,y+h*.29],[x+w,y+h*.29],[x+w,y+h],[x,y+h]],C.blue,1.6,color,true,'folder');
  ln(x+1,y+h*.37,x+w-1,y+h*.37,'#56B3EC',1);
 });
}
function database(x,y,w,h){
 const begin=svg.length;
 groupWith(`database-${serial}`,()=>{
  box(x,y+h*.13,w,h*.73,gradient('#B4A0EB','#7551CB'),'none',0,0);
  ellipse(x,y+h*.73,w,h*.27,'#7958CA','#6944BD',1.4);
  for(const yy of [.38,.64])poly(cubic([x,y+h*yy],[x+w*.14,y+h*(yy+.2)],[x+w*.86,y+h*(yy+.2)],[x+w,y+h*yy]),'#FFFFFF',1.6);
  ellipse(x,y,w,h*.28,'#BBA9EF','#8963D6',1.4);
  ln(x,y+h*.14,x,y+h*.85,'#8963D6',1.2);ln(x+w,y+h*.14,x+w,y+h*.85,'#8963D6',1.2);
 });
 if(!iconFiles.has('database'))iconFiles.set('database',{x,y,w,h,parts:svg.slice(begin).join('\n')});
}
function spark(x,y,w,h,row,target=false){
 const blue='#0082FF',red='#FB1419';
 ln(x,y,x,y+h,'#7094BD',1);ln(x,y+h,x+w,y+h,'#7094BD',1);
 const points=[];
 for(let i=0;i<=72;i++){
  const t=i/72,decay=.44-.23*t;
  let v=.72-decay*Math.sin(t*5*Math.PI)**2;
  if(target&&row===1)v=.87+.025*Math.sin(t*47);
  if(row===2){v=.8-(.50+.2*t)*Math.sin(t*5*Math.PI)**2;if(target&&t>.49)v=.42+.48*(t-.49)/.51+.06*Math.sin(t*40);}
  points.push([x+w*t,y+h*v]);
 }
 poly(points,target?red:blue,1.8,'none',false,`${target?'Target':'Source'} ${['execution','forward','gradients','parameter update','next forward'][row]} curve`);
}
function sourceTree(){
 folder(56,208,23);text('my_project/',95,203,157,21);
 ln(66,232,66,377,'#587394',1.4);
 const names=['train.py','model.py','data.py'];
 names.forEach((v,i)=>{const y=239+i*40;ln(66,y+18,81,y+18,'#587394',1.4);box(126,y,125,35,'#F2F5F9','none',0,7);if(i===0)logo('python',97,y+4,24,25);else icon('document',94,y+1,28,31);text(v,138,y+4,113,21);});
 ln(66,368,80,368,'#587394',1.4);text('…  …',96,355,137,24);
}

groupWith('Migration Setting',()=>{
 box(21,38,266,597,gradient('#FFF2E6','#FFFDF9'),'#FF721F',1.3,12);
 text('Migration Setting',35,50,241,30,true,'center');
 box(30,100,248,296,gradient('#FFFFFF','#FFFCF7'),'#FFBB8C',1.1,12);
 text('Source Repository',44,109,220,24,true,'center');
 logo('torch',50,144,31,38);text('PyTorch (Python)',91,149,177,22,true);
 sourceTree();
 text('Target Frameworks\n& Languages',40,405,230,21,true);
 for(const [x,y] of [[41,464],[158,464],[41,549],[158,549]])box(x,y,108,76,gradient('#F2F6FA','#FBFCFD'),'#DEE4EC',1,9);
 logo('mindspore',69,475,55,31);text('MindSpore',47,512,97,19,false,'center');
 logo('jax',184,474,54,32);text('JAX',166,512,92,19,false,'center');
 logo('java',81,557,30,41);text('Java',47,598,96,19,false,'center');
 text('…',170,565,84,32,true,'center');
});
groupWith('Translator Agent',()=>{
 box(318,49,150,574,gradient('#DDF3FF','#EDF9FE'),'#0085F7',1.5,15);
 text('Translator\nAgent',329,81,128,27,true,'center');
 icon('robot',362,174,63,60,'#8ADAAB');
 text('Translate\nto target\necosystem',335,262,116,22,false,'center');
 box(330,366,126,98,gradient('#FFFFFF','#F7FBFE'),'#8FC5F8',1,8);
 text('# translated',339,379,109,18);text('def train():',340,404,108,18);text('…',353,427,79,21,false,'center');
 ln(393,464,393,530,'#0875BD',1.8);text('candidate\nprogram',335,534,116,21,false,'center');
});
groupWith('LaDiM framework',()=>{
 box(483,16,970,627,gradient('#E0F3FF','#E5F5FF'),'#56ACFF',1.4,40);
 text('LaDiM: Multi-Agent Framework for Code Migration and Repair',520,23,905,32,true,'center');
});
groupWith('Verifier Agent',()=>{
 box(511,80,473,394,gradient('#E9F6FF','#F6FCFF'),'#2C9CFF',1.4,18);
 icon('robot',538,99,63,60,'#85CCFF');
 text('Verifier Agent',627,94,330,31,true);text('Layered Diagnosis',627,135,330,28);
 box(526,175,443,281,'#FCFEFF','#D3E8FB',1,11);
 text('Stage',537,181,130,21,true);text('Source',688,181,112,21,true,'center','#006FF2');text('Target',836,181,112,21,true,'center','#F20A10');
 ln(675,183,675,448,'#A3BFDD',1);ln(535,209,959,209,'#C7DDF2',1);
 box(535,298,423,48,gradient('#FFEDEE','#FFF6F6'),'none',0,0);
 const names=['Execution','Forward','Gradients','Parameter update','Next forward'];
 names.forEach((name,i)=>{const y=215+i*49; text(name,537,y+2,134,18.4,i===2);spark(695,y+5,99,19,i);spark(840,i===1?y-11:y+5,98,19,i,true);if(i<4)ln(535,y+38,959,y+38,'#B9D3EC',1);});
 ln(675,298,675,346,'#A3BFDD',1);
 // Dashed annotation circle is a set of editable arc segments.
 for(let i=0;i<16;i++){const a=i*2*Math.PI/16;poly(Array.from({length:6},(_,j)=>[801+29*Math.cos(a+j*.045),325+29*Math.sin(a+j*.045)]),'#F31017',1.5);}
 text('First divergence',820,274,142,18.5,true,'left','#F31017');arrow([[831,299],[806,324]],'#F31017',1.5,9);
});
groupWith('Evidence Handoff',()=>{
 box(1021,80,410,188,gradient('#FFE9C8','#FFF4E4'),'#F17F00',1.5,18);
 box(1044,97,57,62,gradient('#FFD68C','#FFB14D'),'none',0,14);
 icon('document',1048,100,49,55);
 text('Evidence Handoff',1123,97,291,30,true,'left','#7D1D08');
 box(1038,153,377,99,gradient('#FFFFFF','#FFFCF8'),'#E5DACA',1,10);
 const xs=[1090,1190,1279,1368];
 icon('code',1077,170,31,28);semantic('clipboard',1177,168,27,33);semantic('location',1264,168,29,31);semantic('hypothesis',1354,168,29,31);
 [1144,1234,1323].forEach(x=>ln(x,166,x,242,'#D5D9DD',1));
 ['Code\nobservations','Test\nresults','Locations','Hypotheses'].forEach((v,i)=>text(v,xs[i]-46,204,92,17.5,false,'center'));
});
groupWith('Repair Agent',()=>{
 box(1042,298,380,184,gradient('#E1F6EB','#F0FCF7'),'#00974C',1.5,17);
 icon('robot',1059,311,64,56,'#9CE3AF');
 text('Repair Agent',1144,310,260,29,true,'left','#092B21');text('Patch and Validate',1144,347,259,23,false,'left','#12332D');
 box(1058,381,348,87,'#FDFFFE','#CBE7DC',1,10);
 box(1070,393,325,26,'#FFE7E9','none',0,2);box(1070,419,325,27,'#D5F3E5','none',0,2);
 text('-  loss = x.sum()',1078,395,301,19,false,'left','#AD0610');text('+  loss = x.mean()',1078,421,301,19,false,'left','#124835');text('…',1104,441,230,21);
});
groupWith('Orchestrator',()=>{
 box(511,543,911,77,gradient('#C3E4FF','#E0F2FF'),'#168FFF',1.5,16);
 semantic('orchestrator',552,562,50,39);text('Orchestrator',621,559,204,32,true);
 [836,982,1178].forEach(x=>ln(x,565,x,599,'#3097F1',1.1));
 text('Execute',855,567,110,22,false,'center');text('Manage State',1000,567,161,22,false,'center');text('Coordinate Agents',1190,567,218,22,false,'center');
});
groupWith('Flow connections',()=>{
 arrow([[278,299],[313,299]],'#1C4976',2,15);
 arrow([[432,576],[505,576]],'#0084EF',2.2,15);
 arrow([[729,543],[729,474]],'#0088F9',2.8,15);text('execution\nresults',624,488,95,19,false,'center');
 arrow([[798,474],[798,541]],'#0088F9',2.8,15);text('diagnosis\nfeedback',821,488,120,19);
 arrow([[985,155],[1020,155]],'#FF8B00',2.4,14);arrow([[1228,269],[1228,296]],'#FF8B00',2.5,14);
 arrow([[1104,542],[1104,483]],'#0CAF69',2.7,14);text('revised\nprogram',1124,488,119,19);
 arrow([[1255,483],[1255,541]],'#0CAF69',2.7,14);text('execute\n& validate',1276,488,130,19);
 poly([[836,643],[843,652],[836,661],[829,652]],'#8460D9',.5,'#8460D9',true,'Context link diamond');
});
groupWith('Verified Output',()=>{
 box(1466,49,189,574,gradient('#ECFAF3','#F7FDF9'),'#16866C',1.4,14);
 box(1467,50,187,67,gradient('#DEF6EC','#E8F9F1'),'none',0,12);
 text('Verified Output',1478,68,168,26,true,'center','#082A31');
 icon('check',1486,139,49,49);text('Migrated\nProgram',1546,138,100,22,true);
 box(1478,215,165,83,'#FFFFFF','#D8EDE9',1,11);
 logo('java',1512,225,44,62);text('Java',1567,233,67,22,true);text('(target)',1567,259,67,18);
 box(1478,314,165,206,'#FFFFFF','#D8EDE9',1,11);
 folder(1488,332,20);text('my_project/',1518,327,120,19);
 ln(1497,360,1497,502,'#587394',1.2);
 ['Main.java','Model.java','Data.java'].forEach((v,i)=>{let y=368+i*38;ln(1497,y+16,1508,y+16,'#587394',1.2);icon('document',1512,y+3,23,29);box(1539,y,95,34,'#F3F5F8','none',0,6);text(v,1546,y+5,86,19.5);});
 ln(1497,492,1508,492,'#587394',1.2);text('…  …',1515,479,121,22);
});
groupWith('Repository Context Management',()=>{
 box(26,661,1628,260,gradient('#EEE9FF','#F6F3FF'),'#947AFF',1.5,14);
 database(43,673,28,30);text('Repository Context Management',87,669,900,29,true,'left','#110F59');
 box(41,716,534,192,'#FCFBFF','#C7B9FF',1.1,10);
 box(585,716,481,192,'#FCFBFF','#C7B9FF',1.1,10);
 box(1075,716,566,192,'#FCFBFF','#C7B9FF',1.1,10);
});
groupWith('Repository Structural Analysis',()=>{
 text('Repository Structural Analysis',60,721,498,22,true,'left','#100C59');
 folder(84,758,18);text('src/',111,753,164,21);
 ln(93,780,93,893,'#587394',1.5);
 ['models/','data/','utils/','…'].forEach((v,i)=>{let y=788+i*28;ln(93,y+9,107,y+9,'#587394',1.4);folder(118,y,18,i===3?'#FFFFFF':'#B5E4FF');text(v,146,y-5,146,20);});
 ln(314,757,314,893,'#3C70B6',1.5);
 ['Functions','Classes','Imports','…'].forEach((v,i)=>{const y=750+i*41;if(i<3)box(347,y,195,36,gradient('#EAF0FF','#F6F8FF'),'#E1E8FC',.8,8);if(i===0)text('ƒx',362,y+1,39,25,true,'center','#004DD8');if(i===1){box(368,y+6,19,22,'#BCE4BA','#178648',1,1);text('C',369,y+3,17,23,true,'center','#078035');}if(i===2)icon('document',367,y+4,24,26);text(v,i===3?367:414,y+5,i===3?148:121,19);});
});
groupWith('Repair Dependency Graph Planning',()=>{
 text('Repair Dependency Graph Planning',605,721,440,22,true,'left','#100C59');
 arrow([[712,807],[755,783]],'#2E5B9B',1.7,8,true);arrow([[715,827],[770,858]],'#2E5B9B',1.7,8);arrow([[811,856],[884,817]],'#2E5B9B',1.7,8,true);
 ellipse(681,803,32,32,gradient('#C6ACFC','#AF8AF0'),'#7725DC',1.8);text('train.py',653,841,97,19);
 ellipse(759,765,33,33,gradient('#C7EFFF','#8FCBFF'),'#008BFE',1.8);text('model.py',806,768,137,19);
 ellipse(890,803,33,33,gradient('#C7EFFF','#8FCBFF'),'#008BFE',1.8);text('utils.py',937,806,110,19);
 ellipse(775,851,34,34,gradient('#B7EAD3','#71C996'),'#079A4F',1.8);text('data.py',824,859,135,19);
});
groupWith('Evidence Retrieval and Context Reconstruction',()=>{
 text('Evidence Retrieval & Context Reconstruction',1096,721,526,22,true,'left','#100C59');
 database(1124,771,65,89);text('Evidence store',1095,865,123,18.5,true,'center');
 arrow([[1203,817],[1231,817]],'#285992',1.4,10);
 ['Code snippets','Test results','Error logs','Historical fixes','…'].forEach((v,i)=>{let y=758+i*28;box(1243,y,171,26,'#EBF1FE','#DCE6F9',.7,5);icon('document',1259,y+3,19,20);text(v,1291,y+2,121,18);});
 arrow([[1427,817],[1452,817]],'#285992',1.4,10);icon('document',1461,788,46,55);text('Reconstructed\ncontext for\nrepair',1519,783,112,18);
});

slide.speakerNotes.textFrame.setText('Reconstructed from the user-provided ChatGPT Image Sep 24, 2026, 09_38_25 PM.png. Font: Times New Roman. Supplied SVG contours from figures/icons and figures/editable-method-20260924/icons. Each module and icon is an editable group. Curves reproduce the illustration; they are not experimental measurements.');
await (await PresentationFile.exportPptx(ppt)).save(path.join(build,'candidate.pptx'));
const fullSvg=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><defs>${defs.join('\n')}</defs><rect width="${W}" height="${H}" fill="white"/>${svg.join('\n')}</svg>`;
await fs.writeFile(path.join(out,'method-diagram.svg'),fullSvg);
for(const [type,{x,y,w,h,parts}] of iconFiles)await fs.writeFile(path.join(out,'icons',type+'.svg'),`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="${x-2} ${y-2} ${w+4} ${h+4}"><defs>${defs.join('\n')}</defs>${parts}</svg>`);
await fs.writeFile(path.join(build,'shape-groups.json'),JSON.stringify({width:W,height:H,font:FONT,records},null,2));
const png=await ppt.export({slide,format:'png',scale:1.5});
await fs.writeFile(path.join(build,'artifact-preview.png'),new Uint8Array(await png.arrayBuffer()));
await fs.writeFile(path.join(build,'layout.json'),await (await slide.export({format:'layout'})).text());
console.log(JSON.stringify({shapes:records.length,text:records.filter(x=>x.label).length,output:out}));
