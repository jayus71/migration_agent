/** Generate the editable method overview and SVG from one layout specification.
 * Uses the Codex presentation runtime supplied in RUNTIME_NODE_MODULES.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.dirname(here);
const moduleRoot = process.env.RUNTIME_NODE_MODULES;
const runtime = moduleRoot ? pathToFileURL(path.join(moduleRoot, '@oai/artifact-tool/dist/artifact_tool.mjs')).href : '@oai/artifact-tool';
const { Presentation, PresentationFile } = await import(runtime);
const skill = process.env.SKILL_DIR;
if (!skill || !process.env.RUNTIME_PYTHON) throw new Error('Set SKILL_DIR and RUNTIME_PYTHON for presentation validation.');
const { finalizePresentation } = await import(pathToFileURL(path.join(skill, 'container_tools/artifact_tool_utils.mjs')).href);
const validationRoot = process.env.LADIM_PRESENTATION_WORKSPACE || root;
const build = path.join(validationRoot, 'output/paper-revision-execution-20260921/overview-build');
const finalDir = path.join(validationRoot, 'output/paper-revision-execution-20260921/overview-validated');
await fs.mkdir(build, { recursive: true });
await fs.mkdir(finalDir, { recursive: true });
const width = 1056, height = 566, font = 'Times New Roman';
const presentation = Presentation.create({ slideSize: { width, height } });
const slide = presentation.slides.add();
slide.background.fill = '#FFFFFF';
const svg = [`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`,
 '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L8,4 L0,8 Z" fill="#46535F"/></marker></defs>'];
const esc = value => value.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
function text(value, x, y, w, size=22, bold=false) {
 const lines=value.split('\n');
 // One native textbox per line makes edits and geometry correspond to SVG text.
 for (const [i,line] of lines.entries()) {
  const top=y+i*28;
  const shape=slide.shapes.add({geometry:'textbox',name:line,
   position:{left:x,top,width:w,height:30},fill:'none',line:{fill:'none',width:0}});
  shape.text=line;
  shape.text.style={typeface:font,fontSize:size,bold,color:'#17212B',autoFit:'none',verticalAlignment:'top',
   insets:{left:0,right:0,top:0,bottom:0}};
  svg.push(`<text xml:space="preserve" x="${x}" y="${top+size*.9}" font-family="Times New Roman, serif" font-size="${size}" font-weight="${bold?'bold':'normal'}" fill="#17212B">${esc(line)}</text>`);
 }
}
function box(title, lines, x,y,w,h,fill) {
 slide.shapes.add({geometry:'rect',name:title,position:{left:x,top:y,width:w,height:h},fill,
  line:{fill:'#A8B2BB',width:1.4}});
 svg.push(`<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${fill}" stroke="#A8B2BB" stroke-width="1.4"/>`);
 text(title,x+13,y+10,w-26,26,true);
 text(lines,x+13,y+52,w-26,22);
}
function arrow(points) {
 for(let i=0;i<points.length-1;i++) {
  const source=slide.shapes.add({geometry:'rect',name:'Route start',position:{left:points[i][0]-.01,top:points[i][1]-.01,width:.02,height:.02},fill:'none',line:{fill:'none',width:0}});
  const target=slide.shapes.add({geometry:'rect',name:'Route end',position:{left:points[i+1][0]-.01,top:points[i+1][1]-.01,width:.02,height:.02},fill:'none',line:{fill:'none',width:0}});
  slide.shapes.connect(source,target,{kind:'straight',line:{fill:'#46535F',width:1.8},
   tail:i===points.length-2?{type:'triangle',width:'sm',length:'sm'}:{type:'none'}});
 }
 svg.push(`<polyline points="${points.map(p=>p.join(',')).join(' ')}" fill="none" stroke="#46535F" stroke-width="1.8" marker-end="url(#arrow)"/>`);
}
box('Translator','Source and target framework\nGenerate initial candidate',16,54,285,140,'#F1F3F5');
box('Verifier','Independent investigation\nInspect code and run tests\nRecord supported hypotheses',375,54,310,140,'#E8F2F9');
box('Repair Agent','Examine the evidence\nTest and edit the candidate',760,54,280,140,'#EDF5EC');
box('Target execution','MindSpore or JAX\nRun and measure training',16,284,285,140,'#F1F3F5');
box('Orchestrator','Run acceptance checks\nReturn new measurements\nConfirm completed migration',375,284,310,140,'#FFF2DF');
box('Workspace','Candidate and tests\nEdits and repair history',760,284,280,140,'#F1F3F5');
box('Repository coordination','Track dependencies     Retrieve archived evidence     Invalidate affected checks',16,467,1024,88,'#F1F3F5');
arrow([[301,124],[375,124]]);
arrow([[685,124],[760,124]]);
text('Evidence handoff',660,18,190,22);
arrow([[900,194],[900,284]]);
text('Edits',914,224,95,22);
arrow([[760,354],[685,354]]);
arrow([[301,354],[375,354]]);
arrow([[685,310],[721,310],[721,167],[760,167]]);
text('Measurements',514,230,175,22);
arrow([[900,467],[900,424]]);
slide.speakerNotes.textFrame.setText('LaDiM method overview. Source: conference_101719.tex, Section 3, and scripts/repository_agent_mode.py. All text, boxes and connectors are editable. MindSpore and JAX are the target frameworks. Repository checkpoints track dependencies and become stale after relevant changes.');
svg.push('</svg>');
await fs.writeFile(path.join(here,'slim_v4_overview.svg'),svg.join('\n'));
const draft=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(presentation)).save(draft);
const preview=await presentation.export({slide,format:'png',scale:1.5});
await fs.writeFile(path.join(build,'slide-1.png'),new Uint8Array(await preview.arrayBuffer()));
const layout=await slide.export({format:'layout'});
await fs.writeFile(path.join(build,'slide-1.layout.json'),await layout.text());
const stamp=new Date().toISOString().replaceAll(/[^0-9]/g,'');
const finalPath=path.join(finalDir,`overview-${stamp}.pptx`);
await finalizePresentation({workspaceDir:validationRoot,candidatePath:draft,finalPath,
 pythonExecutable:process.env.RUNTIME_PYTHON,
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu',`${width*9525},${height*9525}`,'--validate-bullet-geometry','--validate-heading-fit'],
 explicitTotalSlideCount:1,fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,
 receiptPath:path.join(build,`validation-${stamp}.json`)});
await fs.copyFile(finalPath,path.join(here,'hierarchical_feedback_architecture.pptx'));
await fs.copyFile(path.join(build,'slide-1.png'),path.join(root,'output/paper-revision-execution-20260921/overview-build/slide-1.png'));
console.log('Wrote editable PowerPoint and SVG; validation receipt:',build);
