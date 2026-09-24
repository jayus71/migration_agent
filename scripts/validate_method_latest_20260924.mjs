import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const build=path.join(root,'tmp/method-latest-20260924');
const out=path.join(root,'figures/editable-method-latest-20260924');
const {finalizePresentation}=await import(pathToFileURL(path.join(process.env.SKILL_DIR,'container_tools/artifact_tool_utils.mjs')).href);
const {PresentationFile,FileBlob}=await import(pathToFileURL(path.join(process.env.RUNTIME_NODE_MODULES,'@oai/artifact-tool/dist/artifact_tool.mjs')).href);
// The Windows finalizer publishes with an atomic hard link. WSL UNC shares
// do not support that operation; validate locally, then copy unchanged.
const validationRoot=process.env.METHOD_DIAGRAM_VALIDATION_DIR??root;
const staging=path.join(validationRoot,'.method-diagram-finalizer');
await fs.mkdir(staging,{recursive:true});
const candidatePath=path.join(staging,'candidate.pptx');
await fs.copyFile(path.join(build,'grouped-candidate.pptx'),candidatePath);
const finalPath=path.join(out,'method-diagram-editable.pptx');
const validatedPath=path.join(validationRoot,'method-diagram-output','method-diagram-editable.pptx');
await fs.mkdir(path.dirname(validatedPath),{recursive:true});
const result=await finalizePresentation({
 workspaceDir:validationRoot,candidatePath,finalPath:validatedPath,
 explicitTotalSlideCount:1,
 pythonExecutable:process.env.RUNTIME_PYTHON,
 integrityValidatorPath:path.join(process.env.SKILL_DIR,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(process.env.SKILL_DIR,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu',`${1672*9525},${941*9525}`,'--validate-bullet-geometry','--validate-heading-fit'],
 requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],
 fontPolicy:{basis:'user_request',families:['Times New Roman']},
 verifyArtifactToolImport:true,receiptPath:path.join(staging,'final.validation.json')
});
await fs.copyFile(validatedPath,finalPath);
await fs.copyFile(path.join(staging,'final.validation.json'),path.join(build,'final.validation.json'));
console.log(JSON.stringify(result));
const presentation=await PresentationFile.importPptx(await FileBlob.load(finalPath));
const png=await presentation.export({slide:presentation.slides.items[0],format:'png',scale:1.5});
await fs.writeFile(path.join(out,'method-diagram-preview.png'),new Uint8Array(await png.arrayBuffer()));
