/** Rebuild the user-supplied 2026-09-24 method image as native PPT objects.
 * Both SVG and PPTX are generated from the same geometry. No raster tracing.
 * Requires the bundled @oai/artifact-tool (RUNTIME_NODE_MODULES).
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { spawnSync } from 'node:child_process';
const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const build = path.join(root, 'tmp/method-flow-focus-20260924');
const out = path.join(root, 'figures/editable-method-focus-20260924');
await fs.mkdir(build, { recursive: true });
await fs.mkdir(path.join(out, 'icons'), { recursive: true });
const runtime = path.join(process.env.RUNTIME_NODE_MODULES, '@oai/artifact-tool/dist/artifact_tool.mjs');
const { Presentation, PresentationFile } = await import(pathToFileURL(runtime).href);
const W = 1672, H = 941, FONT = 'Times New Roman';
const preparation=spawnSync(process.env.RUNTIME_PYTHON??'python3',[path.join(root,'scripts/finalize_method_focus_20260924.py'),'--prepare-fonts'],{encoding:'utf8'});
if(preparation.status!==0)throw new Error(preparation.stderr||'Font preparation failed');
const fontMetrics = JSON.parse(await fs.readFile(path.join(build, 'font-metrics.json'), 'utf8'));
const ppt = Presentation.create({slideSize:{width:W,height:H}});
const slide = ppt.slides.add();
slide.background.fill = '#FFFFFF';
const C = { ink:'#071E4C', blue:'#064A92', line:'#082752', pale:'#F7F9FC', grey:'#71869C', green:'#007253' };
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
function codeLines(lines,x,y,w,size=16,lh=20,colors={}){lines.forEach((s,i)=>text(s,x,y+i*lh,w,size,false,'left',colors[i]??'#003599'));}
function fileTree(x,y,w,rowH,rootName,{highlight=true,checks=false}={}){
 icon('folder',x,y+1,23,23);text(rootName,x+34,y-1,w-35,21);
 const names=['train.py','model.py','data.py','utils.py','config.yaml'];
 const start=y+37;
 ln(x+9,start-11,x+9,start+4*rowH+30,'#656F7B',1.7);
 names.forEach((n,i)=>{
  const yy=start+i*rowH;
  if(highlight)box(x+57,yy-4,w-61,rowH-4,'#F2F5F8','none',0,6);
  ln(x+9,yy+11,x+22,yy+11,'#656F7B',1.7);
  icon(i===0?'python':i===4?'config':'document',x+31,yy-2,24,27);
  text(n,x+72,yy-3,w-75,20);
  if(checks)icon('check',x+w-39,yy+1,23);
 });
 text('…',x+31,start+4*rowH+24,50,20,false,'left',C.ink,20);
}

// Supplied logo paths, sampled from their vector curves, remain native shapes.
const logos=JSON.parse(await fs.readFile(path.join(build,'logo-paths.json'),'utf8'));
function logo(type,x,y,w,h){
 const d=logos[type],scale=Math.min(w/d.width,h/d.height);
 const xx=x+(w-d.width*scale)/2, yy=y+(h-d.height*scale)/2;
 const begin=svg.length;
 groupWith(`icon-${type}-${serial}`,()=>{
  for(const p of d.paths){
   const commands=p.commands.map(c=>Object.fromEntries(Object.entries(c).map(([k,v])=>[k,k==='close'?{}:{x:v.x*scale,y:v.y*scale}])));
   const s=slide.shapes.add({geometry:'custom',name:`${++serial} ${type} vector path`,position:{left:xx,top:yy,width:d.width*scale,height:d.height*scale},fill:p.fill,line:{fill:'none',width:0},customPaths:[{width:d.width*scale,height:d.height*scale,commands}]});save(s,type);
   const pathD=commands.map(c=>c.moveTo?`M${c.moveTo.x+xx},${c.moveTo.y+yy}`:c.lineTo?`L${c.lineTo.x+xx},${c.lineTo.y+yy}`:'Z').join(' ');
   svg.push(`<path d="${pathD}" fill="${p.fill}"/>`);
  }
 });
 iconFiles.set(type,{x,y,w,h,parts:svg.slice(begin).join('\n')});
}
function robot(x,y,color){
 groupWith(`robot-${serial}`,()=>{
  ln(x+20,y+6,x+20,y+15,color,2);ellipse(x+16,y,8,8,color);
  box(x,y+22,4,12,color,'none',0,2);box(x+36,y+22,4,12,color,'none',0,2);
  box(x+5,y+13,30,29,gradient(color,color),'none',0,6);
  ellipse(x+11,y+22,6,6,'#FFFFFF');ellipse(x+23,y+22,6,6,'#FFFFFF');
  poly(cubic([x+15,y+33],[x+17,y+36],[x+23,y+36],[x+26,y+33]),'#FFFFFF',1.5);
 });
}
function folder(x,y,s=20){
 poly([[x,y+2],[x+s*.38,y+2],[x+s*.5,y+6],[x+s,y+6],[x+s,y+s*.85],[x,y+s*.85]],C.blue,1.7,'#52A8EF',true,'folder icon');
}
function treeSimple(x,y,w,ext='py',modelDir=false){
 folder(x,y,18);text('src/',x+29,y-3,w-29,19);
 const col='#7290B3';
 if(!modelDir){
  ln(x+10,y+26,x+10,y+38,col,1);ln(x+10,y+38,x+22,y+38,col,1);
  ln(x+33,y+28,x+33,y+116,col,1.3);
  [`model.${ext}`,`train.${ext}`,`utils.${ext}`,'…'].forEach((s,i)=>{let yy=y+28+i*26;ln(x+33,yy+10,x+47,yy+10,col,1.3);text(s,x+62,yy-2,w-62,18);});
 }else{
  ln(x+9,y+25,x+9,y+133,col,1.4);
  ln(x+9,y+32,x+22,y+32,col,1.2);text('models/',x+61,y+18,w-61,18);
  ln(x+38,y+24,x+38,y+121,col,1.3);
  ln(x+38,y+32,x+50,y+32,col,1.2);ln(x+65,y+42,x+65,y+58,col,1);ln(x+65,y+58,x+78,y+58,col,1);
  text('model.py',x+83,y+40,w-83,18);
  ['train.py','utils.py','…'].forEach((s,i)=>{let yy=y+64+i*22;ln(x+38,yy+10,x+50,yy+10,col,1.2);text(s,x+61,yy-2,w-61,18);});
 }
}
function documentIcon(x,y,w=25,h=32,color=C.ink){
 groupWith(`document-${serial}`,()=>{
  poly([[x,y],[x+w*.62,y],[x+w,y+h*.29],[x+w,y+h],[x,y+h]],color,2,'#F7FAFE',true,'document');
  poly([[x+w*.62,y],[x+w*.62,y+h*.29],[x+w,y+h*.29]],color,1.7);
  ln(x+w*.24,y+h*.48,x+w*.73,y+h*.48,color,1.8);ln(x+w*.24,y+h*.67,x+w*.58,y+h*.67,color,1.8);
 });
}
function database(x,y,w,h,color='#7661BC'){
 groupWith(`database-${serial}`,()=>{
  box(x,y+h*.16,w,h*.7,gradient('#ABC8C2',color),'none',0,0);
  ellipse(x,y+h*.72,w,h*.28,color,'#5F8D84',1.5);
  for(let i=1;i<=2;i++){const yy=y+h*(.16+i*.24);poly(cubic([x,yy],[x+w*.15,yy+h*.19],[x+w*.85,yy+h*.19],[x+w,yy]),'#FFFFFF',1.6);}
  ellipse(x,y,w,h*.27,'#BCD4CF','#5F8D84',1.5);
  ln(x,y+h*.14,x,y+h*.86,'#5F8D84',1.3);ln(x+w,y+h*.14,x+w,y+h*.86,'#5F8D84',1.3);
 });
}
function spark(x,y,w,h,kind,target=false){
 ln(x,y,x,y+h,'#729ACA',1);ln(x,y+h*.72,x+w,y+h*.72,'#D4E1F2',.7);
 const base=[.65,.52,.44,.55,.66,.57,.45,.48,.6,.56,.49,.57,.67,.69,.62,.51,.44,.46,.53,.54];
 const pts=base.map((v,i)=>{
  let v2=kind===0?[.63,.51,.52,.61,.63,.61,.65,.63,.57,.53,.48,.4,.36,.34,.29,.24,.21,.19,.18,.2][i]:v;
  if(kind===2&&target)v2=.57+Math.sin(i*1.7)*.04+(i<6?.03:0);
  return [x+i*w/(base.length-1),y+h*Math.max(.08,v2)];
 });
 poly(pts,kind===2?'#B55949':'#4E8E85',1.8,'none',false,'editable diagnostic curve');
}

groupWith('Source program',()=>{
 box(28,55,210,410,'#F7F8F9','#B8C7D3',1.3,8);
 text('Source program',43,73,180,23,true,'center','#52616F');text('Repository',43,101,180,18,false,'center','#6C7884');
 logo('python',58,148,38,42);text('Python',111,160,105,20,false,'left','#596875');
 logo('torch',59,211,36,42);text('PyTorch',111,224,105,20,false,'left','#596875');
 ln(49,274,217,274,'#DDE2E6',.8);folder(53,302,19);text('src/ …',86,298,118,20,false,'left','#6C7884');
 box(47,330,172,111,'#FBFCFE','#D4DEE6',.8,6);text('model.py',61,346,140,18);text('train.py',61,373,140,18);text('utils.py',61,400,140,18);
});
groupWith('Translator',()=>{
 box(252,55,184,410,'#F7F8F9','#BCC8D2',1.1,8);
 robot(325,77,'#6F7F8C');text('Translator',267,138,154,24,true,'center','#4E606F');
 text('Translate candidate',267,172,154,18,false,'center','#657582');
 box(269,220,150,126,'#FBFCFE','#D4DEE6',.8,6);documentIcon(286,239,21,28,'#7F8D99');text('Initial code',317,244,92,18,false,'left','#657582');
 text('…',307,300,70,26,false,'center','#7F8D99');
});
groupWith('Verifier Agent',()=>{
 box(450,55,560,410,'#EAF4F1','#2F786D',2.1,9);
 robot(474,71,'#28675F');text('Verifier Agent',532,68,451,31,true,'left','#214F4C');
 text('Layered Diagnosis',473,107,511,27,true,'left','#214F4C');
 box(465,148,530,205,'#FFFFFF','#C3D9D4',1.1,7);
 text('Training computation',481,159,170,20,true,'left','#214F4C');
 text('Source',667,159,120,20,true,'center','#214F4C');text('Target',822,159,120,20,true,'center','#214F4C');
 [194,246,298].forEach(y=>ln(475,y,985,y,'#D7E7E2',1));[650,805].forEach(x=>ln(x,157,x,351,'#D7E7E2',1));
 box(472,298,516,48,'#FAE9E5','none',0,5);
 const names=['Execution (loss curve)','Forward values','Gradients'];
 names.forEach((label,i)=>{const y=200+i*52;text(label,481,y,160,20,i===2,'left',i===2?'#A44F40':'#2B4847');spark(665,y+2,122,29,i,false);spark(820,y+2,121,29,i,true);});
 ellipse(958,307,23,23,'#B55949');text('!',962,304,15,21,true,'center','#FFFFFF');text('First divergence',803,329,151,17.5,true,'right','#A44F40');
});
groupWith('Evidence handoff',()=>{
 box(1024,55,198,410,'#E8F0F6','#416E8B',2.2,8);
 text('Evidence handoff',1039,76,168,25,true,'center','#355773');text('Findings for repair',1039,111,168,17.2,false,'center','#607990');ln(1037,144,1209,144,'#B9CDD9',1);
 documentIcon(1042,171,22,29,'#587A96');text('Code observations',1074,175,135,18.5,false,'left','#34536A');
 [0,1,2].forEach(i=>box(1043+i*8,238-i*7,5,11+i*7,'#587A96','none',0,0));ln(1040,250,1069,250,'#587A96',1.8);text('Test results',1074,224,135,18.5,false,'left','#34536A');
 documentIcon(1042,278,21,27,'#587A96');text('Code locations',1074,282,135,18.5,false,'left','#34536A');
 ellipse(1042,348,21,22,'#FFFFFF','#587A96',1.8);poly([[1046,366],[1048,373],[1057,373],[1060,366]],'#587A96',1.8);ln(1048,377,1057,377,'#587A96',1.8);text('Hypotheses',1074,351,135,18.5,false,'left','#34536A');
 [214,266,326].forEach(y=>ln(1039,y,1207,y,'#C7D8E1',.8));
});
groupWith('Repair Agent',()=>{
 box(1236,55,184,410,'#F7F8F9','#BCC8D2',1.1,8);
 robot(1309,77,'#6F7F8C');text('Repair Agent',1251,138,154,24,true,'center','#4E606F');
 text('Revise candidate',1251,172,154,18,false,'center','#657582');
 box(1255,220,146,126,'#FBFCFE','#D4DEE6',.8,6);documentIcon(1272,239,21,28,'#7F8D99');text('Revised code',1302,244,92,18,false,'left','#657582');
 text('…',1291,300,70,26,false,'center','#7F8D99');
});
groupWith('Target program',()=>{
 box(1434,55,210,410,'#F7F8F9','#B8C7D3',1.3,8);
 text('Target program',1449,73,180,23,true,'center','#52616F');text('Repository',1449,101,180,18,false,'center','#6C7884');
 logo('java',1472,148,38,45);text('Java',1523,160,105,20,false,'left','#596875');
 logo('mindspore',1473,211,60,37);text('MindSpore',1523,224,105,20,false,'left','#596875');
 ln(1455,274,1623,274,'#DDE2E6',.8);folder(1458,302,19);text('src/ …',1491,298,118,20,false,'left','#6C7884');
 box(1451,330,172,111,'#FBFCFE','#D4DEE6',.8,6);text('model.java',1465,346,140,18);text('train.java',1465,373,140,18);text('utils.java',1465,400,140,18);
});
groupWith('Orchestrator',()=>{
 box(230,540,1225,56,'#F5F7F8','#B9C6CF',1,7);
 let gear=[];for(let i=0;i<48;i++){const a=2*Math.PI*i/48,r=[0,1,4,5].includes(i%6)?11:14;gear.push([258+r*Math.cos(a),568+r*Math.sin(a)]);}
 poly(gear,'#6D7F8D',.5,'#6D7F8D',true,'orchestrator gear');ellipse(252,562,12,12,'#F5F7F8');
 text('Orchestrator',281,552,204,24,true,'left','#4A6070');
 ln(486,552,486,583,'#D1DBE1',1);
 text('Schedule',508,554,177,21,false,'center','#536A79');
 text('Execute & measure',748,554,276,21,true,'center','#435E6B');
 text('Return results',1110,554,248,21,false,'center','#536A79');
 arrow([[689,568],[733,568]],'#8E9DA7',1.4,8);arrow([[1034,568],[1085,568]],'#8E9DA7',1.4,8);
});
groupWith('Execution and repair connections',()=>{
 arrow([[238,260],[252,260]],'#7F8F9B',1.8,8);
 arrow([[436,260],[450,260]],'#355773',2.4,10);
 arrow([[1010,260],[1024,260]],'#355773',2.6,10);
 arrow([[1222,260],[1236,260]],'#355773',2.6,10);
 arrow([[1420,260],[1434,260]],'#7F8F9B',1.8,8);
 arrow([[344,465],[344,539]],'#7D919B',1.7,9);
 text('Initial code',354,481,110,18,false,'left','#697F8D');
 arrow([[730,465],[730,539]],'#36776F',2.2,10,true);
 text('Checks & tests',520,493,190,18,false,'right','#3E706A');
 text('Execution information',752,483,244,18,false,'left','#3E706A');
 text('(errors & measurements)',752,506,256,18,false,'left','#3E706A');
 arrow([[1328,465],[1328,539]],'#7D919B',1.7,9);
 text('Revised code',1215,481,107,18,false,'right','#697F8D');
 arrow([[1455,568],[1566,568],[1566,465]],'#7D919B',1.7,9);
 text('Accepted',1500,477,133,18,false,'center','#697F8D');
});
groupWith('Repository Context Management',()=>{
 box(33,632,1609,261,'#EDF4F3','#4D817A',1.6,8);
 database(59,649,29,31,'#5C8B83');text('Repository Context Management',108,644,578,29,true,'left','#214F4C');
 text('Structure, dependencies, and evidence across repair iterations',710,652,901,21,false,'left','#54746F');
});
groupWith('Repository Structural Analysis',()=>{
 box(53,689,525,193,'#FFFFFF','#B3CCC7',1,7);text('Repository Structural Analysis',78,695,478,20.5,true,'left','#214F4C');
 box(72,724,252,150,'#FBFDFC','#DEE9E6',.8,6);box(348,724,213,150,'#FBFDFC','#DEE9E6',.8,6);
 treeSimple(90,734,223,'py',true);ln(325,733,325,866,'#8EACCE',1);
 ['Functions','Classes','Imports'].forEach((s,i)=>{
  const yy=732+i*39;box(354,yy,49,35,['#EDF4F2','#EDF4F2','#EDF4F2'][i],'none',0,6);
  if(i===0)text('ƒx',367,yy+1,30,26,true,'left','#456E68');
  if(i===1){box(370,yy+7,18,21,'none','#117553',2,1);text('C',373,yy+5,15,17,true,'left','#117553');}
  if(i===2)documentIcon(371,yy+6,16,21,'#456E68');
  text(s,419,yy+4,126,18);ln(419,yy+35,474,yy+35,'#E4EBF7',.7);
 });
 text('…',366,841,100,21);
});
groupWith('Repair Dependency Graph Planning',()=>{
 box(590,689,490,193,'#FFFFFF','#B3CCC7',1,7);text('Repair Dependency Graph Planning',612,696,448,20.5,true,'left','#214F4C');
 arrow([[691,780],[724,755]],'#45658D',1.4,7,true);
 arrow([[694,798],[741,824]],'#45658D',1.4,7,true);
 arrow([[780,822],[817,796]],'#45658D',1.4,7,true);
 [[727,732,32,'#CAE0DC','#548D82'],[664,778,28,'#C9D9E3','#648198'],[821,774,32,'#CAE0DC','#548D82'],[744,819,34,'#D7E4DC','#6D9582']].forEach(([x,y,s,f,c])=>ellipse(x,y,s,s,gradient('#FFFFFF',f),c,2));
 text('model.py',769,737,110,18);text('train.py',633,810,88,18);text('utils.py',859,791,77,18);text('data.py',793,833,90,18);
 text('Plan repair order\nvia dependency graph',924,768,146,17.5);
});
groupWith('Evidence Retrieval and Context Reconstruction',()=>{
 box(1091,689,536,193,'#FFFFFF','#B3CCC7',1,7);text('Evidence Retrieval & Context Reconstruction',1114,695,497,20.5,true,'left','#214F4C');
 box(1105,726,505,141,'#FBFDFC','#DEE9E6',.8,7);
 database(1135,749,60,86,'#6C998F');text('Evidence store',1115,841,111,18,false,'center');
 arrow([[1206,797],[1234,797]],'#385C8A',1.6,8);
 ['Code snippets','Test results','Error logs','Historical fixes','…'].forEach((s,i)=>{
  let yy=729+i*28;box(1243,yy,169,26,'#EFF5F4','#D4E2DE',.7,4);documentIcon(1260,yy+6,10,16,C.ink);text(s,1288,yy+1,115,17.5);
 });
 ln(1433,735,1433,859,'#D3E0F4',.8);arrow([[1418,798],[1440,798]],C.ink,1.6,8);
 documentIcon(1451,773,34,48,'#17477F');text('Reconstructed\ncontext for\nnext iteration',1502,769,102,17.4);
});
groupWith('Context supports orchestration',()=>arrow([[836,631],[836,597]],'#5E8982',1.7,9));
groupWith('Figure caption',()=>{
 text('Figure 1: Overview of LaDiM.',225,901,300,24,true);
 text('LaDiM translates, verifies, and iteratively repairs programs with repository context management.',530,901,1089,24);
});

slide.speakerNotes.textFrame.setText('Source: user-supplied “ChatGPT Image Sep 24, 2026, 03_56_07 PM.png”. Language and framework logos use vector paths from figures/icons.');
await (await PresentationFile.exportPptx(ppt)).save(path.join(build,'candidate.pptx'));
const fullSvg=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><defs>${defs.join('\n')}</defs><rect width="${W}" height="${H}" fill="white"/>${svg.join('\n')}</svg>`;
await fs.writeFile(path.join(out,'method-diagram.svg'),fullSvg);
for(const [type,{x,y,w,h,parts}] of iconFiles)await fs.writeFile(path.join(out,'icons',type+'.svg'),`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="${x-2} ${y-2} ${w+4} ${h+4}"><defs>${defs.join('\n')}</defs>${parts}</svg>`);
await fs.writeFile(path.join(build,'shape-groups.json'),JSON.stringify({width:W,height:H,font:FONT,records},null,2));
const png=await ppt.export({slide,format:'png',scale:1.5});
await fs.writeFile(path.join(build,'artifact-preview.png'),new Uint8Array(await png.arrayBuffer()));
await fs.writeFile(path.join(build,'layout.json'),await (await slide.export({format:'layout'})).text());
console.log(JSON.stringify({draft:path.join(build,'candidate.pptx'),objects:records.length,icons:iconFiles.size}));

