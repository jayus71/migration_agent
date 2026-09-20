"""Bounded file generation before autonomous repository diagnosis and repair.

Only public source syntax, source-defined state metadata and prior generated
dependencies determine generation inputs. No evaluator outcomes enter this stage.
"""
from __future__ import annotations
import ast
from dataclasses import replace
import json
from pathlib import PurePosixPath
from autofix.autonomous.agent import BudgetExhausted


def generation_order(source):
    files={p.relative_to(source).as_posix():p for p in source.rglob('*.py')}
    modules={name[:-3].replace('/','.'):name for name in files}
    dependencies={};required=set()
    for name,path in files.items():
        tree=ast.parse(path.read_text());imports=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):imports.extend(x.name for x in node.names)
            elif isinstance(node,ast.ImportFrom):imports.append(node.module or '')
        dependencies[name]=sorted(set(modules[v] for v in imports if v in modules and modules[v]!=name))
        if any(v.split('.')[0]=='torch' for v in imports):required.add(name)
    order=[];visiting=set();visited=set()
    def visit(name):
        if name in visited:return
        if name in visiting:return  # Public cycles are kept in the input metadata.
        visiting.add(name)
        for dependency in dependencies[name]:visit(dependency)
        visiting.remove(name);visited.add(name)
        if name in required:order.append(name)
    for name in sorted(files):visit(name)
    return order,dependencies


def parse_files(response,allowed):
    choice=response['choices'][0]
    content=choice['message'].get('content') or ''
    if not content.strip():raise ValueError('Empty generation content; finish_reason='+str(choice.get('finish_reason')))
    content=content.strip()
    if content.startswith('```') and content.endswith('```'):content=content.split('\n',1)[1].rsplit('```',1)[0]
    files=json.loads(content)['files'];normalized={}
    if not isinstance(files,dict):raise ValueError('Expected files object')
    for name,value in files.items():
        if name.startswith('target/'):name=name[7:]
        path=PurePosixPath(name)
        if path.is_absolute() or any(x.startswith('.') for x in path.parts) or str(path)!=name or name not in allowed or not isinstance(value,str):
            raise ValueError('Out-of-scope generated file: '+name)
        if name in normalized:raise ValueError('Duplicate generated path')
        if name.endswith('.py'):compile(value,name,'exec')
        if name.endswith('.json'):json.loads(value)
        normalized[name]=value
    if set(normalized)!=set(allowed):raise ValueError('Missing generated files')
    return normalized


def bootstrap(agent,workspace,contract,save,path,max_output_tokens=80000,max_calls=20):
    source,target=workspace/'source',workspace/'target'
    order,dependencies=generation_order(source)
    plan=[{'files':[name],'source_files':{name:(source/name).read_text()},'dependencies':dependencies[name]} for name in order]
    plan.append({'files':['parameter_map.json','requirements.txt','README.md'],
        'source_files':{'README.md':(source/'README.md').read_text()},'dependencies':[n for n in order if n.startswith('src/')]})
    save(path/'plan.json',{'basis':'Public AST import dependencies and files with source-framework imports','units':plan,
        'max_calls':max_calls,'max_output_tokens':max_output_tokens})
    original_config=agent.config;start_calls=agent.calls;start_outputs=agent.output_tokens
    rows=[]
    try:
        for index,unit in enumerate(plan):
            remaining=max_output_tokens-(agent.output_tokens-start_outputs)
            if remaining<=0 or agent.calls-start_calls>=max_calls or agent._budget_status():break
            agent.config=replace(original_config,per_call_output_tokens=min(12288,remaining))
            payload={'task':contract,'files_to_generate':unit['files'],'source_files':unit['source_files'],
                'public_import_dependencies':unit['dependencies'],
                'current_dependency_files':{name:(target/name).read_text() for name in unit['dependencies']},
                'output_rule':'Return only JSON {"files":{"path":"complete file contents"}} for exactly files_to_generate. Preserve behavior and public interfaces, including source limitations. Use compact implementation and docstrings. Do not rewrite other files or produce analysis in content.'}
            if 'parameter_map.json' in unit['files']:
                payload['source_parameter_metadata']=contract['source_parameter_metadata']
            else:
                payload['task']={k:v for k,v in contract.items() if k!='source_parameter_metadata'}
            response=agent.complete([{'role':'system','content':'You translate one bounded unit of a software repository into the requested native framework. Generate the requested files now. Preserve the source behavior and compatibility with already translated dependencies. Output JSON only.'},
                {'role':'user','content':json.dumps(payload,ensure_ascii=False)}],stage='repository_translation',attempt=index+1)
            row={'unit':index+1,'files':unit['files'],'call':agent.calls,'status':'pending'}
            try:
                generated=parse_files(response,unit['files'])
                # Source-derived file scope and syntax are validated before writing.
                for name,value in generated.items():
                    destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(value)
                row.update(status='written')
            except (ValueError,KeyError,TypeError,SyntaxError) as exc:
                row.update(status='generation_failed',error=str(exc))
            rows.append(row);save(path/'result.json',{'status':'running','units':rows,'calls':agent.calls-start_calls,'output_tokens':agent.output_tokens-start_outputs})
    finally:agent.config=original_config
    result={'status':'completed','units':rows,'calls':agent.calls-start_calls,'output_tokens':agent.output_tokens-start_outputs,
        'planned_units':len(plan),'unattempted_units':len(plan)-len(rows),'written_units':sum(r['status']=='written' for r in rows)}
    save(path/'result.json',result);return result
