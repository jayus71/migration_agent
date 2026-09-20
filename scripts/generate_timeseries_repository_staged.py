"""One dependency-aware initial translation; preserve the earlier exhausted call."""
from __future__ import annotations
import json
from pathlib import Path, PurePosixPath
import shutil
import time

from repository_timeseries_pilot import RUN,ROOT,read,save,digest,hashes,coverage
from autofix.autonomous.agent import OpenAICompatibleClient


def generate(name, payload, max_tokens, allowed):
    folder=RUN/'translation_stages'/name
    request={'model':'deepseek-v4-flash','thinking':{'type':'enabled'},'reasoning_effort':'high',
             'max_tokens':max_tokens,'stream':False,
             'messages':[{'role':'system','content':'Translate the specified part of the supplied repository while preserving its behavior and the common public contract. Return only one JSON object {"files": {"relative/path": "complete UTF-8 file contents", ...}}. Keep interfaces consistent across files. Do not output Markdown fences.'},
                         {'role':'user','content':json.dumps(payload,ensure_ascii=False)}]}
    if folder.exists():
        if read(folder/'request.json')!=request:raise ValueError('A different request already exists for this stage')
        state=read(folder/'status.json')
        if state['status']=='generated':
            return {name:(folder/'files'/name).read_text() for name in state['files']}
        if not (folder/'response.json').is_file():raise RuntimeError('Existing stage has no response; do not issue another call')
        if not (folder/'previous_adapter_error.json').exists():save(folder/'previous_adapter_error.json',state)
    else:
        folder.mkdir(parents=True,exist_ok=False)
        save(folder/'request.json',request)
    save(folder/'status.json',{'status':'running','max_tokens':max_tokens})
    started=time.monotonic()
    response=None
    try:
        if (folder/'response.json').exists():
            response=read(folder/'response.json')
        else:
            response=OpenAICompatibleClient()(request,1800)
            save(folder/'response.json',response)
        choice=response['choices'][0]
        content=choice['message'].get('content') or ''
        if content.strip().startswith('```'):content=content.strip().split('\n',1)[1].rsplit('```',1)[0]
        if not content.strip():raise ValueError('No generated files; finish_reason='+str(choice.get('finish_reason')))
        files=json.loads(content)['files']
        if not isinstance(files,dict) or not files:raise ValueError('Expected a nonempty files object')
        out=folder/'files';out.mkdir(exist_ok=True)
        normalized={}
        for name,text in files.items():
            p=PurePosixPath(name)
            if p.is_absolute() or any(x.startswith('.') for x in p.parts):
                raise ValueError('Out-of-scope generated path: '+name)
            # Public contract paths include target/. A returned workspace-relative
            # path and a repository-relative path denote the same destination.
            name=PurePosixPath(*p.parts[1:]).as_posix() if p.parts[0]=='target' else name
            if not allowed(name) or name in normalized:raise ValueError('Out-of-scope or duplicate path: '+name)
            if not isinstance(text,str):raise ValueError('File content must be a string: '+name)
            normalized[name]=text
            dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
        save(folder/'status.json',{'status':'generated','seconds':time.monotonic()-started,
             'usage':response.get('usage'),'finish_reason':choice.get('finish_reason'),'files':hashes(out)})
        return normalized
    except Exception as exc:
        save(folder/'status.json',{'status':'error','seconds':time.monotonic()-started,'error':str(exc),
             'usage':response.get('usage') if response else None})
        raise


def main():
    assert not (RUN/'translation/target').exists(),'Do not replace an existing initial target'
    assert not (RUN/'conditions').exists(),'Initial generation must finish before any method condition starts'
    contract=read(RUN/'task.json')
    manifest=read(RUN/'manifest.json')
    assert manifest['source_hashes']==hashes(RUN/'source')
    assert manifest['contract_sha256']==digest(RUN/'task.json')
    old=read(RUN/'translation/response.json')
    assert old['choices'][0]['finish_reason']=='length' and not old['choices'][0]['message'].get('content')
    save(RUN/'staged_translation_protocol.json',{
        'reason':'The first monolithic call exhausted all 32768 output tokens in reasoning and produced no target. Preserve its cost and produce one shared target using dependency-aware stages.',
        'authorization_context':'User asked whether whole-repository translation needs a higher reasoning allowance or file-wise conversion; choose retained reasoning and dependency-aware stages.',
        'stages':[{'name':'core','max_tokens_including_reasoning':65536,'scope':['project.py','parameter_map.json','requirements.txt']},
                  {'name':'examples','max_tokens_including_reasoning':32768,'scope':'All original teaching Python files, notebook and README, reusing frozen translated core'}],
        'model':'deepseek-v4-flash','thinking':'enabled','reasoning_effort':'high',
        'physical_generation_calls':3,'initial_exhausted_call_included':True,
        'selection':'Exactly one generated core and one examples bundle. No candidate selection, hand edits, or evaluator feedback between generation stages.',
        'comparison':'All methods receive identical final files and are charged all three generation calls.',
        'acceptance_contract_sha256':digest(RUN/'task.json'),'generator_sha256':digest(Path(__file__))})
    source=RUN/'source'
    core_names={'project.py','parameter_map.json','requirements.txt'}
    core=generate('core',{'public_contract':contract,
        'scope':'Generate project.py, parameter_map.json and requirements.txt only. Define reusable import-safe public APIs so the original teaching snippets and notebook can reuse this implementation in the next stage. Preserve all original complete main() behavior.',
        'source_files':{name:(source/name).read_text() for name in ('project.py','requirements.txt')}},65536,lambda name:name in core_names)
    if set(core)!=core_names:raise ValueError('The core stage did not generate its declared files')
    fragments={p.relative_to(source).as_posix():p.read_text() for p in sorted((source/'step_by_step_code_blocks').glob('*.py'))}
    notebook=read(source/'demo-predicting-stock-prices.ipynb')
    fragments['demo-predicting-stock-prices.ipynb']=json.dumps({'cells':[{'cell_type':c['cell_type'],'source':''.join(c['source'])} for c in notebook['cells']]})
    fragments['README.md']=(source/'README.md').read_text()
    examples=generate('examples',{'public_contract':contract,
        'scope':'Generate every supplied teaching file, the complete valid notebook JSON as a string, and README.md. Reuse the given translated core via imports where appropriate; preserve runnable instructional progression and all existing functionality. Do not modify the core files. Clear notebook execution outputs. Return the original file paths.',
        'translated_core':core,'original_examples':fragments},32768,lambda name:name in fragments)
    target=RUN/'translation/target'
    shutil.copytree(source,target)
    for name,text in {**core,**examples}.items():
        path=target/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    usage={key:sum(r.get('usage',{}).get(key,0) for r in (old,read(RUN/'translation_stages/core/response.json'),read(RUN/'translation_stages/examples/response.json')))
           for key in ('prompt_tokens','completion_tokens','total_tokens')}
    result={'status':'generated','physical_generation_calls':3,'usage_including_exhausted_call':usage,
            'files':hashes(target),'coverage':coverage(target),'source_unchanged':manifest['source_hashes']==hashes(source)}
    save(RUN/'staged_translation_result.json',result)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
