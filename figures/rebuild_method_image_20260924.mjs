/** Rebuild the user-supplied 2026-09-24 method image as native PPT objects.
 * Both SVG and PPTX are generated from the same geometry. No raster tracing.
 * Requires the bundled @oai/artifact-tool (RUNTIME_NODE_MODULES).
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { spawnSync } from 'node:child_process';
const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const build = path.join(root, 'tmp/method-image-20260924');
const out = path.join(root, 'figures/editable-method-20260924');
await fs.mkdir(build, { recursive: true });
await fs.mkdir(path.join(out, 'icons'), { recursive: true });
const runtime = path.join(process.env.RUNTIME_NODE_MODULES, '@oai/artifact-tool/dist/artifact_tool.mjs');
const { Presentation, PresentationFile } = await import(pathToFileURL(runtime).href);
const W = 1672, H = 941, FONT = 'Times New Roman';
const preparation=spawnSync(process.env.RUNTIME_PYTHON??'python3',[path.join(root,'scripts/finalize_method_image_20260924.py'),'--prepare-fonts'],{encoding:'utf8'});
if(preparation.status!==0)throw new Error(preparation.stderr||'Font preparation failed');
const fontMetrics = JSON.parse(await fs.readFile(path.join(build, 'font-metrics.json'), 'utf8'));
const ppt = Presentation.create({slideSize:{width:W,height:H}});
const slide = ppt.slides.add();
slide.background.fill = '#FFFFFF';
const C = { ink:'#090D28', blue:'#003496', line:'#273247', pale:'#F7F9FC', grey:'#71869C', green:'#159F50' };
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

// Main canvas and title strips.
groupWith('Migration setting',()=>{
 box(16,7,468,827,gradient('#FFEEE2','#FFF8F1'),'#EF6B2C',1.1,18,'orange setting panel');
 box(18,9,464,60,gradient('#FFCFB0','#FFE6D3'),'none',0,17,'setting title strip');
 box(18,61,464,60,'#FFF2E9','none',0,12);
 text('Migration Setting',36,16,428,36,true,'center');
});
groupWith('Framework background',()=>{
 box(498,7,780,827,gradient('#EAFE F5'.replace(' ',''),'#F3FFF8'),'#20AC7A',1.1,18,'green framework panel');
 box(500,9,776,64,gradient('#C0EAD9','#D1EFE1'),'none',0,17);
 box(500,61,776,78,'#EEFFF7','none',0,12);
 text('Dependency Guided Multi-Agent Framework',518,14,740,32,true,'center');
});
groupWith('Verified output background',()=>{
 box(1290,7,368,827,gradient('#DDEAFF','#F1F7FF'),'#276CE6',1.1,18,'blue output panel');
 box(1292,9,364,60,gradient('#C0D8FC','#DAE8FF'),'none',0,17);
 box(1292,67,364,55,'#EDF5FF','none',0,12);
 box(1304,79,342,743,'none','#B5D3FE',.7,16);
 text('Verified Output',1310,16,328,36,true,'center');
});
groupWith('Source repository',()=>{
 box(29,79,442,307,gradient('#FFF2E3','#FFF8EE'),'#F19861',1,14);
 icon('database',43,85,40,40,'#A4C3DC');
 text('Source Repository',97,89,186,25,true);
 text('(Training Project)',286,91,172,22,true);
 box(38,131,423,240,'#FFFFFF','#738FA3',1.2,11);
 fileTree(49,138,176,35,'my_project/');
 box(234,142,216,217,'#F7FAFE','#DCE6F1',.6,8);
 box(234,142,216,29,'#E7EDF3','none',0,8);
 text('train.py',248,145,185,19);
 codeLines(['def train(model, loader):','    model.train()','    for x, y in loader:','        optim.zero_grad()','        loss = model(x, y)','        loss.backward()','        optim.step()'],246,178,205,16,20.2);
});
groupWith('Migration target ecosystem',()=>{
 poly([[243,371],[261,371],[261,382],[270,382],[252,397],[234,382],[243,382]],'#78828B',1,'#B8BCC0',true);
 box(123,397,253,32,'#FFFFFF','none',0,8);text('Migrate to New Ecosystem',128,398,243,24,true,'center');
 box(36,431,427,54,'#FFFFFF','#99A6B0',.9,9);
 box(41,438,128,40,gradient('#EDE9FF','#FAF7FF'),'#9B87ED',.8,7);icon('gear',47,445,25);text('Framework B',78,447,87,18);
 box(176,438,135,40,gradient('#FFF0E0','#FFFCF6'),'#ED9962',.8,7);icon('flame',184,444,26,30);text('Framework C',216,447,91,18);
 box(317,438,140,40,gradient('#E7FFF1','#F7FFFB'),'#62BFA0',.8,7);icon('code',326,447,28,26);text('Language X',362,447,91,18);
 poly([[244,485],[261,485],[261,491],[269,491],[252,505],[235,491],[244,491]],'#78828B',1,'#B8BCC0',true);
});
groupWith('Initial migrated repository',()=>{
 box(29,502,442,320,gradient('#FFF0E0','#FFF8EF'),'#F18C4D',1,14);
 icon('database',43,508,40,40,'#A4C3DC');icon('warning',71,521,28,28);
 text('Initial Migrated Repository',117,515,260,23,true);text('(Imperfect)',376,517,88,20,true);
 box(39,556,422,195,'#FFFFFF','#6E8AA0',1.2,10);
 fileTree(50,561,178,27,'migrated_project/');
 box(240,566,211,176,'#F7FAFE','#DFE8EF',.6,8);box(240,566,211,26,'#E7EDF3','none',0,8);
 text('train.py',250,566,185,18);
 box(245,635,201,25,'#FFE6E8','none',0,5);
 codeLines(['def train(model, loader):','    model.train()','    loss = model(data)','    # missing labels?','    loss.backward()','    optim.step()','    ...'],250,597,198,16,20,{2:'#E60920',3:'#526C8C'});
 box(49,760,400,54,'#FFE7E8','#F04C59',1.1,10);icon('error',58,766,42,42);
 text('Initial migration has errors',118,767,322,21,true,'left','#D20A18');
 text('(may fail to run or produce incorrect behavior)',118,790,324,16,false,'left','#D20A18');
});

// Flow arrows between panels.
groupWith('Migration enters the framework',()=>blockArrow(472,388,42,52,gradient('#FFE0B8','#FFF2D8'),'#E77632'));
groupWith('Framework produces verified output',()=>blockArrow(1264,388,42,52,gradient('#97DEA7','#D8F7D9'),'#188B44'));

// Central role coordination paths are behind their modules.
groupWith('Orchestrator connections',()=>{
 arrow(cubic([686,118],[642,115],[602,159],[603,211]),'#2D334E',3,12,true);
 arrow([[856,151],[856,210]],'#2D334E',3,12);
 arrow([...cubic([960,151],[977,181],[1000,178],[1086,178]),...cubic([1086,178],[1118,179],[1133,196],[1145,210]).slice(1)],'#2D334E',3,12);
 text('coordinate',618,168,99,18);text('schedule',873,168,98,18);text('coordinate',1156,177,111,18);
});
groupWith('Orchestrator',()=>{
 box(688,74,292,78,gradient('#F8FCFF','#E4F4FF'),'#3495F9',1.2,12);
 icon('robot',703,85,54,48,'#C7DDF5');text('Orchestrator',780,83,194,29,true,'center');text('Task planning & agent coordination',762,116,211,16.5,false,'center');
 box(983,74,197,91,gradient('#FFFFFF','#F6FCFA'),'#698599',1.1,10);
 ['Analyze task and context','Schedule agent actions','Monitor progress','Define stopping criteria'].forEach((s,i)=>{icon('tick',992,82+i*20,14,14,'#00A149');text(s,1013,80+i*20,160,16);});
});
groupWith('Translator',()=>{
 box(521,212,207,167,gradient('#FFF6DD','#FFFCEE'),'#B78013',1.2,14);
 icon('robot',549,221,35,33,'#FFE04B');text('Translator',600,221,120,25,true,'center');
 text('Cross-ecosystem code rewriting',528,258,193,17,false,'center');
 box(532,286,185,81,'#FFFFFF','#E8CC82',.7,8);
 text('model(x, y)',542,294,167,18);arrow([[617,328],[628,328]],C.ink,2.2,8);text('model(inputs, targets)',542,338,173,18);
});
groupWith('Verifier',()=>{
 box(791,212,183,169,gradient('#E9F7FF','#F1FCFF'),'#1186EC',1.2,14);
 icon('robot',813,221,34,33,'#65CDFF');text('Verifier',861,221,104,25,true,'center');
 text('Run & check behavior',801,256,163,20,false,'center');
 box(800,282,164,90,'#FFFFFF','none',0,8);
 [['play','run tests'],['search','check outputs'],['bars','compare metrics']].forEach(([a,b],i)=>{icon(a,821,290+i*28,21,21);text(b,860,288+i*28,100,18);});
});
groupWith('Repairer',()=>{
 box(1061,212,194,169,gradient('#F1EAFF','#FBF7FF'),'#793ED9',1.2,14);
 icon('robot',1085,221,36,33,'#CBA5FF');text('Repairer',1135,221,111,25,true,'center');
 text('Generate targeted patch',1076,257,167,19,false,'center');
 box(1071,285,174,86,'#FFFFFF','none',0,8);
 box(1076,292,164,23,'#FFE6EA','none',0,4);box(1076,319,164,24,'#DDF9EF','none',0,4);
 text('-  loss = model(data)',1082,294,158,17,false,'left','#F21239');text('+  loss = model(x, y)',1082,321,158,17,false,'left','#0D5454');text('…',1083,340,146,27);
});
groupWith('Agent exchange arrows',()=>{
 arrow([[729,313],[789,313]],C.line,3,12);text('translated',729,263,62,17,false,'center');text('code',734,284,53,17,false,'center');
 arrow([[974,271],[1059,271]],C.line,3,12);text('diagnosis',983,219,71,17,false,'center');text('& feedback',979,239,80,17,false,'center');
 arrow([[1060,322],[976,322]],C.line,3,12);text('repaired',989,333,66,17,false,'center');text('code',998,353,48,17,false,'center');
 arrow([[672,411],[672,382]],C.line,3,12);arrow([[1155,411],[1155,383]],C.line,3,12);
 blockArrow(877,382,21,30,gradient('#A1DCAB','#D4F8D7'),'#198444',true);
});

groupWith('Training semantics diagnosis chain',()=>{
 box(521,411,734,151,gradient('#EEF3F7','#FFFFFF'),'#71879D',1.2,12);
 text('Training Semantics Diagnosis Chain',542,423,692,27,true,'center');
 const xs=[531,671,821,976,1125], widths=[117,129,133,127,121],labels=['API\nusage','Tensor &\nShape','Forward\npass','Backward\npass','Update\nstep'];
 xs.forEach((x,i)=>{box(x,479,widths[i],67,gradient('#FFFFFF','#F5F7FD'),'#AFBED6',1.1,12);text(labels[i],x+6,490,widths[i]-12,21,false,'center');if(i<4)arrow([[x+widths[i]+1,512],[xs[i+1]-2,512]],'#48536A',1.9,9);});
});
groupWith('Workspace supplies evidence',()=>{
 blockArrow(640,563,22,30,gradient('#62BE76','#C7EEC7'),'#267C4F',true);
 blockArrow(866,560,28,33,gradient('#B9ECC3','#DDF9DC'),'#53AB72',true);
 blockArrow(1136,563,22,30,gradient('#66C37E','#CDEFD0'),'#277B4D',true);
});
groupWith('Dependency-aware workspace',()=>{
 box(511,593,753,229,gradient('#EEF7FE','#FFFFFF'),'#165CC7',1.2,16);
 icon('database',525,598,37,45,'#81C9FA');text('Dependency-Aware Workspace',580,599,658,26,true);
 groupWith('Repository graph',()=>{
  box(522,650,212,162,'#FFFFFF','#BDCFEC',1,11);text('Repository Graph',533,657,192,20,true);
  box(534,687,188,110,'#F5F8FB','#D4E0ED',.7,5);
  icon('folder',536,689,19,18,'#95B6CD');text('src/',565,686,130,18);
  ln(565,713,565,782,'#758391',1.3);
  ['model.py','train.py','data.py'].forEach((s,i)=>{const yy=713+i*30;ln(565,yy+8,579,yy+8,'#758391',1.3);icon('document',584,yy,22,22);text(s,617,yy-1,102,18);});
 });
 groupWith('Evidence store',()=>{
  box(744,650,179,162,'#FFFFFF','#BDCFEC',1,11);text('Evidence Store',756,657,160,20,true);
  [['document','Code snippets'],['trace','Execution traces'],['warning','Error messages']].forEach(([ic,t],i)=>{box(754,682+i*40,157,37,'#F5F8FB','#D4E0ED',.7,7);icon(ic,763,690+i*40,22,23);text(t,801,691+i*40,107,17.5);});
 });
 groupWith('Context for next iteration',()=>{
  box(933,650,214,162,'#FFFFFF','#BDCFEC',1,11);text('Context for Next Iteration',945,657,198,19.5,true);
  [['document','Related files'],['clock','Historical patches'],['database','Runtime states']].forEach(([ic,t],i)=>{box(946,682+i*40,189,37,'#F5F8FB','#D4E0ED',.7,7);icon(ic,957,690+i*40,22,23);text(t,997,691+i*40,133,17.5);});
 });
 groupWith('Preserve and update loop',()=>{
  arrow(cubic([1163,710],[1175,649],[1237,649],[1251,710]),C.blue,2.3,10);
  arrow(cubic([1252,757],[1238,812],[1180,815],[1163,758]),C.blue,2.3,10);
  ellipse(1166,682,12,12,'#74CAFB','none',0);
  text('Preserve\nand update\nacross\niterations',1167,698,82,18,true,'center');
 });
});

groupWith('Repaired repository',()=>{
 icon('database',1318,90,42,42,'#64C1FA');icon('check',1343,109,26,26);
 text('Repaired Repository',1383,92,250,27,true);
 box(1317,142,322,268,'#FFFFFF','#6C88A0',1.1,11);
 fileTree(1331,153,240,38,'migrated_project/',{highlight:false,checks:true});
});
groupWith('Migration success',()=>{
 box(1317,425,322,83,gradient('#E5FFF0','#F3FFF8'),'#4EBD88',1.1,12);icon('check',1333,438,52,52);
 text('Migration successful',1398,441,234,26,true);text('Functionally correct and behaviorally aligned',1398,474,234,14.5);
});
groupWith('Verified execution',()=>{
 box(1317,523,322,218,'#FFFFFF','#68839D',1.1,12);text('Verified execution',1333,532,290,26,true);
 box(1328,570,301,158,'#FFFFFF','#C3D6EB',1,10);
 ['passes (no runtime errors)','aligned behavior','stable update'].forEach((t,i)=>{icon('check',1341,587+i*46,36,36);text(t,1392,590+i*46,230,23);});
});

groupWith('Generalization and efficiency',()=>{
 box(18,850,1636,77,gradient('#FAFCFE','#EFF3F7'),'#859DB9',1.1,17);
 text('Generalization and Efficiency',43,869,342,30,true);
 [393,694,980,1325].forEach(x=>ln(x,865,x,914,'#839AB6',1.2));
 icon('globe',430,865,46,50);text('Cross-framework',497,875,181,24,true);
 icon('code-page',742,865,46,49);text('Cross-language',810,875,166,24,true);
 icon('database',1025,862,51,56,'#78BDF4');text('Repository-scale',1104,875,208,24,true);
 icon('lightning',1385,863,41,53);text('Token-efficient',1450,875,186,24,true);
});

slide.speakerNotes.textFrame.setText('Source: user-supplied image “ChatGPT Image Sep 24, 2026, 11_33_02 AM.png”.');
await (await PresentationFile.exportPptx(ppt)).save(path.join(build,'candidate.pptx'));
const fullSvg=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><defs>${defs.join('\n')}</defs><rect width="${W}" height="${H}" fill="white"/>${svg.join('\n')}</svg>`;
await fs.writeFile(path.join(out,'method-diagram.svg'),fullSvg);
for(const [type,{x,y,w,h,parts}] of iconFiles)await fs.writeFile(path.join(out,'icons',type+'.svg'),`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="${x-2} ${y-2} ${w+4} ${h+4}"><defs>${defs.join('\n')}</defs>${parts}</svg>`);
await fs.writeFile(path.join(build,'shape-groups.json'),JSON.stringify({width:W,height:H,font:FONT,records},null,2));
try {
 const png=await ppt.export({slide,format:'png',scale:1.5});
 await fs.writeFile(path.join(build,'artifact-preview.png'),new Uint8Array(await png.arrayBuffer()));
} catch(e) {console.warn('Artifact preview:',e.message);}
await fs.writeFile(path.join(build,'layout.json'),await (await slide.export({format:'layout'})).text());
console.log(JSON.stringify({draft:path.join(build,'candidate.pptx'),svg:path.join(out,'method-diagram.svg'),objects:records.length,icons:iconFiles.size}));
