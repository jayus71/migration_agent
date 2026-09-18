// Editable native PowerPoint diagram; archived I-09 evidence, no experiment execution.
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const runtime=process.env.CODEX_ARTIFACT_RUNTIME || 'C:/Users/jayus71/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const skill=process.env.CODEX_PRESENTATIONS_SKILL || 'C:/Users/jayus71/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.61513/skills/presentations';
process.env.RUNTIME_NODE_MODULES=path.join(runtime,'node/node_modules');
const {Presentation,PresentationFile}=await import(pathToFileURL(path.join(runtime,'node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const workspaceDir=process.env.CODEX_REPAIR_BUILD || 'C:/Users/jayus71/AppData/Local/Temp/codex-repair-cases';
const build=path.join(workspaceDir,'natural-translation-build');
await fs.mkdir(path.join(build,'final'),{recursive:true});
const evidence=JSON.parse(await fs.readFile(path.join(root,'data/paper_figures/intro_motivation_evidence.json'),'utf8'));
if(evidence.zero_target_update_parameters.length!==6 || Math.abs(evidence.loss_absolute_difference-4.76837158203125e-7)>1e-15)throw Error('Review changed evidence before redrawing.');
const p=Presentation.create({slideSize:{width:1056,height:377}});
const s=p.slides.add();s.background.fill='#FFFFFF';
const C={ink:'#20384B',blue:'#397294',pale:'#EFF6FA',green:'#288062',red:'#B34449',rose:'#FCF3F3',gray:'#758593',line:'#AAC1CF'};
let seq=0;
function shape(g,x,y,w,h,fill='none',stroke='none',width=0){return s.shapes.add({name:`diagram-${++seq}`,geometry:g,position:{left:x,top:y,width:w,height:h},fill,line:{fill:stroke,width}})}
function text(str,x,y,w,h,size=22,color=C.ink,bold=false,align='left'){let a=shape('textbox',x,y,w,h);a.text=str;a.text.insets={top:0,right:0,bottom:0,left:0};a.text.style={typeface:'Arial',fontSize:size,color,bold,alignment:align,verticalAlignment:'middle',autoFit:'none'};return a;}
function line(x1,y1,x2,y2,color=C.blue,width=2,arrow=false){const a=shape('rect',x1,y1,.1,.1),b=shape('rect',x2,y2,.1,.1);return s.shapes.connect(a,b,{kind:'straight',fromSide:'right',toSide:'left',line:{fill:color,width},tail:arrow?{type:'triangle',width:'med',length:'med'}:undefined});}
function polyline(points,color,width=2){const xs=points.map(p=>p[0]),ys=points.map(p=>p[1]),x=Math.min(...xs),y=Math.min(...ys),w=Math.max(...xs)-x,h=Math.max(...ys)-y;return s.shapes.add({geometry:'custom',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:color,width},customPaths:[{width:w,height:h,commands:[{moveTo:{x:points[0][0]-x,y:points[0][1]-y}},...points.slice(1).map(([xx,yy])=>({lineTo:{x:xx-x,y:yy-y}}))]}]});}
function panel(x,y,w,h,title,color,fill){shape('roundRect',x,y,w,h,fill,color,1.3);shape('rect',x+1,y+1,w-2,39,color);text(title,x+14,y+4,w-28,32,25,'#FFFFFF',true);}
function mark(x,y,good){const color=good?C.green:C.red;if(good){line(x,y+10,x+7,y+17,color,3);line(x+7,y+17,x+22,y,color,3);}else{line(x+3,y+1,x+20,y+18,color,3);line(x+3,y+18,x+20,y+1,color,3);}}
panel(8,8,374,361,'LLM translation',C.blue,'#F7FAFC');
panel(394,8,654,174,'SWE-agent / MatchFixAgent',C.blue,C.pale);
panel(394,195,654,174,'LaDiM (Ours)',C.red,C.rose);
// The two networks are isomorphic. Every forward edge remains present.
function network(x,y,broken){
 const nodes=[[0,29],[0,77],[49,5],[49,53],[49,101],[102,53]];
 for(const i of [0,1])for(const j of [2,3,4]){const a=nodes[i],b=nodes[j];line(x+a[0]+9,y+a[1],x+b[0]-10,y+b[1],C.gray,1.6,true);}
 for(const j of [2,3,4]){const a=nodes[j],b=nodes[5];line(x+a[0]+9,y+a[1],x+b[0]-10,y+b[1],C.gray,1.6,true);}
 // Independent backward return arc: intact head-side segment followed by one break.
 polyline([[x+104,y+65],[x+108,y+108],[x+94,y+137],[x+68,y+147],[x+40,y+144],[x+18,y+128]],C.blue,2);
 line(x+18,y+128,x+8,y+111,C.blue,2,true);
 if(broken){shape('ellipse',x+35,y+132,25,25,'#F7FAFC');mark(x+36,y+134,false);}
 for(let i=0;i<nodes.length;i++){let [a,b]=nodes[i];shape('ellipse',x+a-10,y+b-10,20,20,i===5?'#F4DADC':'#C6E0ED',i===5?C.red:C.blue,1.5);}
}
text('PyTorch',20,74,133,35,24,C.ink,true,'center');
text('MindSpore',223,74,151,35,24,C.ink,true,'center');
network(33,139,false);network(249,139,true);
line(156,201,219,201,C.blue,3,true);
text('Missing mapping',161,318,205,33,22,C.red,true,'center');
line(283,316,296,297,C.red,1.4,true);
// Conceptual baseline workflow: no measured I-09 success or failure is asserted.
shape('roundRect',410,70,225,91,'#FFFFFF',C.line,1);
text('Code, tests &\nsemantic analysis',420,82,205,64,22,C.ink,false,'center');
line(638,116,655,116,C.gray,2,true);
shape('roundRect',660,70,143,91,'#FFFFFF',C.line,1);
text('Repair\nfeedback',664,82,135,64,22,C.ink,false,'center');
line(806,116,823,116,C.gray,2,true);
shape('roundRect',828,70,204,91,'#FFFFFF',C.line,1);
text('Infer fault\nlocation',834,82,160,64,22,C.ink,false,'center');
text('?',997,89,28,48,32,C.blue,true,'center');
// Explicit staged diagnostics from the recorded first paired training step.
const checks=[['Execution',411,100,true],['Loss',521,84,true],['Gradients',615,106,false],['Parameter\nupdates',731,130,false]];
for(const [label,x,w,good] of checks){text(label,x,245,w,49,22,C.ink,false,'center');mark(x+w/2-11,301,good);}
for(const x of [510,604,720])line(x,309,x+11,309,C.gray,1.5,true);
line(863,285,883,285,C.gray,2,true);
shape('roundRect',889,248,143,79,'#FBE7E8',C.red,1.2);
text('Training\nerror detected',891,255,139,64,22,C.red,true,'center');
text('Loss difference: 4.77 × 10⁻⁷',411,336,348,28,22,C.ink);
text('6 parameter tensors unchanged',709,336,326,28,22,C.red,false,'right');
s.speakerNotes.textFrame.setText('Natural translation task I-09. Sources: data/paper_figures/intro_motivation_evidence.json; docs/natural-translation-cause-review-20260916.md; archived initial paired report and static adapter-code tracing. Initial loss absolute difference 4.76837158203125e-7; six upstream parameter tensors have zero target updates and head updates match. The missing high-level GroupNorm mapping invokes a NumPy value-copy path without a cross-framework backward bridge. The intact forward network and partially broken backward arc abstract that mechanism. Baseline panel is a conceptual code/test/semantic-analysis repair workflow for SWE-agent and MatchFixAgent, not an I-09 baseline outcome. LaDiM detects this error; recorded repair outcome STOP_NO_PROGRESS. No repaired outcome is depicted.');
const candidatePath=path.join(build,'candidate.pptx');
await(await PresentationFile.exportPptx(p)).save(candidatePath);
const stamp=Date.now(),finalPath=path.join(build,'final',`checked-${stamp}.pptx`);
const result=await finalizePresentation({workspaceDir,candidatePath,finalPath,pythonExecutable:path.join(runtime,'python/python.exe'),integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','10058400,3590925','--validate-heading-fit'],explicitTotalSlideCount:1,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,receiptPath:path.join(build,`validation-${stamp}.json`)});
await fs.copyFile(finalPath,path.join(root,'figures/repair_cases.pptx'));
console.log(JSON.stringify(result));
